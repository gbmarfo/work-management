from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: UUID,
    action: str,
    actor_id: UUID | None = None,
    actor_email: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            before_state=before,
            after_state=after,
        )
    )
