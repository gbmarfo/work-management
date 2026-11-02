from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    AssetTask,
    PMQueueEntry,
    ScheduleType,
    WorkOrder,
    WorkOrderStatus,
    WorkOrderType,
)


def _next_number(db: Session, site_id, prefix: str) -> str:
    count = db.query(WorkOrder).filter(WorkOrder.site_id == site_id).count()
    return f"{prefix}-{count + 1:06d}"


def process_pm_queue(db: Session, lead_time_days: int = 0) -> list[WorkOrder]:
    now = datetime.now(timezone.utc)
    entries = db.query(PMQueueEntry).filter(PMQueueEntry.status == "PENDING").all()
    created: list[WorkOrder] = []
    for entry in entries:
        task = db.query(AssetTask).filter(AssetTask.id == entry.asset_task_id).first()
        if not task:
            continue
        wo = WorkOrder(
            site_id=task.asset.site_id if hasattr(task, "asset") else None,
            number=_next_number(db, task.asset.site_id, "PM"),
            type=WorkOrderType.PREVENTIVE,
            status=WorkOrderStatus.OPEN,
            title=f"PM: {task.description}",
            description=task.description,
            asset_id=task.asset_id,
            source_asset_task_id=task.id,
            date_due=entry.due_date,
            estimated_hours=task.estimated_hours,
            date_created=now,
        )
        if wo.site_id is None:
            from app.models import Asset

            asset = db.query(Asset).filter(Asset.id == task.asset_id).first()
            if asset:
                wo.site_id = asset.site_id
                wo.number = _next_number(db, asset.site_id, "PM")
        db.add(wo)
        db.flush()
        entry.status = "GENERATED"
        entry.work_order_id = wo.id
        created.append(wo)
    db.commit()
    return created


def evaluate_meter_pm(db: Session, asset_id, current_reading: float) -> None:
    tasks = (
        db.query(AssetTask)
        .filter(
            AssetTask.asset_id == asset_id,
            AssetTask.is_active == True,
            AssetTask.schedule_type.in_([ScheduleType.METER, ScheduleType.BOTH]),
        )
        .all()
    )
    for task in tasks:
        if task.due_meter and current_reading >= task.due_meter:
            existing = (
                db.query(PMQueueEntry)
                .filter(PMQueueEntry.asset_task_id == task.id, PMQueueEntry.status == "PENDING")
                .first()
            )
            if not existing:
                db.add(PMQueueEntry(asset_task_id=task.id, due_meter=task.due_meter, status="PENDING"))
    db.commit()
