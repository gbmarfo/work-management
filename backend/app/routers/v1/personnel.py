from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.helpers import utcnow
from app.common.pagination import apply_partial_update
from app.common.search import apply_search
from app.database import get_db
from app.models import Personnel, PersonnelType, SecurityGroup, Training, User, UserRole
from app.schemas import CustomFieldDefinitionCreate, CustomFieldDefinitionResponse, CustomFieldDefinitionUpdate, PersonnelCreate, PersonnelResponse, PersonnelUpdate, TrainingCreate

router = APIRouter(prefix="/v1", tags=["Personnel & Security"])


@router.post("/personnel", response_model=PersonnelResponse)
def create_personnel(body: PersonnelCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    p = Personnel(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/personnel", response_model=list[PersonnelResponse])
def list_personnel(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    personnel_type: PersonnelType | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Personnel).filter(Personnel.deleted_at.is_(None))
    if site_id:
        q = q.filter(Personnel.site_id == site_id)
    if personnel_type:
        q = q.filter(Personnel.personnel_type == personnel_type)
    q = apply_search(q, search, Personnel.full_name, Personnel.email, Personnel.employee_id, Personnel.craft, Personnel.department)
    return q.order_by(Personnel.full_name).all()


@router.get("/personnel/{personnel_id}", response_model=PersonnelResponse)
def get_personnel(personnel_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.query(Personnel).filter(Personnel.id == personnel_id, Personnel.deleted_at.is_(None)).first()
    if not p:
        raise HTTPException(status_code=404)
    return p


@router.put("/personnel/{personnel_id}", response_model=PersonnelResponse)
def update_personnel(personnel_id: UUID, body: PersonnelUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    p = db.query(Personnel).filter(Personnel.id == personnel_id, Personnel.deleted_at.is_(None)).first()
    if not p:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(p, data, body.fields_to_update)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/personnel/{personnel_id}")
def delete_personnel(personnel_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    p = db.query(Personnel).filter(Personnel.id == personnel_id, Personnel.deleted_at.is_(None)).first()
    if not p:
        raise HTTPException(status_code=404)
    p.deleted_at = utcnow()
    p.is_active = False
    db.commit()
    return {"deleted": True}


@router.post("/personnel/{personnel_id}/trainings")
def add_training(personnel_id: UUID, body: TrainingCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    t = Training(personnel_id=personnel_id, **body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/personnel/{personnel_id}/trainings")
def list_trainings(personnel_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Training).filter(Training.personnel_id == personnel_id).all()


@router.post("/security-groups")
def create_security_group(site_id: UUID, name: str, description: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    sg = SecurityGroup(site_id=site_id, name=name, description=description)
    db.add(sg)
    db.commit()
    db.refresh(sg)
    return sg


@router.get("/security-groups")
def list_security_groups(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(SecurityGroup).filter(SecurityGroup.deleted_at.is_(None))
    if site_id:
        q = q.filter(SecurityGroup.site_id == site_id)
    return q.all()


@router.post("/custom-fields", response_model=CustomFieldDefinitionResponse)
def create_custom_field(body: CustomFieldDefinitionCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    from app.models import CustomFieldDefinition

    name = body.name.strip().lower().replace(" ", "_")
    existing = (
        db.query(CustomFieldDefinition)
        .filter(
            CustomFieldDefinition.site_id == body.site_id,
            CustomFieldDefinition.entity_type == body.entity_type,
            CustomFieldDefinition.name == name,
            CustomFieldDefinition.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Custom field '{name}' already exists for this entity type")
    cf = CustomFieldDefinition(**{**body.model_dump(), "name": name})
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return cf


@router.get("/custom-fields", response_model=list[CustomFieldDefinitionResponse])
def list_custom_fields(site_id: UUID | None = None, entity_type: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models import CustomFieldDefinition, CustomFieldEntity

    q = db.query(CustomFieldDefinition).filter(CustomFieldDefinition.deleted_at.is_(None))
    if site_id:
        q = q.filter(CustomFieldDefinition.site_id == site_id)
    if entity_type:
        q = q.filter(CustomFieldDefinition.entity_type == CustomFieldEntity(entity_type))
    return q.order_by(CustomFieldDefinition.label).all()


@router.put("/custom-fields/{field_id}", response_model=CustomFieldDefinitionResponse)
def update_custom_field(
    field_id: UUID,
    body: CustomFieldDefinitionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    from app.models import CustomFieldDefinition

    cf = db.query(CustomFieldDefinition).filter(CustomFieldDefinition.id == field_id, CustomFieldDefinition.deleted_at.is_(None)).first()
    if not cf:
        raise HTTPException(status_code=404, detail="Custom field not found")
    data = body.model_dump(exclude_none=True)
    apply_partial_update(cf, data, None)
    db.commit()
    db.refresh(cf)
    return cf


@router.delete("/custom-fields/{field_id}")
def delete_custom_field(field_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    from app.models import CustomFieldDefinition

    cf = db.query(CustomFieldDefinition).filter(CustomFieldDefinition.id == field_id, CustomFieldDefinition.deleted_at.is_(None)).first()
    if not cf:
        raise HTTPException(status_code=404, detail="Custom field not found")
    cf.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}
