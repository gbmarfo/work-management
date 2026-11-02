"""Asset response serialization with FaciliWorks-aligned enriched fields."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    Asset,
    Attachment,
    AttachmentEntity,
    AttachmentKind,
    CostCenter,
    Location,
    Site,
    Supplier,
)
from app.schemas import AssetResponse


def _location_path(db: Session, location: Location | None) -> str | None:
    if not location:
        return None
    parts: list[str] = []
    current: Location | None = location
    seen: set[object] = set()
    while current and current.id not in seen:
        seen.add(current.id)
        parts.append(current.name)
        if not current.parent_id:
            break
        current = db.query(Location).filter(Location.id == current.parent_id).first()
    parts.reverse()
    return " / ".join(parts) if parts else location.name


def serialize_asset(db: Session, asset: Asset, custom_fields: dict | None = None) -> AssetResponse:
    site = db.query(Site).filter(Site.id == asset.site_id).first()
    location = (
        db.query(Location).filter(Location.id == asset.current_location_id).first()
        if asset.current_location_id
        else None
    )
    cost_center = (
        db.query(CostCenter).filter(CostCenter.id == asset.cost_center_id).first()
        if asset.cost_center_id
        else None
    )
    supplier = db.query(Supplier).filter(Supplier.id == asset.supplier_id).first() if asset.supplier_id else None
    warranty_vendor = (
        db.query(Supplier).filter(Supplier.id == asset.warranty_vendor_id).first()
        if asset.warranty_vendor_id
        else None
    )
    parent_asset = db.query(Asset).filter(Asset.id == asset.parent_asset_id).first() if asset.parent_asset_id else None

    photo = (
        db.query(Attachment)
        .filter(
            Attachment.entity_type == AttachmentEntity.ASSET,
            Attachment.entity_id == asset.id,
            Attachment.kind == AttachmentKind.PHOTO,
            Attachment.is_primary.is_(True),
        )
        .first()
    )
    if not photo:
        photo = (
            db.query(Attachment)
            .filter(
                Attachment.entity_type == AttachmentEntity.ASSET,
                Attachment.entity_id == asset.id,
                Attachment.kind == AttachmentKind.PHOTO,
            )
            .order_by(Attachment.created_at.desc())
            .first()
        )

    return AssetResponse(
        id=asset.id,
        site_id=asset.site_id,
        number=asset.number,
        name=asset.name,
        description=asset.description,
        asset_no=asset.asset_no,
        serial_number=asset.serial_number,
        make=asset.make,
        model=asset.model,
        manufacturer=asset.manufacturer,
        bar_code=asset.bar_code,
        rfid=asset.rfid,
        category=asset.category,
        sub_category=asset.sub_category,
        sub_category_no=asset.sub_category_no,
        status=asset.status,
        substatus=asset.substatus,
        asset_status_category=asset.asset_status_category,
        asset_condition_no=asset.asset_condition_no,
        asset_condition_name=asset.asset_condition_name,
        priority=asset.priority,
        criticality=asset.criticality,
        criticality_weight=asset.criticality_weight,
        cost=asset.cost,
        replacement_cost=asset.replacement_cost,
        salvage_value=asset.salvage_value,
        purchase_date=asset.purchase_date,
        invoice_no=asset.invoice_no,
        invoice_date=asset.invoice_date,
        purchase_note=asset.purchase_note,
        equipment_life=asset.equipment_life,
        warranty_expiration_date=asset.warranty_expiration_date,
        warranty_title=asset.warranty_title,
        warranty_note=asset.warranty_note,
        service_date=asset.service_date,
        retirement_date=asset.retirement_date,
        retirement_reason=asset.retirement_reason,
        manufacture_on=asset.manufacture_on,
        out_of_service_begin_date=asset.out_of_service_begin_date,
        out_of_service_end_date=asset.out_of_service_end_date,
        placed_on=asset.placed_on,
        removed_on=asset.removed_on,
        condition_date=asset.condition_date,
        estimated_replacement_date=asset.estimated_replacement_date,
        last_checked_out_date=asset.last_checked_out_date,
        current_location_id=asset.current_location_id,
        cost_center_id=asset.cost_center_id,
        supplier_id=asset.supplier_id,
        warranty_vendor_id=asset.warranty_vendor_id,
        parent_asset_id=asset.parent_asset_id,
        is_critical=asset.is_critical,
        is_retired=asset.is_retired,
        is_auto_generate=asset.is_auto_generate,
        is_update_medium=asset.is_update_medium,
        is_tool_crib=asset.is_tool_crib,
        is_system=asset.is_system,
        is_referenced=asset.is_referenced,
        notes=asset.notes,
        assessment_note=asset.assessment_note,
        tool_crib_note=asset.tool_crib_note,
        emergency_note=asset.emergency_note,
        safety_note=asset.safety_note,
        training_note=asset.training_note,
        shutdown_procedure=asset.shutdown_procedure,
        loto_procedure=asset.loto_procedure,
        hyperlink=asset.hyperlink,
        tag_number=asset.tag_number,
        manufacturer_no=asset.manufacturer_no,
        latitude=asset.latitude if asset.latitude is not None else (location.latitude if location else None),
        longitude=asset.longitude if asset.longitude is not None else (location.longitude if location else None),
        medium_ids=asset.medium_ids,
        total_cost=asset.total_cost or 0,
        total_hours=asset.total_hours or 0,
        total_downtime=asset.total_downtime or 0,
        estimated_hours=asset.estimated_hours,
        measurement_unit_id=asset.measurement_unit_id,
        uom_cost=asset.uom_cost,
        uom_quantity=asset.uom_quantity,
        system_name=asset.system_name,
        correlation_id=asset.correlation_id,
        security_group_id=asset.security_group_id,
        fs_type=asset.fs_type,
        nist=asset.nist,
        ref_standard=asset.ref_standard,
        attach_to_event=asset.attach_to_event,
        asset_disposition=asset.asset_disposition,
        user_def1=asset.user_def1,
        user_def2=asset.user_def2,
        user_def3=asset.user_def3,
        created_by=asset.created_by,
        last_modified_by=asset.last_modified_by,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        row_version=asset.row_version,
        custom_fields=custom_fields,
        site_no=site.code if site else None,
        site_name=site.name if site else None,
        category_no=asset.category,
        category_name=asset.category,
        cost_center_no=cost_center.number if cost_center else None,
        cost_center_name=cost_center.name if cost_center else None,
        location_no=location.number if location else None,
        location_name=location.name if location else None,
        location_path=_location_path(db, location),
        asset_status_name=asset.status,
        asset_status_no=asset.status,
        criticality_no=asset.criticality,
        criticality_name=asset.criticality,
        supplier_no=supplier.supplier_code if supplier else None,
        supplier_name=supplier.name if supplier else None,
        warranty_vendor_no=warranty_vendor.supplier_code if warranty_vendor else None,
        warranty_vendor_name=warranty_vendor.name if warranty_vendor else None,
        parent_asset_name=parent_asset.name if parent_asset else None,
        manufacturer_name=asset.manufacturer or asset.make,
        sub_category_name=asset.sub_category,
        photo_name=photo.file_name if photo else None,
        photo_url=f"/v1/assets/{asset.id}/attachments/{photo.id}/download" if photo else None,
    )
