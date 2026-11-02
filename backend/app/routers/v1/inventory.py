from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.common.custom_fields import get_custom_fields, set_custom_fields
from app.common.helpers import next_number, utcnow
from app.common.pagination import apply_partial_update, paginate
from app.common.search import apply_search
from app.database import get_db
from app.models import (
    CustomFieldEntity,
    Part,
    PartAdjustment,
    PartAssetLink,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Supplier,
    User,
    UserRole,
)
from app.services.purchase_order import recalculate_purchase_order_totals, serialize_purchase_order
from app.schemas import (
    PartAdjustRequest,
    PartCreate,
    PartResponse,
    PartUpdate,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)

router = APIRouter(prefix="/v1", tags=["Inventory"])


def _part_response(db: Session, part: Part, include_custom: bool) -> PartResponse:
    data = PartResponse.model_validate(part)
    if include_custom:
        data.custom_fields = get_custom_fields(db, CustomFieldEntity.PART, part.id)
    return data


@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(body: SupplierCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    s = Supplier(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Supplier).filter(Supplier.deleted_at.is_(None))
    if site_id:
        q = q.filter(Supplier.site_id == site_id)
    return q.all()


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_(None)).first()
    if not s:
        raise HTTPException(status_code=404)
    return s


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: UUID, body: SupplierUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    s = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_(None)).first()
    if not s:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(s, data, body.fields_to_update)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    s = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_(None)).first()
    if not s:
        raise HTTPException(status_code=404)
    s.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@router.get("/parts")
def list_parts(site_id: UUID | None = None, search: str | None = Query(None), status: str | None = Query(None), page: int = 1, page_size: int = 20, custom_fields: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Part).filter(Part.deleted_at.is_(None))
    if site_id:
        q = q.filter(Part.site_id == site_id)
    if status:
        q = q.filter(Part.status == status)
    q = apply_search(q, search, Part.part_number, Part.description, Part.manufacturer, Part.model, Part.category)
    total = q.count()
    items = q.order_by(Part.part_number).offset((page - 1) * page_size).limit(page_size).all()
    return paginate([_part_response(db, p, custom_fields) for p in items], total, page, page_size)


@router.post("/parts", response_model=PartResponse)
def create_part(body: PartCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    part = Part(**body.model_dump(exclude={"custom_fields"}))
    db.add(part)
    db.flush()
    if body.custom_fields:
        set_custom_fields(db, CustomFieldEntity.PART, part.id, body.custom_fields)
    db.commit()
    db.refresh(part)
    return _part_response(db, part, True)


@router.get("/parts/{part_id}", response_model=PartResponse)
def get_part(part_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404)
    return _part_response(db, part, True)


@router.put("/parts/{part_id}", response_model=PartResponse)
def update_part(part_id: UUID, body: PartUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update", "custom_fields"}, exclude_none=True)
    apply_partial_update(part, data, body.fields_to_update)
    if body.custom_fields:
        set_custom_fields(db, CustomFieldEntity.PART, part.id, body.custom_fields)
    db.commit()
    db.refresh(part)
    return _part_response(db, part, True)


@router.put("/parts/{part_id}/adjust-quantity")
def adjust_quantity(part_id: UUID, body: PartAdjustRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER, UserRole.TECHNICIAN))):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404)
    part.quantity_on_hand += body.quantity_delta
    adj = PartAdjustment(
        part_id=part_id,
        quantity_delta=body.quantity_delta,
        total_after=part.quantity_on_hand,
        reason=body.reason,
        employee_id=body.employee_id,
    )
    db.add(adj)
    db.commit()
    return {"quantity_on_hand": part.quantity_on_hand}


@router.get("/parts/{part_id}/history")
def part_history(part_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(PartAdjustment).filter(PartAdjustment.part_id == part_id).order_by(PartAdjustment.created_at.desc()).all()


@router.post("/parts/{part_id}/assets")
def link_part_asset(part_id: UUID, asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    link = PartAssetLink(part_id=part_id, asset_id=asset_id)
    db.add(link)
    db.commit()
    return {"linked": True}


@router.delete("/parts/{part_id}")
def delete_part(part_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    part = db.query(Part).filter(Part.id == part_id, Part.deleted_at.is_(None)).first()
    if not part:
        raise HTTPException(status_code=404)
    part.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
def create_purchase_order(body: PurchaseOrderCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    data = body.model_dump(exclude={"lines"})
    now = utcnow()
    if not data.get("date_originated"):
        data["date_originated"] = now
    po = PurchaseOrder(number=next_number(db, PurchaseOrder, body.site_id, "PO"), created_by=user.email, **data)
    db.add(po)
    db.flush()
    lines: list[PurchaseOrderLine] = []
    for line in body.lines:
        row = PurchaseOrderLine(purchase_order_id=po.id, **line.model_dump())
        db.add(row)
        lines.append(row)
    recalculate_purchase_order_totals(po, lines)
    db.commit()
    db.refresh(po)
    return serialize_purchase_order(db, po)


@router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    status: PurchaseOrderStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(PurchaseOrder).filter(PurchaseOrder.deleted_at.is_(None))
    if site_id:
        q = q.filter(PurchaseOrder.site_id == site_id)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    q = apply_search(q, search, PurchaseOrder.number, PurchaseOrder.name, PurchaseOrder.notes, PurchaseOrder.account_no)
    pos = q.order_by(PurchaseOrder.created_at.desc()).all()
    return [serialize_purchase_order(db, po, include_lines=False) for po in pos]


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.deleted_at.is_(None)).first()
    if not po:
        raise HTTPException(status_code=404)
    return serialize_purchase_order(db, po)


@router.put("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(po_id: UUID, body: PurchaseOrderUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.deleted_at.is_(None)).first()
    if not po:
        raise HTTPException(status_code=404)
    data = body.model_dump(exclude={"fields_to_update"}, exclude_none=True)
    apply_partial_update(po, data, body.fields_to_update)
    po.last_modified_by = user.email
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po_id).all()
    recalculate_purchase_order_totals(po, lines)
    db.commit()
    db.refresh(po)
    return serialize_purchase_order(db, po)


@router.put("/purchase-orders/{po_id}/receive")
def receive_purchase_order(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404)
    lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po_id).all()
    now = utcnow()
    for line in lines:
        remaining = line.quantity - line.quantity_received
        if remaining > 0:
            part = db.query(Part).filter(Part.id == line.part_id).first()
            if part:
                part.quantity_on_hand += remaining
                db.add(PartAdjustment(part_id=part.id, quantity_delta=remaining, total_after=part.quantity_on_hand, reason=f"PO {po.number} receipt"))
            line.quantity_received = line.quantity
    po.status = PurchaseOrderStatus.RECEIVED
    po.date_received = now
    po.date_completed = now
    po.last_modified_by = user.email
    recalculate_purchase_order_totals(po, lines)
    db.commit()
    return {"received": True}


@router.delete("/purchase-orders/{po_id}")
def delete_purchase_order(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.deleted_at.is_(None)).first()
    if not po:
        raise HTTPException(status_code=404)
    po.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}
