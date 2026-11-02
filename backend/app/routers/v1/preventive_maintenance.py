from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.helpers import utcnow
from app.common.pagination import apply_partial_update
from app.common.search import apply_search
from app.database import get_db
from app.models import Asset, AssetTask, Checklist, ChecklistTestPoint, PMQueueEntry, TaskLibrary, User, UserRole
from app.schemas import (
    AssetTaskCreate,
    AssetTaskResponse,
    AssetTaskUpdate,
    ChecklistCreate,
    ChecklistTestPointCreate,
    ChecklistTestPointUpdate,
    PMQueueGenerate,
    TaskLibraryCreate,
    TaskLibraryUpdate,
)
from app.services.pm_queue import process_pm_queue

router = APIRouter(prefix="/v1", tags=["Preventive Maintenance"])


@router.post("/task-library")
def create_task_library(body: TaskLibraryCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    t = TaskLibrary(**body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/task-library")
def list_task_library(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(TaskLibrary).filter(TaskLibrary.deleted_at.is_(None))
    if site_id:
        q = q.filter(TaskLibrary.site_id == site_id)
    return q.all()


@router.put("/task-library/{task_id}")
def update_task_library(task_id: UUID, body: TaskLibraryUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    t = db.query(TaskLibrary).filter(TaskLibrary.id == task_id, TaskLibrary.deleted_at.is_(None)).first()
    if not t:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(t, data, body.fields_to_update)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/task-library/{task_id}")
def delete_task_library(task_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    t = db.query(TaskLibrary).filter(TaskLibrary.id == task_id, TaskLibrary.deleted_at.is_(None)).first()
    if not t:
        raise HTTPException(status_code=404)
    t.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@router.post("/asset-tasks", response_model=AssetTaskResponse)
def create_asset_task(body: AssetTaskCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    task = AssetTask(**body.model_dump())
    db.add(task)
    db.flush()
    if task.due_date and task.due_date <= utcnow():
        db.add(PMQueueEntry(asset_task_id=task.id, due_date=task.due_date, status="PENDING"))
    db.commit()
    db.refresh(task)
    return task


@router.get("/assets/{asset_id}/tasks", response_model=list[AssetTaskResponse])
def list_asset_tasks(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(AssetTask).filter(AssetTask.asset_id == asset_id, AssetTask.deleted_at.is_(None)).all()


@router.get("/asset-tasks")
def list_all_asset_tasks(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(AssetTask).filter(AssetTask.deleted_at.is_(None))
    if site_id:
        q = q.join(Asset).filter(Asset.site_id == site_id)
    if status:
        q = q.filter(AssetTask.status == status)
    q = apply_search(q, search, AssetTask.task_code, AssetTask.description, AssetTask.task_type)
    return q.order_by(AssetTask.task_code).all()


@router.get("/asset-tasks/{task_id}", response_model=AssetTaskResponse)
def get_asset_task(task_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.query(AssetTask).filter(AssetTask.id == task_id, AssetTask.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404)
    return task


@router.put("/asset-tasks/{task_id}", response_model=AssetTaskResponse)
def update_asset_task(task_id: UUID, body: AssetTaskUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    task = db.query(AssetTask).filter(AssetTask.id == task_id, AssetTask.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(task, data, body.fields_to_update)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/asset-tasks/{task_id}")
def delete_asset_task(task_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    task = db.query(AssetTask).filter(AssetTask.id == task_id, AssetTask.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404)
    task.deleted_at = utcnow()
    task.is_active = False
    db.commit()
    return {"deleted": True}


@router.get("/pm-queue")
def list_pm_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(PMQueueEntry).filter(PMQueueEntry.status == "PENDING").all()


@router.post("/pm-queue/generate")
def generate_pm_work_orders(body: PMQueueGenerate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.PLANNER, UserRole.ADMIN))):
    created = process_pm_queue(db, body.lead_time_days)
    return {"generated": len(created), "work_orders": [{"id": str(w.id), "number": w.number} for w in created]}


@router.post("/work-orders/{wo_id}/checklists")
def create_checklist(wo_id: UUID, body: ChecklistCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cl = Checklist(work_order_id=wo_id, **body.model_dump())
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return {"id": str(cl.id), "name": cl.name}


@router.get("/work-orders/{wo_id}/checklists")
def list_checklists(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Checklist).filter(Checklist.work_order_id == wo_id).all()


@router.post("/checklists/{checklist_id}/test-points")
def add_test_point(checklist_id: UUID, body: ChecklistTestPointCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tp = ChecklistTestPoint(checklist_id=checklist_id, **body.model_dump())
    db.add(tp)
    db.commit()
    db.refresh(tp)
    return tp


@router.get("/checklists/{checklist_id}/test-points")
def list_test_points(checklist_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ChecklistTestPoint).filter(ChecklistTestPoint.checklist_id == checklist_id).order_by(ChecklistTestPoint.line_number).all()


@router.put("/checklist-test-points/{tp_id}")
def update_test_point(tp_id: UUID, body: ChecklistTestPointUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tp = db.query(ChecklistTestPoint).filter(ChecklistTestPoint.id == tp_id).first()
    if not tp:
        raise HTTPException(status_code=404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(tp, k, v)
    db.commit()
    return tp
