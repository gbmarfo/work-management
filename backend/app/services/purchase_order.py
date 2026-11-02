"""Purchase order totals and FaciliWorks-aligned response serialization."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    CostCenter,
    Part,
    Personnel,
    Project,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Site,
    Supplier,
)
from app.schemas import PurchaseOrderLineResponse, PurchaseOrderResponse

PO_STATUS_LABELS = {
    PurchaseOrderStatus.DRAFT: "Draft",
    PurchaseOrderStatus.SUBMITTED: "Submitted",
    PurchaseOrderStatus.APPROVED: "Approved",
    PurchaseOrderStatus.RECEIVED: "Received",
    PurchaseOrderStatus.CANCELLED: "Cancelled",
}


def line_part_amount(line: PurchaseOrderLine) -> float:
    return line.quantity * line.unit_price


def line_received_amount(line: PurchaseOrderLine) -> float:
    return line.quantity_received * line.unit_price


def recalculate_purchase_order_totals(po: PurchaseOrder, lines: list[PurchaseOrderLine]) -> None:
    part_total = sum(line_part_amount(line) for line in lines)
    received_total = sum(line_received_amount(line) for line in lines)
    po.total_part_amount = part_total
    po.total_item_amount = part_total
    po.total_amount = part_total
    po.grand_total = part_total + (po.total_tax or 0) + (po.total_shipping or 0) + (po.total_other or 0)
    po.received_total = received_total


def serialize_purchase_order(db: Session, po: PurchaseOrder, include_lines: bool = True) -> PurchaseOrderResponse:
    site = db.query(Site).filter(Site.id == po.site_id).first()
    supplier = db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
    cost_center = db.query(CostCenter).filter(CostCenter.id == po.cost_center_id).first() if po.cost_center_id else None
    project = db.query(Project).filter(Project.id == po.project_id).first() if po.project_id else None
    originator = db.query(Personnel).filter(Personnel.id == po.originator_id).first() if po.originator_id else None

    lines: list[PurchaseOrderLineResponse] = []
    if include_lines:
        po_lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
        part_ids = {line.part_id for line in po_lines}
        parts = {p.id: p for p in db.query(Part).filter(Part.id.in_(part_ids)).all()} if part_ids else {}
        for line in po_lines:
            part = parts.get(line.part_id)
            lines.append(
                PurchaseOrderLineResponse(
                    id=line.id,
                    part_id=line.part_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    quantity_received=line.quantity_received,
                    part_number=part.part_number if part else None,
                    part_description=part.description if part else None,
                )
            )

    status_label = PO_STATUS_LABELS.get(po.status, po.status.value)

    return PurchaseOrderResponse(
        id=po.id,
        site_id=po.site_id,
        number=po.number,
        name=po.name,
        supplier_id=po.supplier_id,
        status=po.status,
        account_no=po.account_no,
        created_by=po.created_by,
        last_modified_by=po.last_modified_by,
        created_at=po.created_at,
        updated_at=po.updated_at,
        date_submitted=po.date_submitted,
        date_received=po.date_received,
        date_completed=po.date_completed,
        date_expected=po.date_expected,
        date_originated=po.date_originated,
        total_tax=po.total_tax or 0,
        total_shipping=po.total_shipping or 0,
        total_other=po.total_other or 0,
        billing_name=po.billing_name,
        billing_addr1=po.billing_addr1,
        billing_addr2=po.billing_addr2,
        billing_city=po.billing_city,
        billing_state_province=po.billing_state_province,
        billing_postal_code=po.billing_postal_code,
        billing_country_code=po.billing_country_code,
        shipping_name=po.shipping_name,
        shipping_addr1=po.shipping_addr1,
        shipping_addr2=po.shipping_addr2,
        shipping_city=po.shipping_city,
        shipping_state_province=po.shipping_state_province,
        shipping_postal_code=po.shipping_postal_code,
        shipping_country_code=po.shipping_country_code,
        notes=po.notes,
        name_format=po.name_format,
        total_part_amount=po.total_part_amount or 0,
        total_item_amount=po.total_item_amount or 0,
        total_amount=po.total_amount or 0,
        grand_total=po.grand_total or 0,
        received_total=po.received_total or 0,
        last_signed_by=po.last_signed_by,
        last_signed=po.last_signed,
        last_signed_on=po.last_signed_on,
        region_id=po.region_id,
        region_name=po.region_name,
        cost_center_id=po.cost_center_id,
        project_id=po.project_id,
        originator_id=po.originator_id,
        po_status_category=po.po_status_category,
        last_reminded_on=po.last_reminded_on,
        is_auto_generate=po.is_auto_generate,
        correlation_id=po.correlation_id,
        medium_count=po.medium_count or 0,
        site_no=site.code if site else None,
        site_name=site.name if site else None,
        supplier_no=supplier.supplier_code if supplier else None,
        supplier_name=supplier.name if supplier else None,
        cost_center_no=cost_center.number if cost_center else None,
        cost_center_name=cost_center.name if cost_center else None,
        project_no=project.number if project else None,
        project_name=project.name if project else None,
        originator_no=originator.employee_id if originator else None,
        originator_name=originator.full_name if originator else None,
        po_status_name=status_label,
        po_status_no=po.status.value,
        lines=lines,
    )
