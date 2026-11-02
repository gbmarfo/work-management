import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CustomFieldDefinition, CustomFieldEntity, CustomFieldValue


def get_custom_fields(
    db: Session,
    entity_type: CustomFieldEntity,
    entity_id: UUID,
    site_id: UUID | None = None,
) -> dict:
    q = (
        db.query(CustomFieldValue, CustomFieldDefinition)
        .join(CustomFieldDefinition, CustomFieldValue.definition_id == CustomFieldDefinition.id)
        .filter(
            CustomFieldDefinition.entity_type == entity_type,
            CustomFieldDefinition.deleted_at.is_(None),
            CustomFieldValue.entity_id == entity_id,
        )
    )
    if site_id:
        q = q.filter(CustomFieldDefinition.site_id == site_id)
    values = q.all()
    result = {}
    for val, defn in values:
        result[defn.name] = _parse_value(val.value, defn.data_type.value)
    return result


def _parse_value(raw: str | None, data_type: str):
    if raw is None:
        return None
    if data_type == "NUMBER":
        try:
            return float(raw)
        except ValueError:
            return raw
    if data_type == "BOOLEAN":
        return raw.lower() in ("true", "1", "yes")
    if data_type == "SELECT":
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def set_custom_fields(
    db: Session,
    entity_type: CustomFieldEntity,
    entity_id: UUID,
    fields: dict[str, object],
    site_id: UUID | None = None,
) -> None:
    if not fields:
        return
    q = db.query(CustomFieldDefinition).filter(
        CustomFieldDefinition.entity_type == entity_type,
        CustomFieldDefinition.deleted_at.is_(None),
    )
    if site_id:
        q = q.filter(CustomFieldDefinition.site_id == site_id)
    definitions = q.all()
    by_name = {d.name: d for d in definitions}
    for name, value in fields.items():
        defn = by_name.get(name)
        if not defn:
            continue
        stored = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        existing = (
            db.query(CustomFieldValue)
            .filter(
                CustomFieldValue.definition_id == defn.id,
                CustomFieldValue.entity_id == entity_id,
            )
            .first()
        )
        if existing:
            existing.value = stored
        else:
            db.add(CustomFieldValue(definition_id=defn.id, entity_id=entity_id, value=stored))
