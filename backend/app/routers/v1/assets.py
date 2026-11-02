import os
import shutil
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.common.audit import log_audit
from app.common.auth import get_current_user, require_roles
from app.common.custom_fields import get_custom_fields, set_custom_fields
from app.common.pagination import apply_partial_update, paginate
from app.common.search import apply_search
from app.common.helpers import next_number, utcnow
from app.config import settings
from app.database import get_db
from app.models import (
    Asset,
    AssetHistory,
    AssetRelationship,
    AssetWarranty,
    Attachment,
    AttachmentEntity,
    AttachmentKind,
    CustomFieldEntity,
    Part,
    PartAssetLink,
    User,
    UserRole,
    WebhookEvent,
)
from app.schemas import (
    AssetCreate,
    AssetRelationshipCreate,
    AssetResponse,
    AssetUpdate,
    AssetWarrantyCreate,
    AssetWarrantyResponse,
    AttachmentResponse,
)
from app.services.asset import serialize_asset
from app.services.webhooks import dispatch_webhook_sync

router = APIRouter(prefix="/v1/assets", tags=["Assets"])

IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml"}


def _asset_response(db: Session, asset: Asset, include_custom: bool) -> AssetResponse:
    custom = get_custom_fields(db, CustomFieldEntity.ASSET, asset.id, asset.site_id) if include_custom else None
    return serialize_asset(db, asset, custom)


def _get_asset_or_404(db: Session, asset_id: UUID) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at.is_(None)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _attachment_response(att: Attachment) -> AttachmentResponse:
    return AttachmentResponse(
        id=att.id,
        entity_type=att.entity_type.value,
        entity_id=att.entity_id,
        file_name=att.file_name,
        content_type=att.content_type,
        file_size=att.file_size,
        kind=att.kind.value,
        is_primary=att.is_primary,
        created_at=att.created_at,
    )


def _infer_kind(content_type: str, requested: str | None) -> AttachmentKind:
    if requested == "photo":
        return AttachmentKind.PHOTO
    if requested == "document":
        return AttachmentKind.DOCUMENT
    if content_type in IMAGE_TYPES:
        return AttachmentKind.PHOTO
    return AttachmentKind.DOCUMENT


def _clear_primary_photos(db: Session, asset_id: UUID) -> None:
    (
        db.query(Attachment)
        .filter(
            Attachment.entity_type == AttachmentEntity.ASSET,
            Attachment.entity_id == asset_id,
            Attachment.kind == AttachmentKind.PHOTO,
        )
        .update({Attachment.is_primary: False})
    )


def _save_upload(file: UploadFile, asset_id: UUID) -> tuple[str, int]:
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    stored_name = f"{asset_id}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.upload_dir, stored_name)
    size = 0
    with open(path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            out.write(chunk)
    return path, size


@router.get("")
def list_assets(
    site_id: UUID | None = None,
    search: str | None = Query(None),
    status: str | None = Query(None),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    custom_fields: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Asset).filter(Asset.deleted_at.is_(None))
    if site_id:
        q = q.filter(Asset.site_id == site_id)
    if status:
        q = q.filter(Asset.status == status)
    if category:
        q = q.filter(Asset.category == category)
    q = apply_search(
        q,
        search,
        Asset.number,
        Asset.name,
        Asset.description,
        Asset.asset_no,
        Asset.category,
        Asset.serial_number,
        Asset.manufacturer,
        Asset.make,
        Asset.model,
        Asset.bar_code,
        Asset.tag_number,
    )
    total = q.count()
    items = q.order_by(Asset.number).offset((page - 1) * page_size).limit(page_size).all()
    return paginate([_asset_response(db, a, custom_fields) for a in items], total, page, page_size)


@router.post("", response_model=AssetResponse)
def create_asset(body: AssetCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    asset = Asset(created_by=user.email, **body.model_dump(exclude={"custom_fields"}))
    db.add(asset)
    db.flush()
    if body.custom_fields:
        set_custom_fields(db, CustomFieldEntity.ASSET, asset.id, body.custom_fields, asset.site_id)
    log_audit(db, entity_type="Asset", entity_id=asset.id, action="CREATE", actor_id=user.id, actor_email=user.email, after={"number": asset.number})
    db.commit()
    db.refresh(asset)
    dispatch_webhook_sync(db, asset.site_id, WebhookEvent.ASSET_CREATED, {"id": str(asset.id), "number": asset.number})
    return _asset_response(db, asset, True)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: UUID, custom_fields: bool = Query(True), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = _get_asset_or_404(db, asset_id)
    return _asset_response(db, asset, custom_fields)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: UUID, body: AssetUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER, UserRole.TECHNICIAN))):
    asset = _get_asset_or_404(db, asset_id)
    old_status = asset.status
    data = body.model_dump(exclude={"fields_to_update", "custom_fields"}, exclude_none=True)
    apply_partial_update(asset, data, body.fields_to_update)
    asset.last_modified_by = user.email
    if body.custom_fields:
        set_custom_fields(db, CustomFieldEntity.ASSET, asset.id, body.custom_fields, asset.site_id)
    if body.status and body.status != old_status:
        dispatch_webhook_sync(db, asset.site_id, WebhookEvent.ASSET_STATUS_CHANGED, {"id": str(asset.id), "status": asset.status})
    if body.current_location_id:
        dispatch_webhook_sync(db, asset.site_id, WebhookEvent.ASSET_LOCATION_CHANGED, {"id": str(asset.id), "location_id": str(asset.current_location_id)})
    db.commit()
    db.refresh(asset)
    return _asset_response(db, asset, True)


@router.delete("/{asset_id}")
def delete_asset(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN))):
    asset = _get_asset_or_404(db, asset_id)
    asset.deleted_at = utcnow()
    db.commit()
    return {"deleted": True}


@router.post("/{asset_id}/relationships")
def add_relationship(asset_id: UUID, body: AssetRelationshipCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rel = AssetRelationship(source_asset_id=asset_id, **body.model_dump())
    db.add(rel)
    db.commit()
    return {"id": str(rel.id)}


@router.get("/{asset_id}/relationships")
def list_relationships(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(AssetRelationship).filter(AssetRelationship.source_asset_id == asset_id).all()


@router.post("/{asset_id}/warranties", response_model=AssetWarrantyResponse)
def add_warranty(asset_id: UUID, body: AssetWarrantyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    w = AssetWarranty(asset_id=asset_id, **body.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@router.get("/{asset_id}/warranties", response_model=list[AssetWarrantyResponse])
def list_warranties(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(AssetWarranty).filter(AssetWarranty.asset_id == asset_id).all()


@router.get("/{asset_id}/history")
def list_history(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(AssetHistory).filter(AssetHistory.asset_id == asset_id).order_by(AssetHistory.occurred_at.desc()).all()


@router.post("/{asset_id}/attachments", response_model=list[AttachmentResponse])
async def upload_attachments(
    asset_id: UUID,
    files: list[UploadFile] = File(...),
    kind: str | None = Query(None, description="photo or document"),
    set_primary: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_asset_or_404(db, asset_id)
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    created: list[AttachmentResponse] = []
    has_primary = (
        db.query(Attachment)
        .filter(
            Attachment.entity_type == AttachmentEntity.ASSET,
            Attachment.entity_id == asset_id,
            Attachment.kind == AttachmentKind.PHOTO,
            Attachment.is_primary.is_(True),
        )
        .count()
        > 0
    )

    for index, file in enumerate(files):
        content_type = file.content_type or "application/octet-stream"
        file_kind = _infer_kind(content_type, kind)
        path, size = _save_upload(file, asset_id)

        make_primary = False
        if file_kind == AttachmentKind.PHOTO and (set_primary and index == 0 or not has_primary):
            _clear_primary_photos(db, asset_id)
            make_primary = True
            has_primary = True

        att = Attachment(
            entity_type=AttachmentEntity.ASSET,
            entity_id=asset_id,
            file_name=file.filename or "upload",
            content_type=content_type,
            file_path=path,
            file_size=size,
            kind=file_kind,
            is_primary=make_primary,
            uploaded_by=user.id,
        )
        db.add(att)
        db.flush()
        created.append(_attachment_response(att))

    db.commit()
    return created


@router.get("/{asset_id}/attachments", response_model=list[AttachmentResponse])
def list_attachments(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_asset_or_404(db, asset_id)
    rows = (
        db.query(Attachment)
        .filter(Attachment.entity_type == AttachmentEntity.ASSET, Attachment.entity_id == asset_id)
        .order_by(Attachment.is_primary.desc(), Attachment.created_at.desc())
        .all()
    )
    return [_attachment_response(a) for a in rows]


@router.get("/attachments/{attachment_id}/file")
def download_attachment(attachment_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if not os.path.isfile(att.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(att.file_path, media_type=att.content_type, filename=att.file_name)


@router.put("/attachments/{attachment_id}/primary", response_model=AttachmentResponse)
def set_primary_photo(attachment_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not att or att.entity_type != AttachmentEntity.ASSET:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if att.kind != AttachmentKind.PHOTO:
        raise HTTPException(status_code=400, detail="Only photos can be set as primary")
    _clear_primary_photos(db, att.entity_id)
    att.is_primary = True
    db.commit()
    db.refresh(att)
    return _attachment_response(att)


@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER, UserRole.TECHNICIAN))):
    att = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not att or att.entity_type != AttachmentEntity.ASSET:
        raise HTTPException(status_code=404, detail="Attachment not found")
    was_primary = att.is_primary
    asset_id = att.entity_id
    if os.path.isfile(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.flush()
    if was_primary:
        next_photo = (
            db.query(Attachment)
            .filter(
                Attachment.entity_type == AttachmentEntity.ASSET,
                Attachment.entity_id == asset_id,
                Attachment.kind == AttachmentKind.PHOTO,
            )
            .order_by(Attachment.created_at.desc())
            .first()
        )
        if next_photo:
            next_photo.is_primary = True
    db.commit()
    return {"deleted": True}


@router.get("/{asset_id}/parts")
def list_asset_parts(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    links = db.query(PartAssetLink).filter(PartAssetLink.asset_id == asset_id).all()
    part_ids = [l.part_id for l in links]
    return db.query(Part).filter(Part.id.in_(part_ids)).all() if part_ids else []
