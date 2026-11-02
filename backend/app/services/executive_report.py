"""Executive dashboard metrics for leadership reporting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    Asset,
    PMQueueEntry,
    Part,
    ServiceRequest,
    ServiceRequestStatus,
    Site,
    WorkOrder,
    WorkOrderStatus,
    WorkOrderType,
)
from app.schemas import (
    AttentionItem,
    ExecutiveDashboard,
    PriorityBreakdown,
    WorkOrderMix,
    WorkOrderTrendPoint,
)

DOWN_STATUSES = {"DOWN", "OUT_OF_SERVICE", "INACTIVE", "OFFLINE"}
PRIORITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_overdue(wo: WorkOrder, now: datetime) -> bool:
    return (
        wo.status not in (WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED)
        and wo.date_due is not None
        and wo.date_due < now
    )


def _priority_bucket(priority: str | None) -> str:
    if not priority:
        return "other"
    key = priority.upper()
    if key in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return key.lower()
    return "other"


def _month_start(d: datetime, months_back: int) -> datetime:
    month = d.month - months_back
    year = d.year
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1, tzinfo=timezone.utc)


def build_executive_dashboard(db: Session, site_id: UUID | None = None) -> ExecutiveDashboard:
    now = _now()
    thirty_days_ago = now - timedelta(days=30)
    trend_map: dict[str, dict[str, int]] = {}
    month_starts = [_month_start(now, i) for i in range(5, -1, -1)]
    for month_start in month_starts:
        key = month_start.strftime("%b %Y")
        trend_map[key] = {"completed": 0, "opened": 0}
    six_months_ago = month_starts[0]

    site_name = "All Sites"
    if site_id:
        site = db.query(Site).filter(Site.id == site_id).first()
        if site:
            site_name = site.name

    asset_q = db.query(Asset).filter(Asset.deleted_at.is_(None), Asset.is_retired.is_(False))
    wo_q = db.query(WorkOrder).filter(WorkOrder.deleted_at.is_(None))
    sr_q = db.query(ServiceRequest).filter(ServiceRequest.deleted_at.is_(None))
    part_q = db.query(Part).filter(Part.deleted_at.is_(None))
    pm_q = db.query(PMQueueEntry).filter(PMQueueEntry.status == "PENDING")

    if site_id:
        asset_q = asset_q.filter(Asset.site_id == site_id)
        wo_q = wo_q.filter(WorkOrder.site_id == site_id)
        sr_q = sr_q.filter(ServiceRequest.site_id == site_id)
        part_q = part_q.filter(Part.site_id == site_id)

    assets = asset_q.all()
    work_orders = wo_q.all()
    total_assets = len(assets)
    active_assets = sum(1 for a in assets if (a.status or "").upper() == "ACTIVE")
    down_assets = sum(1 for a in assets if (a.status or "").upper() in DOWN_STATUSES)
    critical_assets = sum(1 for a in assets if a.is_critical)
    total_asset_value = sum(a.cost or 0 for a in assets)
    availability = round((active_assets / total_assets * 100) if total_assets else 100.0, 1)

    open_statuses = (WorkOrderStatus.OPEN, WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.WAITING_PARTS, WorkOrderStatus.WAITING_CONTRACTOR)
    open_wo = [wo for wo in work_orders if wo.status in open_statuses]
    open_cm = sum(1 for wo in open_wo if wo.type == WorkOrderType.CORRECTIVE)
    overdue = sum(1 for wo in work_orders if _is_overdue(wo, now))
    open_sr = sr_q.filter(ServiceRequest.status == ServiceRequestStatus.OPEN).count()
    low_parts = part_q.filter(Part.quantity_on_hand <= Part.reorder_point).count()
    pending_pm = pm_q.count()

    completed_recent = [
        wo for wo in work_orders
        if wo.status == WorkOrderStatus.COMPLETED
        and wo.date_completed
        and wo.date_completed >= thirty_days_ago
    ]
    opened_recent = [
        wo for wo in work_orders
        if wo.date_created and wo.date_created >= thirty_days_ago
    ]
    still_open_recent = [wo for wo in opened_recent if wo.status in open_statuses]
    completion_denominator = len(completed_recent) + len(still_open_recent)
    wo_completion_rate = round(len(completed_recent) / completion_denominator * 100, 1) if completion_denominator else 100.0

    resolution_days: list[float] = []
    for wo in work_orders:
        if wo.status == WorkOrderStatus.COMPLETED and wo.date_created and wo.date_completed:
            delta = (wo.date_completed - wo.date_created).total_seconds() / 86400
            if delta >= 0:
                resolution_days.append(delta)
    avg_resolution = round(sum(resolution_days) / len(resolution_days), 1) if resolution_days else None

    pm_total = db.query(PMQueueEntry).count()
    pm_done = db.query(PMQueueEntry).filter(PMQueueEntry.status != "PENDING").count()
    pm_compliance = round(pm_done / pm_total * 100, 1) if pm_total else 100.0

    mix = WorkOrderMix(
        corrective=sum(1 for wo in open_wo if wo.type == WorkOrderType.CORRECTIVE),
        preventive=sum(1 for wo in open_wo if wo.type == WorkOrderType.PREVENTIVE),
        general=sum(1 for wo in open_wo if wo.type == WorkOrderType.GENERAL),
    )

    priority = PriorityBreakdown(critical=0, high=0, medium=0, low=0, other=0)
    for wo in open_wo:
        bucket = _priority_bucket(wo.priority)
        setattr(priority, bucket, getattr(priority, bucket) + 1)

    for wo in work_orders:
        if wo.date_created and wo.date_created >= six_months_ago:
            key = wo.date_created.strftime("%b %Y")
            if key in trend_map:
                trend_map[key]["opened"] += 1
        if wo.status == WorkOrderStatus.COMPLETED and wo.date_completed and wo.date_completed >= six_months_ago:
            key = wo.date_completed.strftime("%b %Y")
            if key in trend_map:
                trend_map[key]["completed"] += 1

    trend = [
        WorkOrderTrendPoint(month=month, completed=vals["completed"], opened=vals["opened"])
        for month, vals in trend_map.items()
    ]

    attention: list[AttentionItem] = []
    for wo in sorted(open_wo, key=lambda w: (PRIORITY_RANK.get((w.priority or "").upper(), 9), w.date_due or now)):
        asset_name = None
        if wo.asset_id:
            asset = db.query(Asset).filter(Asset.id == wo.asset_id).first()
            asset_name = asset.name if asset else None
        attention.append(
            AttentionItem(
                id=str(wo.id),
                kind="work_order",
                title=wo.title,
                subtitle=f"{wo.number} · {wo.type.value.replace('_', ' ').title()}" + (f" · {asset_name}" if asset_name else ""),
                priority=wo.priority,
                status="OVERDUE" if _is_overdue(wo, now) else wo.status.value,
                due_date=wo.date_due,
                path=f"/work-orders/{wo.id}/edit",
            )
        )

    for sr in sr_q.filter(ServiceRequest.status == ServiceRequestStatus.OPEN).order_by(ServiceRequest.created_at.desc()).limit(5):
        attention.append(
            AttentionItem(
                id=str(sr.id),
                kind="service_request",
                title=(sr.problem[:72] + "…") if len(sr.problem) > 72 else sr.problem,
                subtitle=f"{sr.number} · Service Request",
                priority=sr.priority,
                status=sr.status.value,
                due_date=None,
                path=f"/service-requests/{sr.id}/edit",
            )
        )

    for asset in assets:
        if (asset.status or "").upper() in DOWN_STATUSES:
            attention.append(
                AttentionItem(
                    id=str(asset.id),
                    kind="asset",
                    title=asset.name,
                    subtitle=f"{asset.number} · Asset offline",
                    priority=asset.priority,
                    status=asset.status,
                    due_date=None,
                    path=f"/assets/{asset.id}/edit",
                )
            )

    attention.sort(key=lambda item: (0 if item.status == "OVERDUE" else 1, PRIORITY_RANK.get((item.priority or "").upper(), 9)))
    attention = attention[:8]

    health = 100
    health -= min(40, overdue * 8)
    health -= min(25, down_assets * 10)
    health -= min(15, low_parts * 5)
    health -= min(20, max(0, 100 - pm_compliance) // 5)
    health = max(0, min(100, health))

    return ExecutiveDashboard(
        site_name=site_name,
        generated_at=now,
        health_score=health,
        open_work_orders=len(open_wo),
        overdue_work_orders=overdue,
        open_corrective_maintenance=open_cm,
        open_service_requests=open_sr,
        parts_below_reorder=low_parts,
        pending_pm_queue=pending_pm,
        total_assets=total_assets,
        active_assets=active_assets,
        down_assets=down_assets,
        critical_assets=critical_assets,
        asset_availability_pct=availability,
        total_asset_value=round(total_asset_value, 2),
        pm_compliance_pct=pm_compliance,
        wo_completion_rate_pct=wo_completion_rate,
        completed_last_30_days=len(completed_recent),
        avg_resolution_days=avg_resolution,
        work_order_trend=trend,
        work_order_mix=mix,
        priority_breakdown=priority,
        attention_items=attention,
    )
