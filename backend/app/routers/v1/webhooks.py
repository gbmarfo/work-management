from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.database import get_db
from app.models import (
    AuditLog,
    Part,
    PMQueueEntry,
    ServiceRequest,
    ServiceRequestStatus,
    User,
    UserRole,
    WebhookDeliveryLog,
    WebhookSubscription,
    WorkOrder,
    WorkOrderStatus,
    WorkOrderType,
)
from app.schemas import ExecutiveDashboard, ReportSummary, WebhookSubscriptionCreate, WebhookSubscriptionResponse
from app.services.executive_report import build_executive_dashboard

router = APIRouter(prefix="/v1", tags=["Webhooks & Reports"])


@router.post("/webhooks", response_model=WebhookSubscriptionResponse)
def create_webhook(body: WebhookSubscriptionCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    sub = WebhookSubscription(**body.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/webhooks", response_model=list[WebhookSubscriptionResponse])
def list_webhooks(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    q = db.query(WebhookSubscription).filter(WebhookSubscription.deleted_at.is_(None))
    if site_id:
        q = q.filter(WebhookSubscription.site_id == site_id)
    return q.all()


@router.delete("/webhooks/{sub_id}")
def delete_webhook(sub_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404)
    sub.is_active = False
    db.commit()
    return {"deleted": True}


@router.get("/webhooks/{sub_id}/logs")
def webhook_logs(sub_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    return db.query(WebhookDeliveryLog).filter(WebhookDeliveryLog.subscription_id == sub_id).order_by(WebhookDeliveryLog.delivered_at.desc()).limit(50).all()


@router.get("/reports/summary", response_model=ReportSummary)
def report_summary(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wo_q = db.query(WorkOrder).filter(WorkOrder.deleted_at.is_(None))
    sr_q = db.query(ServiceRequest).filter(ServiceRequest.deleted_at.is_(None))
    part_q = db.query(Part).filter(Part.deleted_at.is_(None))
    pm_q = db.query(PMQueueEntry).filter(PMQueueEntry.status == "PENDING")
    if site_id:
        wo_q = wo_q.filter(WorkOrder.site_id == site_id)
        sr_q = sr_q.filter(ServiceRequest.site_id == site_id)
        part_q = part_q.filter(Part.site_id == site_id)
    open_wo = wo_q.filter(WorkOrder.status.in_([WorkOrderStatus.OPEN, WorkOrderStatus.IN_PROGRESS])).count()
    open_cm = wo_q.filter(
        WorkOrder.type == WorkOrderType.CORRECTIVE,
        WorkOrder.status.in_([WorkOrderStatus.OPEN, WorkOrderStatus.IN_PROGRESS]),
    ).count()
    now = datetime.now(timezone.utc)
    overdue = wo_q.filter(
        WorkOrder.status.notin_([WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]),
        WorkOrder.date_due.isnot(None),
        WorkOrder.date_due < now,
    ).count()
    open_sr = sr_q.filter(ServiceRequest.status == ServiceRequestStatus.OPEN).count()
    low_parts = part_q.filter(Part.quantity_on_hand <= Part.reorder_point).count()
    pending_pm = pm_q.count()
    return ReportSummary(
        open_work_orders=open_wo,
        overdue_work_orders=overdue,
        open_corrective_maintenance=open_cm,
        open_service_requests=open_sr,
        parts_below_reorder=low_parts,
        pending_pm_queue=pending_pm,
    )


@router.get("/reports/executive", response_model=ExecutiveDashboard)
def executive_dashboard(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return build_executive_dashboard(db, site_id)


@router.get("/audit-logs")
def list_audit_logs(entity_type: str | None = None, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
