"""Seed database with demo organization, site, lookups, users, and sample data."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.common.auth import hash_password
from app.common.helpers import next_number, utcnow
from app.database import SessionLocal, engine
from app.models import (
    Asset,
    AssetTask,
    Base,
    CustomFieldDataType,
    CustomFieldDefinition,
    CustomFieldEntity,
    CostCenter,
    Location,
    LookupType,
    LookupValue,
    Meter,
    MeterGroup,
    MeterHistory,
    MeterReading,
    Organization,
    Part,
    Personnel,
    PersonnelType,
    ScheduleType,
    Site,
    Supplier,
    TaskLibrary,
    PMQueueEntry,
    ServiceRequest,
    ServiceRequestStatus,
    User,
    UserRole,
    WorkOrder,
    WorkOrderStatus,
    WorkOrderTask,
    WorkOrderType,
)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Organization).first():
            print("Database already seeded.")
            return

        org = Organization(name="Demo Organization", settings={"currency": "USD"})
        db.add(org)
        db.flush()

        site = Site(organization_id=org.id, code="MAIN", name="Main Campus", timezone="UTC")
        db.add(site)
        db.flush()

        loc = Location(site_id=site.id, number="BLDG-A", name="Building A", criticality="HIGH")
        db.add(loc)
        db.flush()

        cc_facilities = CostCenter(
            site_id=site.id,
            number="CC-100",
            name="Facilities Operations",
            description="General facilities maintenance and operations",
            active=True,
            color_code="#2563eb",
            created_by="admin@eam.demo",
        )
        cc_hvac = CostCenter(
            site_id=site.id,
            number="CC-200",
            name="HVAC Capital",
            description="HVAC equipment and capital projects",
            active=True,
            color_code="#059669",
            created_by="admin@eam.demo",
        )
        db.add_all([cc_facilities, cc_hvac])
        db.flush()

        for code, name, values in [
            ("PRIORITY", "Priority", [("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("CRITICAL", "Critical")]),
            ("WO_STATUS", "Work Order Status", [("OPEN", "Open"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed")]),
            ("ASSET_CATEGORY", "Asset Category", [("HVAC", "HVAC"), ("ELECTRICAL", "Electrical"), ("PLUMBING", "Plumbing")]),
            ("ROOT_CAUSE", "Root Cause", [("WEAR", "Normal Wear"), ("OPERATOR", "Operator Error"), ("DEFECT", "Manufacturing Defect")]),
        ]:
            lt = LookupType(code=code, name=name)
            db.add(lt)
            db.flush()
            for i, (vc, vl) in enumerate(values):
                db.add(LookupValue(lookup_type_id=lt.id, code=vc, label=vl, sort_order=i))

        admin = User(email="admin@eam.demo", hashed_password=hash_password("admin123"), role=UserRole.ADMIN)
        planner = User(email="planner@eam.demo", hashed_password=hash_password("planner123"), role=UserRole.PLANNER)
        tech = User(email="tech@eam.demo", hashed_password=hash_password("tech123"), role=UserRole.TECHNICIAN)
        requester = User(email="requester@eam.demo", hashed_password=hash_password("requester123"), role=UserRole.REQUESTER)
        db.add_all([admin, planner, tech, requester])
        db.flush()

        personnel = Personnel(
            site_id=site.id,
            personnel_type=PersonnelType.STAFF,
            full_name="John Technician",
            email="tech@eam.demo",
            employee_id="EMP001",
            craft="Maintenance",
            department="Facilities",
            hourly_rate=45.0,
            allow_login=True,
        )
        db.add(personnel)
        db.flush()

        cf = CustomFieldDefinition(
            site_id=site.id,
            entity_type=CustomFieldEntity.ASSET,
            name="building_zone",
            label="Building Zone",
            data_type=CustomFieldDataType.STRING,
        )
        db.add(cf)

        supplier = Supplier(site_id=site.id, name="Industrial Supply Co", contact_email="orders@indsupply.demo")
        db.add(supplier)
        db.flush()

        asset = Asset(
            site_id=site.id,
            number="AST-000001",
            name="Chiller Unit #1",
            serial_number="CH-2024-001",
            model="CVHF-500",
            manufacturer="Carrier",
            category="HVAC",
            status="ACTIVE",
            priority="HIGH",
            criticality="CRITICAL",
            cost=125000.0,
            current_location_id=loc.id,
            is_critical=True,
        )
        db.add(asset)
        db.flush()

        task_lib = TaskLibrary(site_id=site.id, task_code="PM-CHILLER", description="Quarterly chiller inspection", estimated_hours=4.0, task_type="PM")
        db.add(task_lib)
        db.flush()

        asset_task = AssetTask(
            asset_id=asset.id,
            task_library_id=task_lib.id,
            task_code="PM-CHILLER",
            description="Quarterly chiller inspection",
            schedule_type=ScheduleType.TIME,
            recurrence_pattern={"interval_days": 90},
            lead_time_days=7,
            due_date=datetime.now(timezone.utc) + timedelta(days=5),
            priority="HIGH",
            estimated_hours=4.0,
        )
        db.add(asset_task)

        part = Part(
            site_id=site.id,
            part_number="FLT-001",
            description="HVAC Filter 20x20",
            manufacturer="FilterCorp",
            reorder_point=10,
            quantity_on_hand=25,
            unit_cost=15.99,
            supplier_id=supplier.id,
        )
        db.add(part)

        hours_group = MeterGroup(site_id=site.id, code="RUN-HRS", name="Run Hours", unit_of_measure="hours")
        cycles_group = MeterGroup(site_id=site.id, code="CYCLES", name="Start Cycles", unit_of_measure="cycles")
        db.add_all([hours_group, cycles_group])
        db.flush()

        meter_hours = Meter(
            asset_id=asset.id,
            meter_group_id=hours_group.id,
            current_reading=4820.0,
            rollover_point=99999.0,
        )
        db.add(meter_hours)
        db.flush()

        db.add(
            MeterReading(
                meter_id=meter_hours.id,
                reading=4820.0,
                rollover=False,
                recorded_by="tech@eam.demo",
            )
        )
        db.add(MeterHistory(meter_id=meter_hours.id, reading=4820.0, delta=4820.0))

        cm_wo = WorkOrder(
            site_id=site.id,
            number=next_number(db, WorkOrder, site.id, "CM"),
            type=WorkOrderType.CORRECTIVE,
            status=WorkOrderStatus.OPEN,
            title="Chiller low refrigerant pressure alarm",
            problem="Operator reported low suction pressure and elevated discharge temperature on chiller unit.",
            priority="HIGH",
            asset_id=asset.id,
            location_id=loc.id,
            date_created=utcnow(),
            created_by="planner@eam.demo",
            waiting_for_parts=False,
        )
        db.add(cm_wo)
        db.flush()

        db.add_all([
            WorkOrderTask(
                work_order_id=cm_wo.id,
                line_number=1,
                description="Verify suction and discharge pressures",
                estimated_hours=0.5,
            ),
            WorkOrderTask(
                work_order_id=cm_wo.id,
                line_number=2,
                description="Inspect refrigerant levels and check for leaks",
                estimated_hours=1.5,
            ),
            WorkOrderTask(
                work_order_id=cm_wo.id,
                line_number=3,
                description="Review chiller alarm history and reset if resolved",
                estimated_hours=0.25,
            ),
        ])

        extra_assets = [
            Asset(site_id=site.id, number="AST-000002", name="Air Handler Unit 2B", category="HVAC", status="ACTIVE", priority="MEDIUM", cost=42000.0, current_location_id=loc.id),
            Asset(site_id=site.id, number="AST-000003", name="Emergency Generator", category="ELECTRICAL", status="ACTIVE", priority="CRITICAL", criticality="CRITICAL", cost=89000.0, current_location_id=loc.id, is_critical=True),
            Asset(site_id=site.id, number="AST-000004", name="Boiler Plant #2", category="HVAC", status="DOWN", priority="HIGH", cost=156000.0, current_location_id=loc.id, is_critical=True),
            Asset(site_id=site.id, number="AST-000005", name="Cooling Tower West", category="HVAC", status="ACTIVE", priority="MEDIUM", cost=67000.0, current_location_id=loc.id),
            Asset(site_id=site.id, number="AST-000006", name="Main Electrical Panel", category="ELECTRICAL", status="ACTIVE", priority="HIGH", cost=34000.0, current_location_id=loc.id),
        ]
        db.add_all(extra_assets)
        db.flush()

        low_part = Part(
            site_id=site.id,
            part_number="BLT-220",
            description="Drive Belt 220V",
            reorder_point=15,
            quantity_on_hand=4,
            unit_cost=42.50,
            supplier_id=supplier.id,
            is_critical=True,
        )
        db.add(low_part)

        db.add(
            ServiceRequest(
                site_id=site.id,
                number="SR-000001",
                status=ServiceRequestStatus.OPEN,
                requested_by="Facilities Manager",
                requester_email="requester@eam.demo",
                problem="Unusual vibration reported on cooling tower fan motor during night shift.",
                priority="HIGH",
                asset_id=extra_assets[3].id,
                location_id=loc.id,
            )
        )
        db.add(
            ServiceRequest(
                site_id=site.id,
                number="SR-000002",
                status=ServiceRequestStatus.OPEN,
                requested_by="Building A Supervisor",
                requester_email="requester@eam.demo",
                problem="Restroom exhaust fan not running on floor 3, east wing.",
                priority="MEDIUM",
                location_id=loc.id,
            )
        )

        db.add(PMQueueEntry(asset_task_id=asset_task.id, due_date=asset_task.due_date, status="PENDING"))

        completed_wos = [
            WorkOrder(
                site_id=site.id,
                number=next_number(db, WorkOrder, site.id, "PM"),
                type=WorkOrderType.PREVENTIVE,
                status=WorkOrderStatus.COMPLETED,
                title="Quarterly chiller inspection",
                priority="HIGH",
                asset_id=asset.id,
                location_id=loc.id,
                date_created=utcnow() - timedelta(days=95),
                date_completed=utcnow() - timedelta(days=92),
                date_due=utcnow() - timedelta(days=90),
                actual_hours=3.5,
            ),
            WorkOrder(
                site_id=site.id,
                number=next_number(db, WorkOrder, site.id, "CM"),
                type=WorkOrderType.CORRECTIVE,
                status=WorkOrderStatus.COMPLETED,
                title="Replace chiller filter media",
                priority="MEDIUM",
                asset_id=asset.id,
                location_id=loc.id,
                date_created=utcnow() - timedelta(days=45),
                date_completed=utcnow() - timedelta(days=42),
                date_due=utcnow() - timedelta(days=40),
                actual_hours=2.0,
            ),
            WorkOrder(
                site_id=site.id,
                number=next_number(db, WorkOrder, site.id, "CM"),
                type=WorkOrderType.CORRECTIVE,
                status=WorkOrderStatus.COMPLETED,
                title="Generator load bank test",
                priority="HIGH",
                asset_id=extra_assets[1].id,
                location_id=loc.id,
                date_created=utcnow() - timedelta(days=18),
                date_completed=utcnow() - timedelta(days=12),
                date_due=utcnow() - timedelta(days=14),
                actual_hours=5.0,
            ),
            WorkOrder(
                site_id=site.id,
                number=next_number(db, WorkOrder, site.id, "CM"),
                type=WorkOrderType.CORRECTIVE,
                status=WorkOrderStatus.COMPLETED,
                title="AHU belt tension adjustment",
                priority="LOW",
                asset_id=extra_assets[0].id,
                location_id=loc.id,
                date_created=utcnow() - timedelta(days=8),
                date_completed=utcnow() - timedelta(days=5),
                actual_hours=1.5,
            ),
        ]
        db.add_all(completed_wos)

        db.add(
            WorkOrder(
                site_id=site.id,
                number=next_number(db, WorkOrder, site.id, "CM"),
                type=WorkOrderType.CORRECTIVE,
                status=WorkOrderStatus.IN_PROGRESS,
                title="Boiler combustion analysis overdue",
                problem="Annual combustion tuning required; unit currently offline.",
                priority="CRITICAL",
                asset_id=extra_assets[2].id,
                location_id=loc.id,
                date_created=utcnow() - timedelta(days=21),
                date_due=utcnow() - timedelta(days=3),
                waiting_for_contractor=True,
            )
        )
        db.add(
            WorkOrder(
                site_id=site.id,
                number=next_number(db, WorkOrder, site.id, "PM"),
                type=WorkOrderType.PREVENTIVE,
                status=WorkOrderStatus.OPEN,
                title="Cooling tower basin cleaning",
                priority="MEDIUM",
                asset_id=extra_assets[3].id,
                location_id=loc.id,
                date_created=utcnow() - timedelta(days=2),
                date_due=utcnow() + timedelta(days=10),
            )
        )

        db.commit()
        print("Seed complete.")
        print("  Admin:     admin@eam.demo / admin123")
        print("  Planner:   planner@eam.demo / planner123")
        print("  Tech:      tech@eam.demo / tech123")
        print("  Requester: requester@eam.demo / requester123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
