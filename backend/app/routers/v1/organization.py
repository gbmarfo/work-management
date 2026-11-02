from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.helpers import utcnow
from app.common.pagination import apply_partial_update, paginate
from app.common.search import apply_search
from app.database import get_db
from app.models import (
    Budget,
    BudgetYear,
    CostCenter,
    Location,
    LookupType,
    LookupValue,
    Organization,
    Project,
    Site,
    User,
    UserRole,
)
from app.services.cost_center import serialize_cost_center
from app.schemas import (
    BudgetCreate,
    BudgetResponse,
    BudgetYearCreate,
    CostCenterCreate,
    CostCenterResponse,
    CostCenterUpdate,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    LookupValueCreate,
    LookupValueResponse,
    LookupValueUpdate,
    LookupTypeResponse,
    LookupTypeUpdate,
    OrganizationCreate,
    OrganizationResponse,
    ProjectCreate,
    ProjectResponse,
    SiteCreate,
    SiteResponse,
    SiteUpdate,
)

router = APIRouter(prefix="/v1", tags=["Organization"])


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(body: OrganizationCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    org = Organization(name=body.name, settings=body.settings)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/organizations", response_model=list[OrganizationResponse])
def list_organizations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Organization).filter(Organization.deleted_at.is_(None)).all()


@router.post("/sites", response_model=SiteResponse)
def create_site(body: SiteCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    site = Site(**body.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/sites", response_model=list[SiteResponse])
def list_sites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Site).filter(Site.deleted_at.is_(None)).all()


@router.get("/sites/{site_id}", response_model=SiteResponse)
def get_site(site_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.deleted_at.is_(None)).first()
    if not site:
        raise HTTPException(status_code=404)
    return site


@router.put("/sites/{site_id}", response_model=SiteResponse)
def update_site(site_id: UUID, body: SiteUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    site = db.query(Site).filter(Site.id == site_id, Site.deleted_at.is_(None)).first()
    if not site:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(site, data, body.fields_to_update)
    db.commit()
    db.refresh(site)
    return site


@router.delete("/sites/{site_id}")
def delete_site(site_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    site = db.query(Site).filter(Site.id == site_id, Site.deleted_at.is_(None)).first()
    if not site:
        raise HTTPException(status_code=404)
    site.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@router.post("/locations", response_model=LocationResponse)
def create_location(body: LocationCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    loc = Location(**body.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.get("/locations", response_model=list[LocationResponse])
def list_locations(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    criticality: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Location).filter(Location.deleted_at.is_(None))
    if site_id:
        q = q.filter(Location.site_id == site_id)
    if criticality:
        q = q.filter(Location.criticality == criticality)
    q = apply_search(q, search, Location.number, Location.name)
    return q.order_by(Location.number).all()


@router.get("/locations/{location_id}", response_model=LocationResponse)
def get_location(location_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loc = db.query(Location).filter(Location.id == location_id, Location.deleted_at.is_(None)).first()
    if not loc:
        raise HTTPException(status_code=404)
    return loc


@router.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(location_id: UUID, body: LocationUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    loc = db.query(Location).filter(Location.id == location_id, Location.deleted_at.is_(None)).first()
    if not loc:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(loc, data, body.fields_to_update)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/locations/{location_id}")
def delete_location(location_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    loc = db.query(Location).filter(Location.id == location_id, Location.deleted_at.is_(None)).first()
    if not loc:
        raise HTTPException(status_code=404)
    loc.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@router.post("/cost-centers", response_model=CostCenterResponse)
def create_cost_center(body: CostCenterCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    cc = CostCenter(created_by=user.email, **body.model_dump())
    db.add(cc)
    db.commit()
    db.refresh(cc)
    return serialize_cost_center(db, cc)


@router.get("/cost-centers", response_model=list[CostCenterResponse])
def list_cost_centers(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    active: bool | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(CostCenter).filter(CostCenter.deleted_at.is_(None))
    if site_id:
        q = q.filter(CostCenter.site_id == site_id)
    if active is not None:
        q = q.filter(CostCenter.active.is_(active))
    q = apply_search(q, search, CostCenter.number, CostCenter.name, CostCenter.description)
    items = q.order_by(CostCenter.number).all()
    return [serialize_cost_center(db, cc) for cc in items]


@router.get("/cost-centers/{cost_center_id}", response_model=CostCenterResponse)
def get_cost_center(cost_center_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cc = db.query(CostCenter).filter(CostCenter.id == cost_center_id, CostCenter.deleted_at.is_(None)).first()
    if not cc:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return serialize_cost_center(db, cc)


@router.put("/cost-centers/{cost_center_id}", response_model=CostCenterResponse)
def update_cost_center(
    cost_center_id: UUID,
    body: CostCenterUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER)),
):
    cc = db.query(CostCenter).filter(CostCenter.id == cost_center_id, CostCenter.deleted_at.is_(None)).first()
    if not cc:
        raise HTTPException(status_code=404, detail="Cost center not found")
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(cc, data, body.fields_to_update)
    cc.last_modified_by = user.email
    db.commit()
    db.refresh(cc)
    return serialize_cost_center(db, cc)


@router.delete("/cost-centers/{cost_center_id}")
def delete_cost_center(
    cost_center_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER)),
):
    cc = db.query(CostCenter).filter(CostCenter.id == cost_center_id, CostCenter.deleted_at.is_(None)).first()
    if not cc:
        raise HTTPException(status_code=404, detail="Cost center not found")
    cc.deleted_at = utcnow()
    cc.last_modified_by = user.email
    db.commit()
    return {"deleted": True}


@router.post("/projects", response_model=ProjectResponse)
def create_project(body: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    proj = Project(**body.model_dump())
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Project).filter(Project.deleted_at.is_(None))
    if site_id:
        q = q.filter(Project.site_id == site_id)
    return q.all()


@router.post("/budget-years")
def create_budget_year(body: BudgetYearCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    by = BudgetYear(**body.model_dump())
    db.add(by)
    db.commit()
    db.refresh(by)
    return by


@router.post("/budgets", response_model=BudgetResponse)
def create_budget(body: BudgetCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    b = Budget(**body.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.get("/lookups", response_model=list[LookupTypeResponse])
def list_lookups(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    types = db.query(LookupType).order_by(LookupType.name).all()
    result: list[LookupTypeResponse] = []
    for lt in types:
        q = db.query(LookupValue).filter(LookupValue.lookup_type_id == lt.id)
        if not include_inactive:
            q = q.filter(LookupValue.is_active.is_(True))
        values = q.order_by(LookupValue.sort_order, LookupValue.label).all()
        result.append(
            LookupTypeResponse(
                id=lt.id,
                code=lt.code,
                name=lt.name,
                values=[LookupValueResponse.model_validate(v) for v in values],
            )
        )
    return result


@router.get("/lookups/{code}", response_model=LookupTypeResponse)
def get_lookup(
    code: str,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lt = db.query(LookupType).filter(LookupType.code == code).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Lookup type not found")
    q = db.query(LookupValue).filter(LookupValue.lookup_type_id == lt.id)
    if not include_inactive:
        q = q.filter(LookupValue.is_active.is_(True))
    values = q.order_by(LookupValue.sort_order, LookupValue.label).all()
    return LookupTypeResponse(
        id=lt.id,
        code=lt.code,
        name=lt.name,
        values=[LookupValueResponse.model_validate(v) for v in values],
    )


@router.put("/lookups/{code}", response_model=LookupTypeResponse)
def update_lookup_type(
    code: str,
    body: LookupTypeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    lt = db.query(LookupType).filter(LookupType.code == code).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Lookup type not found")
    if body.name is not None:
        lt.name = body.name
    db.commit()
    db.refresh(lt)
    values = (
        db.query(LookupValue)
        .filter(LookupValue.lookup_type_id == lt.id)
        .order_by(LookupValue.sort_order, LookupValue.label)
        .all()
    )
    return LookupTypeResponse(
        id=lt.id,
        code=lt.code,
        name=lt.name,
        values=[LookupValueResponse.model_validate(v) for v in values],
    )


@router.post("/lookups/{code}/values", response_model=LookupValueResponse)
def add_lookup_value(code: str, body: LookupValueCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    lt = db.query(LookupType).filter(LookupType.code == code).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Lookup type not found")
    existing = (
        db.query(LookupValue)
        .filter(LookupValue.lookup_type_id == lt.id, LookupValue.code == body.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Lookup code '{body.code}' already exists")
    val = LookupValue(lookup_type_id=lt.id, **body.model_dump())
    db.add(val)
    db.commit()
    db.refresh(val)
    return val


@router.put("/lookups/{code}/values/{value_id}", response_model=LookupValueResponse)
def update_lookup_value(
    code: str,
    value_id: UUID,
    body: LookupValueUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    lt = db.query(LookupType).filter(LookupType.code == code).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Lookup type not found")
    val = (
        db.query(LookupValue)
        .filter(LookupValue.id == value_id, LookupValue.lookup_type_id == lt.id)
        .first()
    )
    if not val:
        raise HTTPException(status_code=404, detail="Lookup value not found")
    data = body.model_dump(exclude_none=True)
    if "code" in data and data["code"] != val.code:
        duplicate = (
            db.query(LookupValue)
            .filter(LookupValue.lookup_type_id == lt.id, LookupValue.code == data["code"], LookupValue.id != value_id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail=f"Lookup code '{data['code']}' already exists")
    apply_partial_update(val, data, None)
    db.commit()
    db.refresh(val)
    return val
