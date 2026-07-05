from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.custom_fields import get_custom_fields, set_custom_fields
from app.common.helpers import next_number, utcnow
from app.common.pagination import apply_partial_update, paginate
from app.common.search import apply_search
from app.database import get_db
from app.models import (
    AssetHistory,
    CustomFieldEntity,
    ServiceRequest,
    ServiceRequestStatus,
    User,
    UserRole,
    WebhookEvent,
    WorkOrder,
    WorkOrderAssignment,
    WorkOrderComment,
    WorkOrderPartUsage,
    WorkOrderStatus,
    WorkOrderTask,
    WorkOrderType,
)
from app.schemas import (
    ServiceRequestCreate,
    ServiceRequestResponse,
    ServiceRequestUpdate,
    WorkOrderAssignmentCreate,
    WorkOrderCommentCreate,
    WorkOrderCommentResponse,
    WorkOrderCreate,
    WorkOrderPartUsageCreate,
    WorkOrderResponse,
    WorkOrderSearch,
    WorkOrderTaskCreate,
    WorkOrderTaskResponse,
    WorkOrderTaskUpdate,
    WorkOrderUpdate,
)
from app.services.webhooks import dispatch_webhook_sync

router = APIRouter(tags=["Work Management"])


def _wo_response(db: Session, wo: WorkOrder, include_custom: bool) -> WorkOrderResponse:
    data = WorkOrderResponse.model_validate(wo)
    if include_custom:
        data.custom_fields = get_custom_fields(db, CustomFieldEntity.WORK_ORDER, wo.id)
    return data


def _get_work_order_or_404(db: Session, wo_id: UUID) -> WorkOrder:
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id, WorkOrder.deleted_at.is_(None)).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return wo


def _next_task_line_number(db: Session, wo_id: UUID) -> int:
    current = (
        db.query(WorkOrderTask)
        .filter(WorkOrderTask.work_order_id == wo_id, WorkOrderTask.deleted_at.is_(None))
        .order_by(WorkOrderTask.line_number.desc())
        .first()
    )
    return (current.line_number + 1) if current else 1


# --- Service Requests ---
sr_router = APIRouter(prefix="/v1/service-requests", tags=["Service Requests"])


@sr_router.get("")
def list_service_requests(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    status: ServiceRequestStatus | None = None,
    priority: str | None = Query(None),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ServiceRequest).filter(ServiceRequest.deleted_at.is_(None))
    if site_id:
        q = q.filter(ServiceRequest.site_id == site_id)
    if status:
        q = q.filter(ServiceRequest.status == status)
    if priority:
        q = q.filter(ServiceRequest.priority == priority)
    q = apply_search(q, search, ServiceRequest.number, ServiceRequest.problem, ServiceRequest.requested_by, ServiceRequest.requester_email)
    total = q.count()
    items = q.order_by(ServiceRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginate([ServiceRequestResponse.model_validate(i) for i in items], total, page, page_size)


@sr_router.post("", response_model=ServiceRequestResponse)
def create_service_request(body: ServiceRequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = ServiceRequest(number=next_number(db, ServiceRequest, body.site_id, "SR"), **body.model_dump())
    db.add(sr)
    db.commit()
    db.refresh(sr)
    dispatch_webhook_sync(db, sr.site_id, WebhookEvent.SERVICE_REQUEST_CREATED, {"id": str(sr.id), "number": sr.number})
    return sr


@sr_router.get("/{sr_id}", response_model=ServiceRequestResponse)
def get_service_request(sr_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id).first()
    if not sr:
        raise HTTPException(status_code=404)
    return sr


@sr_router.put("/{sr_id}", response_model=ServiceRequestResponse)
def update_service_request(sr_id: UUID, body: ServiceRequestUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id).first()
    if not sr:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(sr, data, body.fields_to_update)
    db.commit()
    db.refresh(sr)
    dispatch_webhook_sync(db, sr.site_id, WebhookEvent.SERVICE_REQUEST_UPDATED, {"id": str(sr.id)})
    return sr


@sr_router.post("/{sr_id}/convert-to-work-order", response_model=WorkOrderResponse)
def convert_to_work_order(sr_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.PLANNER, UserRole.ADMIN))):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id).first()
    if not sr:
        raise HTTPException(status_code=404)
    wo = WorkOrder(
        site_id=sr.site_id,
        number=next_number(db, WorkOrder, sr.site_id, "CM"),
        type=WorkOrderType.CORRECTIVE,
        status=WorkOrderStatus.OPEN,
        title=f"SR {sr.number}: {sr.problem[:80]}",
        description=sr.instructions,
        problem=sr.problem,
        priority=sr.priority,
        asset_id=sr.asset_id,
        location_id=sr.location_id,
        service_request_id=sr.id,
        date_created=utcnow(),
    )
    db.add(wo)
    db.flush()
    sr.work_order_id = wo.id
    sr.status = ServiceRequestStatus.FOR_REVIEW
    db.commit()
    db.refresh(wo)
    dispatch_webhook_sync(db, wo.site_id, WebhookEvent.WORK_ORDER_CREATED, {"id": str(wo.id), "number": wo.number})
    return _wo_response(db, wo, False)


@sr_router.put("/{sr_id}/decline")
def decline_service_request(sr_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.PLANNER, UserRole.ADMIN))):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id).first()
    if not sr:
        raise HTTPException(status_code=404)
    sr.status = ServiceRequestStatus.DECLINED
    db.commit()
    return {"declined": True}


@sr_router.delete("/{sr_id}")
def delete_service_request(sr_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id, ServiceRequest.deleted_at.is_(None)).first()
    if not sr:
        raise HTTPException(status_code=404)
    sr.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


# --- Work Orders ---
wo_router = APIRouter(prefix="/v1/work-orders", tags=["Work Orders"])


@wo_router.get("")
def list_work_orders(
    site_id: UUID | None = None,
    type: WorkOrderType | None = None,
    status: WorkOrderStatus | None = None,
    priority: str | None = Query(None),
    search: str | None = Query(None),
    page: int = 1,
    page_size: int = 20,
    custom_fields: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(WorkOrder).filter(WorkOrder.deleted_at.is_(None))
    if site_id:
        q = q.filter(WorkOrder.site_id == site_id)
    if type:
        q = q.filter(WorkOrder.type == type)
    if status:
        q = q.filter(WorkOrder.status == status)
    if priority:
        q = q.filter(WorkOrder.priority == priority)
    q = apply_search(q, search, WorkOrder.number, WorkOrder.title, WorkOrder.description, WorkOrder.problem)
    total = q.count()
    items = q.order_by(WorkOrder.date_created.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginate([_wo_response(db, w, custom_fields) for w in items], total, page, page_size)


@wo_router.post("/searches")
def search_work_orders(body: WorkOrderSearch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(WorkOrder).filter(WorkOrder.deleted_at.is_(None))
    if body.status:
        q = q.filter(WorkOrder.status == body.status)
    if body.type:
        q = q.filter(WorkOrder.type == body.type)
    if body.asset_id:
        q = q.filter(WorkOrder.asset_id == body.asset_id)
    if body.priority:
        q = q.filter(WorkOrder.priority == body.priority)
    total = q.count()
    items = q.offset((body.page - 1) * body.page_size).limit(body.page_size).all()
    return paginate([_wo_response(db, w, False) for w in items], total, body.page, body.page_size)


@wo_router.post("", response_model=WorkOrderResponse)
def create_work_order(body: WorkOrderCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.PLANNER, UserRole.ADMIN, UserRole.TECHNICIAN))):
    prefix = "PM" if body.type == WorkOrderType.PREVENTIVE else "CM" if body.type == WorkOrderType.CORRECTIVE else "WO"
    wo = WorkOrder(number=next_number(db, WorkOrder, body.site_id, prefix), date_created=utcnow(), created_by=user.email, **body.model_dump(exclude={"custom_fields"}))
    db.add(wo)
    db.flush()
    if body.custom_fields:
        set_custom_fields(db, CustomFieldEntity.WORK_ORDER, wo.id, body.custom_fields)
    db.commit()
    db.refresh(wo)
    dispatch_webhook_sync(db, wo.site_id, WebhookEvent.WORK_ORDER_CREATED, {"id": str(wo.id), "number": wo.number})
    return _wo_response(db, wo, True)


@wo_router.get("/{wo_id}", response_model=WorkOrderResponse)
def get_work_order(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404)
    return _wo_response(db, wo, True)


@wo_router.put("/{wo_id}", response_model=WorkOrderResponse)
def update_work_order(wo_id: UUID, body: WorkOrderUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update", "custom_fields"}, exclude_none=True)
    apply_partial_update(wo, data, body.fields_to_update)
    if body.custom_fields:
        set_custom_fields(db, CustomFieldEntity.WORK_ORDER, wo.id, body.custom_fields)
    db.commit()
    db.refresh(wo)
    dispatch_webhook_sync(db, wo.site_id, WebhookEvent.WORK_ORDER_PROGRESS, {"id": str(wo.id), "status": wo.status.value})
    return _wo_response(db, wo, True)


@wo_router.put("/{wo_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404)
    wo.status = WorkOrderStatus.COMPLETED
    wo.date_completed = utcnow()
    if wo.asset_id:
        db.add(AssetHistory(asset_id=wo.asset_id, event_type="WORK_ORDER_COMPLETED", description=wo.title, work_order_id=wo.id))
    db.commit()
    db.refresh(wo)
    return _wo_response(db, wo, False)


@wo_router.post("/{wo_id}/personnel")
def assign_personnel(wo_id: UUID, body: WorkOrderAssignmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = WorkOrderAssignment(work_order_id=wo_id, **body.model_dump())
    db.add(a)
    db.commit()
    return {"id": str(a.id)}


@wo_router.get("/{wo_id}/personnel")
def list_personnel(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(WorkOrderAssignment).filter(WorkOrderAssignment.work_order_id == wo_id).all()


@wo_router.post("/{wo_id}/parts")
def add_part_usage(wo_id: UUID, body: WorkOrderPartUsageCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    usage = WorkOrderPartUsage(work_order_id=wo_id, **body.model_dump())
    db.add(usage)
    db.commit()
    return {"id": str(usage.id)}


@wo_router.get("/{wo_id}/parts")
def list_part_usage(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(WorkOrderPartUsage).filter(WorkOrderPartUsage.work_order_id == wo_id).all()


@wo_router.post("/{wo_id}/comments", response_model=WorkOrderCommentResponse)
def add_comment(wo_id: UUID, body: WorkOrderCommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = WorkOrderComment(work_order_id=wo_id, author=user.email, body=body.body)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@wo_router.get("/{wo_id}/comments", response_model=list[WorkOrderCommentResponse])
def list_comments(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(WorkOrderComment).filter(WorkOrderComment.work_order_id == wo_id).order_by(WorkOrderComment.created_at).all()


@wo_router.get("/{wo_id}/tasks", response_model=list[WorkOrderTaskResponse])
def list_work_order_tasks(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_work_order_or_404(db, wo_id)
    return (
        db.query(WorkOrderTask)
        .filter(WorkOrderTask.work_order_id == wo_id, WorkOrderTask.deleted_at.is_(None))
        .order_by(WorkOrderTask.line_number)
        .all()
    )


@wo_router.post("/{wo_id}/tasks", response_model=WorkOrderTaskResponse)
def create_work_order_task(
    wo_id: UUID,
    body: WorkOrderTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_work_order_or_404(db, wo_id)
    task = WorkOrderTask(
        work_order_id=wo_id,
        line_number=body.line_number or _next_task_line_number(db, wo_id),
        description=body.description,
        estimated_hours=body.estimated_hours,
        notes=body.notes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@wo_router.put("/{wo_id}/tasks/{task_id}", response_model=WorkOrderTaskResponse)
def update_work_order_task(
    wo_id: UUID,
    task_id: UUID,
    body: WorkOrderTaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_work_order_or_404(db, wo_id)
    task = (
        db.query(WorkOrderTask)
        .filter(WorkOrderTask.id == task_id, WorkOrderTask.work_order_id == wo_id, WorkOrderTask.deleted_at.is_(None))
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    data = body.model_dump(exclude_none=True)
    if data.get("status") == "COMPLETED" and task.status != "COMPLETED":
        task.completed_at = utcnow()
    elif data.get("status") == "PENDING":
        task.completed_at = None
    apply_partial_update(task, data, None)
    db.commit()
    db.refresh(task)
    return task


@wo_router.delete("/{wo_id}/tasks/{task_id}")
def delete_work_order_task(
    wo_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_work_order_or_404(db, wo_id)
    task = (
        db.query(WorkOrderTask)
        .filter(WorkOrderTask.id == task_id, WorkOrderTask.work_order_id == wo_id, WorkOrderTask.deleted_at.is_(None))
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@wo_router.delete("/{wo_id}")
def delete_work_order(wo_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id, WorkOrder.deleted_at.is_(None)).first()
    if not wo:
        raise HTTPException(status_code=404)
    wo.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}
