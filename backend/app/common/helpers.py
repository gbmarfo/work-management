from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session


def next_number(db: Session, model, site_id: UUID, prefix: str) -> str:
    count = db.query(model).filter(model.site_id == site_id).count()
    return f"{prefix}-{count + 1:06d}"


def utcnow():
    return datetime.now(timezone.utc)
