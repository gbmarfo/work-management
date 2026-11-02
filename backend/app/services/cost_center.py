"""Cost center response serialization aligned with Asset Essentials API."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import CostCenter, Site
from app.schemas import CostCenterResponse


def serialize_cost_center(db: Session, cost_center: CostCenter) -> CostCenterResponse:
    site = db.query(Site).filter(Site.id == cost_center.site_id).first()
    return CostCenterResponse(
        id=cost_center.id,
        site_id=cost_center.site_id,
        number=cost_center.number,
        name=cost_center.name,
        description=cost_center.description,
        active=cost_center.active,
        color_code=cost_center.color_code,
        created_by=cost_center.created_by,
        last_modified_by=cost_center.last_modified_by,
        created_at=cost_center.created_at,
        updated_at=cost_center.updated_at,
        row_version=cost_center.row_version,
        site_no=site.code if site else None,
        site_name=site.name if site else None,
    )
