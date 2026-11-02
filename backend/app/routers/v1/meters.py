from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.auth import get_current_user, require_roles
from app.database import get_db
from app.models import Asset, AssetTask, Meter, MeterGroup, MeterHistory, MeterReading, User, UserRole
from app.schemas import (
    MeterDetailResponse,
    MeterGroupCreate,
    MeterGroupResponse,
    MeterReadingBatch,
    MeterReadingDetailResponse,
    MeterReadingResponse,
    MeterReadingUpdate,
)
from app.services.pm_queue import evaluate_meter_pm

router = APIRouter(prefix="/v1/meter-readings", tags=["Meters"])


@router.post("/groups", response_model=MeterGroupResponse)
def create_meter_group(body: MeterGroupCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.PLANNER))):
    g = MeterGroup(**body.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("/groups", response_model=list[MeterGroupResponse])
def list_meter_groups(site_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(MeterGroup).filter(MeterGroup.deleted_at.is_(None))
    if site_id:
        q = q.filter(MeterGroup.site_id == site_id)
    return q.order_by(MeterGroup.code).all()


@router.get("/meters", response_model=list[MeterDetailResponse])
def list_meters(site_id: UUID | None = None, asset_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = (
        db.query(Meter, Asset, MeterGroup)
        .join(Asset, Meter.asset_id == Asset.id)
        .join(MeterGroup, Meter.meter_group_id == MeterGroup.id)
        .filter(Asset.deleted_at.is_(None))
    )
    if site_id:
        q = q.filter(Asset.site_id == site_id)
    if asset_id:
        q = q.filter(Meter.asset_id == asset_id)
    rows = q.order_by(Asset.number, MeterGroup.code).all()
    return [
        MeterDetailResponse(
            id=m.id,
            asset_id=m.asset_id,
            meter_group_id=m.meter_group_id,
            current_reading=m.current_reading,
            rollover_count=m.rollover_count,
            rollover_point=m.rollover_point,
            asset_number=a.number,
            asset_name=a.name,
            meter_group_code=g.code,
            meter_group_name=g.name,
            unit_of_measure=g.unit_of_measure,
        )
        for m, a, g in rows
    ]


@router.get("", response_model=list[MeterReadingDetailResponse])
def list_meter_readings(
    site_id: UUID | None = None,
    asset_id: UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = (
        db.query(MeterReading, Meter, Asset, MeterGroup)
        .join(Meter, MeterReading.meter_id == Meter.id)
        .join(Asset, Meter.asset_id == Asset.id)
        .join(MeterGroup, Meter.meter_group_id == MeterGroup.id)
        .filter(Asset.deleted_at.is_(None))
    )
    if site_id:
        q = q.filter(Asset.site_id == site_id)
    if asset_id:
        q = q.filter(Meter.asset_id == asset_id)
    rows = q.order_by(MeterReading.recorded_at.desc()).limit(200).all()
    return [
        MeterReadingDetailResponse(
            id=r.id,
            meter_id=r.meter_id,
            reading=r.reading,
            rollover=r.rollover,
            recorded_at=r.recorded_at,
            recorded_by=r.recorded_by,
            asset_id=a.id,
            asset_number=a.number,
            asset_name=a.name,
            meter_group_id=g.id,
            meter_group_code=g.code,
            meter_group_name=g.name,
            unit_of_measure=g.unit_of_measure,
        )
        for r, m, a, g in rows
    ]


def _record_reading(db: Session, meter: Meter, body: MeterReadingUpdate, recorded_by: str) -> MeterReading:
    prev = meter.current_reading
    delta = body.reading - prev if not body.rollover else body.reading
    if body.rollover:
        meter.rollover_count += 1
    meter.current_reading = body.reading
    reading = MeterReading(meter_id=meter.id, reading=body.reading, rollover=body.rollover, recorded_by=recorded_by)
    history = MeterHistory(meter_id=meter.id, reading=body.reading, delta=delta)
    db.add(reading)
    db.add(history)
    evaluate_meter_pm(db, meter.asset_id, body.reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.put("/{meter_id}", response_model=MeterReadingResponse)
def update_meter_reading(meter_id: UUID, body: MeterReadingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    reading = _record_reading(db, meter, body, user.email)
    return MeterReadingResponse.model_validate(reading)


@router.put("/batch/by-asset", response_model=MeterReadingResponse)
def batch_update_by_asset(body: MeterReadingBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meter = (
        db.query(Meter)
        .filter(Meter.asset_id == body.asset_id, Meter.meter_group_id == body.meter_group_id)
        .first()
    )
    if not meter:
        task = db.query(AssetTask).filter(AssetTask.asset_id == body.asset_id).first()
        meter = Meter(asset_id=body.asset_id, meter_group_id=body.meter_group_id, asset_task_id=task.id if task else None)
        db.add(meter)
        db.flush()
    reading = _record_reading(db, meter, MeterReadingUpdate(reading=body.reading, rollover=body.rollover), user.email)
    return MeterReadingResponse.model_validate(reading)


@router.get("/{meter_id}/history")
def meter_history(meter_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(MeterHistory).filter(MeterHistory.meter_id == meter_id).order_by(MeterHistory.recorded_at.desc()).all()


@router.get("/assets/{asset_id}/meters", response_model=list[MeterDetailResponse])
def list_asset_meters(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = (
        db.query(Meter, Asset, MeterGroup)
        .join(Asset, Meter.asset_id == Asset.id)
        .join(MeterGroup, Meter.meter_group_id == MeterGroup.id)
        .filter(Meter.asset_id == asset_id, Asset.deleted_at.is_(None))
        .order_by(MeterGroup.code)
    )
    rows = q.all()
    return [
        MeterDetailResponse(
            id=m.id,
            asset_id=m.asset_id,
            meter_group_id=m.meter_group_id,
            current_reading=m.current_reading,
            rollover_count=m.rollover_count,
            rollover_point=m.rollover_point,
            asset_number=a.number,
            asset_name=a.name,
            meter_group_code=g.code,
            meter_group_name=g.name,
            unit_of_measure=g.unit_of_measure,
        )
        for m, a, g in rows
    ]
