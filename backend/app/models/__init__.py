import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, default=1)


# --- Enums ---


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PLANNER = "PLANNER"
    TECHNICIAN = "TECHNICIAN"
    REQUESTER = "REQUESTER"
    VENDOR = "VENDOR"


class WorkOrderType(str, enum.Enum):
    CORRECTIVE = "CORRECTIVE"
    PREVENTIVE = "PREVENTIVE"
    GENERAL = "GENERAL"


class WorkOrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_PARTS = "WAITING_PARTS"
    WAITING_CONTRACTOR = "WAITING_CONTRACTOR"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ServiceRequestStatus(str, enum.Enum):
    OPEN = "OPEN"
    FOR_REVIEW = "FOR_REVIEW"
    CLOSED = "CLOSED"
    DECLINED = "DECLINED"


class ScheduleType(str, enum.Enum):
    TIME = "TIME"
    METER = "METER"
    BOTH = "BOTH"


class PersonnelType(str, enum.Enum):
    STAFF = "STAFF"
    CONTRACTOR = "CONTRACTOR"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class CustomFieldEntity(str, enum.Enum):
    ASSET = "ASSET"
    WORK_ORDER = "WORK_ORDER"
    PART = "PART"
    USER = "USER"
    SERVICE_REQUEST = "SERVICE_REQUEST"


class CustomFieldDataType(str, enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    SELECT = "SELECT"


class WebhookEvent(str, enum.Enum):
    ASSET_CREATED = "ASSET_CREATED"
    ASSET_STATUS_CHANGED = "ASSET_STATUS_CHANGED"
    ASSET_LOCATION_CHANGED = "ASSET_LOCATION_CHANGED"
    WORK_ORDER_CREATED = "WORK_ORDER_CREATED"
    WORK_ORDER_PROGRESS = "WORK_ORDER_PROGRESS"
    SERVICE_REQUEST_CREATED = "SERVICE_REQUEST_CREATED"
    SERVICE_REQUEST_UPDATED = "SERVICE_REQUEST_UPDATED"


class AttachmentEntity(str, enum.Enum):
    ASSET = "ASSET"
    WORK_ORDER = "WORK_ORDER"
    PART = "PART"
    SERVICE_REQUEST = "SERVICE_REQUEST"


class AttachmentKind(str, enum.Enum):
    PHOTO = "PHOTO"
    DOCUMENT = "DOCUMENT"


# --- 1. Organization & hierarchy ---


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    address1: Mapped[str | None] = mapped_column(String(255))
    address2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    zip_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(100))
    contact: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    fax: Mapped[str | None] = mapped_column(String(50))
    division_name: Mapped[str | None] = mapped_column(String(255))

    sites: Mapped[list["Site"]] = relationship(back_populates="organization")


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    organization: Mapped["Organization"] = relationship(back_populates="sites")
    locations: Mapped[list["Location"]] = relationship(back_populates="site")


class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    criticality: Mapped[str | None] = mapped_column(String(50))

    site: Mapped["Site"] = relationship(back_populates="locations")
    parent: Mapped["Location | None"] = relationship(remote_side="Location.id")


class CostCenter(Base, TimestampMixin):
    __tablename__ = "cost_centers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    color_code: Mapped[str | None] = mapped_column(String(20))
    created_by: Mapped[str | None] = mapped_column(String(255))
    last_modified_by: Mapped[str | None] = mapped_column(String(255))


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")


class BudgetYear(Base, TimestampMixin):
    __tablename__ = "budget_years"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budget_years.id"), nullable=False)
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cost_centers.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0)
    spent: Mapped[float] = mapped_column(Float, default=0)


# --- 8. Reference data ---


class LookupType(Base, TimestampMixin):
    __tablename__ = "lookup_types"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    values: Mapped[list["LookupValue"]] = relationship(back_populates="lookup_type")


class LookupValue(Base, TimestampMixin):
    __tablename__ = "lookup_values"
    __table_args__ = (UniqueConstraint("lookup_type_id", "code"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lookup_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lookup_types.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    lookup_type: Mapped["LookupType"] = relationship(back_populates="values")


# --- 7. People & security ---


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.TECHNICIAN)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    personnel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("personnel.id"), nullable=True)


class SecurityGroup(Base, TimestampMixin):
    __tablename__ = "security_groups"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Personnel(Base, TimestampMixin):
    __tablename__ = "personnel"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    personnel_type: Mapped[PersonnelType] = mapped_column(Enum(PersonnelType), default=PersonnelType.STAFF)
    employee_id: Mapped[str | None] = mapped_column(String(50))
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    craft: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    shift: Mapped[str | None] = mapped_column(String(50))
    hourly_rate: Mapped[float | None] = mapped_column(Float)
    allow_login: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    address: Mapped[str | None] = mapped_column(String(255))
    address2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    zip_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(100))
    home_phone: Mapped[str | None] = mapped_column(String(50))
    work_phone_ext: Mapped[str | None] = mapped_column(String(50))
    date_hired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retire_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer: Mapped[bool] = mapped_column(Boolean, default=False)
    job_title: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    crew: Mapped[str | None] = mapped_column(String(100))
    specialty: Mapped[str | None] = mapped_column(String(100))
    lead_time: Mapped[int | None] = mapped_column(Integer)
    license_type: Mapped[str | None] = mapped_column(String(100))
    salary: Mapped[float | None] = mapped_column(Float)
    salary_overtime: Mapped[float | None] = mapped_column(Float)

    trainings: Mapped[list["Training"]] = relationship(back_populates="personnel")


class Training(Base, TimestampMixin):
    __tablename__ = "trainings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personnel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("personnel.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    certification: Mapped[str | None] = mapped_column(String(255))
    cert_type: Mapped[str | None] = mapped_column(String(100))
    cert_term: Mapped[int | None] = mapped_column(Integer)
    cert_term_uom: Mapped[str | None] = mapped_column(String(50))
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cost: Mapped[float | None] = mapped_column(Float)
    comments: Mapped[str | None] = mapped_column(Text)

    personnel: Mapped["Personnel"] = relationship(back_populates="trainings")


class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    scopes: Mapped[list | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# --- Custom fields ---


class CustomFieldDefinition(Base, TimestampMixin):
    __tablename__ = "custom_field_definitions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    entity_type: Mapped[CustomFieldEntity] = mapped_column(Enum(CustomFieldEntity), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[CustomFieldDataType] = mapped_column(Enum(CustomFieldDataType), nullable=False)
    options: Mapped[list | None] = mapped_column(JSON)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    visibility_rules: Mapped[dict | None] = mapped_column(JSON)


class CustomFieldValue(Base, TimestampMixin):
    __tablename__ = "custom_field_values"
    __table_args__ = (UniqueConstraint("definition_id", "entity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    definition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("custom_field_definitions.id"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    value: Mapped[str | None] = mapped_column(Text)


# --- 2. Asset registry ---


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    supplier_code: Mapped[str | None] = mapped_column(String(50))
    contact: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(255))


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    asset_no: Mapped[str | None] = mapped_column(String(50))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    manufacturer_no: Mapped[str | None] = mapped_column(String(50))
    bar_code: Mapped[str | None] = mapped_column(String(100))
    rfid: Mapped[str | None] = mapped_column(String(100))
    tag_number: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    sub_category: Mapped[str | None] = mapped_column(String(100))
    sub_category_no: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    substatus: Mapped[str | None] = mapped_column(String(50))
    asset_status_category: Mapped[int | None] = mapped_column(Integer)
    asset_condition_no: Mapped[str | None] = mapped_column(String(50))
    asset_condition_name: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[str | None] = mapped_column(String(50))
    criticality: Mapped[str | None] = mapped_column(String(50))
    criticality_weight: Mapped[float | None] = mapped_column(Float)
    cost: Mapped[float | None] = mapped_column(Float)
    replacement_cost: Mapped[float | None] = mapped_column(Float)
    salvage_value: Mapped[float | None] = mapped_column(Float)
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invoice_no: Mapped[str | None] = mapped_column(String(100))
    invoice_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purchase_note: Mapped[str | None] = mapped_column(Text)
    equipment_life: Mapped[float | None] = mapped_column(Float)
    warranty_expiration_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    warranty_title: Mapped[str | None] = mapped_column(String(255))
    warranty_note: Mapped[str | None] = mapped_column(Text)
    service_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retirement_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retirement_reason: Mapped[str | None] = mapped_column(String(255))
    manufacture_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    out_of_service_begin_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    out_of_service_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    placed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    condition_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_replacement_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_out_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    storage_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    location_path: Mapped[str | None] = mapped_column(String(500))
    location_replacement_value: Mapped[float | None] = mapped_column(Float)
    path: Mapped[str | None] = mapped_column(String(500))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cost_centers.id"))
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("suppliers.id"))
    warranty_vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("suppliers.id"))
    parent_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"))
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    is_retired: Mapped[bool] = mapped_column(Boolean, default=False)
    is_auto_generate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_update_medium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tool_crib: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_referenced: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    assessment_note: Mapped[str | None] = mapped_column(Text)
    tool_crib_note: Mapped[str | None] = mapped_column(Text)
    emergency_note: Mapped[str | None] = mapped_column(Text)
    safety_note: Mapped[str | None] = mapped_column(Text)
    training_note: Mapped[str | None] = mapped_column(Text)
    shutdown_procedure: Mapped[str | None] = mapped_column(Text)
    loto_procedure: Mapped[str | None] = mapped_column(Text)
    hyperlink: Mapped[str | None] = mapped_column(String(500))
    region_name: Mapped[str | None] = mapped_column(String(255))
    region_no: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    medium_ids: Mapped[str | None] = mapped_column(String(500))
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    total_hours: Mapped[float] = mapped_column(Float, default=0)
    total_downtime: Mapped[float] = mapped_column(Float, default=0)
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    measurement_unit_id: Mapped[int | None] = mapped_column(Integer)
    uom_cost: Mapped[float | None] = mapped_column(Float)
    uom_quantity: Mapped[float | None] = mapped_column(Float)
    regional_index: Mapped[int | None] = mapped_column(Integer)
    gis_layer_id: Mapped[int | None] = mapped_column(Integer)
    gis_layer_name: Mapped[str | None] = mapped_column(String(255))
    gis_global_id: Mapped[str | None] = mapped_column(String(36))
    global_id: Mapped[str | None] = mapped_column(String(36))
    platform_layer_id: Mapped[str | None] = mapped_column(String(100))
    system_name: Mapped[str | None] = mapped_column(String(255))
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    created_by: Mapped[str | None] = mapped_column(String(255))
    last_modified_by: Mapped[str | None] = mapped_column(String(255))
    security_group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("security_groups.id"))
    fs_type: Mapped[str | None] = mapped_column(String(100))
    nist: Mapped[str | None] = mapped_column(String(50))
    ref_standard: Mapped[bool] = mapped_column(Boolean, default=False)
    attach_to_event: Mapped[bool] = mapped_column(Boolean, default=False)
    asset_disposition: Mapped[str | None] = mapped_column(String(100))
    user_def1: Mapped[str | None] = mapped_column(String(255))
    user_def2: Mapped[str | None] = mapped_column(String(255))
    user_def3: Mapped[str | None] = mapped_column(String(255))


class AssetRelationship(Base, TimestampMixin):
    __tablename__ = "asset_relationships"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    target_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)


class AssetWarranty(Base, TimestampMixin):
    __tablename__ = "asset_warranties"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terms: Mapped[str | None] = mapped_column(Text)
    warranty_item_name: Mapped[str | None] = mapped_column(String(255))
    account_no: Mapped[str | None] = mapped_column(String(100))
    contact: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    contract_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    invoice: Mapped[str | None] = mapped_column(String(100))
    last_warranty_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_warranty_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    warranty_amount: Mapped[float | None] = mapped_column(Float)
    warranty_frequency: Mapped[int | None] = mapped_column(Integer)
    warranty_frequency_uom: Mapped[str | None] = mapped_column(String(50))
    expired: Mapped[bool] = mapped_column(Boolean, default=False)


class AssetHistory(Base):
    __tablename__ = "asset_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_orders.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[AttachmentEntity] = mapped_column(Enum(AttachmentEntity), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[AttachmentKind] = mapped_column(Enum(AttachmentKind), default=AttachmentKind.DOCUMENT)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


# --- 3. Maintenance planning ---


class TaskLibrary(Base, TimestampMixin):
    __tablename__ = "task_library"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    task_code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    task_type: Mapped[str | None] = mapped_column(String(50))


class AssetTask(Base, TimestampMixin):
    __tablename__ = "asset_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    task_library_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("task_library.id"))
    task_code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    schedule_type: Mapped[ScheduleType] = mapped_column(Enum(ScheduleType), default=ScheduleType.TIME)
    recurrence_pattern: Mapped[dict | None] = mapped_column(JSON)
    meter_frequency: Mapped[float | None] = mapped_column(Float)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_maint_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_meter: Mapped[float | None] = mapped_column(Float)
    done_meter: Mapped[float | None] = mapped_column(Float)
    priority: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    task_id: Mapped[str | None] = mapped_column(String(50))
    task_type: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    user_def1: Mapped[str | None] = mapped_column(String(255))
    user_def2: Mapped[str | None] = mapped_column(String(255))
    shift: Mapped[str | None] = mapped_column(String(50))
    meter_group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("meter_groups.id"))
    hyperlink: Mapped[str | None] = mapped_column(String(500))
    can_detach: Mapped[bool] = mapped_column(Boolean, default=True)


class PMQueueEntry(Base, TimestampMixin):
    __tablename__ = "pm_queue_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asset_tasks.id"), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_meter: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_orders.id"))


class Checklist(Base, TimestampMixin):
    __tablename__ = "checklists"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_orders.id"))
    asset_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("asset_tasks.id"))


class ChecklistTestPoint(Base, TimestampMixin):
    __tablename__ = "checklist_test_points"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checklist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("checklists.id"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    nominal: Mapped[float | None] = mapped_column(Float)
    minimum: Mapped[float | None] = mapped_column(Float)
    maximum: Mapped[float | None] = mapped_column(Float)
    plus_tolerance: Mapped[float | None] = mapped_column(Float)
    minus_tolerance: Mapped[float | None] = mapped_column(Float)
    actual_value: Mapped[float | None] = mapped_column(Float)
    performer_ack: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer_ack: Mapped[bool] = mapped_column(Boolean, default=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)


# --- 4. Work management ---


class ServiceRequest(Base, TimestampMixin):
    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ServiceRequestStatus] = mapped_column(Enum(ServiceRequestStatus), default=ServiceRequestStatus.OPEN)
    requested_by: Mapped[str | None] = mapped_column(String(255))
    requester_email: Mapped[str | None] = mapped_column(String(255))
    requester_phone: Mapped[str | None] = mapped_column(String(50))
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(String(50))
    progress: Mapped[str | None] = mapped_column(String(50))
    asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"))
    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_orders.id"))
    cas_type: Mapped[str | None] = mapped_column(String(100))
    cas_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    done_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkOrder(Base, TimestampMixin):
    __tablename__ = "work_orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[WorkOrderType] = mapped_column(Enum(WorkOrderType), nullable=False)
    status: Mapped[WorkOrderStatus] = mapped_column(Enum(WorkOrderStatus), default=WorkOrderStatus.OPEN)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(String(50))
    asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"))
    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cost_centers.id"))
    service_request_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("service_requests.id"))
    source_asset_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("asset_tasks.id"))
    source_pm_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_orders.id"))
    root_cause: Mapped[str | None] = mapped_column(String(255))
    problem: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(Text)
    date_created: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_completed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    downtime_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    actual_hours: Mapped[float | None] = mapped_column(Float)
    waiting_for_parts: Mapped[bool] = mapped_column(Boolean, default=False)
    waiting_for_contractor: Mapped[bool] = mapped_column(Boolean, default=False)
    waiting_for_shutdown: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(255))
    time_maint_hours: Mapped[float | None] = mapped_column(Float)
    time_maint_done: Mapped[float | None] = mapped_column(Float)
    last_maint_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    wo_notes: Mapped[str | None] = mapped_column(Text)
    entered_by: Mapped[str | None] = mapped_column(String(255))
    print_info: Mapped[str | None] = mapped_column(String(500))
    shift: Mapped[str | None] = mapped_column(String(50))
    job_disposition: Mapped[str | None] = mapped_column(String(100))
    user_def1: Mapped[str | None] = mapped_column(String(255))
    user_def2: Mapped[str | None] = mapped_column(String(255))
    signed: Mapped[bool] = mapped_column(Boolean, default=False)
    printed: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkOrderAssignment(Base, TimestampMixin):
    __tablename__ = "work_order_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_orders.id"), nullable=False)
    personnel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("personnel.id"), nullable=False)
    craft: Mapped[str | None] = mapped_column(String(100))
    shift: Mapped[str | None] = mapped_column(String(50))
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    actual_hours: Mapped[float | None] = mapped_column(Float)
    labor_cost: Mapped[float | None] = mapped_column(Float)


class WorkOrderPartUsage(Base, TimestampMixin):
    __tablename__ = "work_order_part_usages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_orders.id"), nullable=False)
    part_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parts.id"), nullable=False)
    quantity_used: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Float)


class WorkOrderComment(Base):
    __tablename__ = "work_order_comments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_orders.id"), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkOrderTask(Base, TimestampMixin):
    __tablename__ = "work_order_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_orders.id"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


# --- 5. Inventory & procurement ---


class Part(Base, TimestampMixin):
    __tablename__ = "parts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    part_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    reorder_point: Mapped[float] = mapped_column(Float, default=0)
    quantity_on_hand: Mapped[float] = mapped_column(Float, default=0)
    unit_cost: Mapped[float | None] = mapped_column(Float)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    storage_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("suppliers.id"))
    manufacturer_part_number: Mapped[str | None] = mapped_column(String(100))
    cost_from_mfg: Mapped[float | None] = mapped_column(Float)
    max_quantity: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    sub_category: Mapped[str | None] = mapped_column(String(100))
    substatus: Mapped[str | None] = mapped_column(String(50))
    look_ahead: Mapped[str | None] = mapped_column(String(50))
    part_user1: Mapped[str | None] = mapped_column(String(255))
    part_user2: Mapped[str | None] = mapped_column(String(255))
    quantity_on_order: Mapped[float] = mapped_column(Float, default=0)
    quantity_on_back_order: Mapped[float] = mapped_column(Float, default=0)


class PartAdjustment(Base):
    __tablename__ = "part_adjustments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parts.id"), nullable=False)
    quantity_delta: Mapped[float] = mapped_column(Float, nullable=False)
    total_after: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    employee_id: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PartAssetLink(Base):
    __tablename__ = "part_asset_links"
    __table_args__ = (UniqueConstraint("part_id", "asset_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parts.id"), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)
    account_no: Mapped[str | None] = mapped_column(String(100))
    created_by: Mapped[str | None] = mapped_column(String(255))
    last_modified_by: Mapped[str | None] = mapped_column(String(255))
    date_submitted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_received: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_completed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_expected: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_originated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_tax: Mapped[float] = mapped_column(Float, default=0)
    total_shipping: Mapped[float] = mapped_column(Float, default=0)
    total_other: Mapped[float] = mapped_column(Float, default=0)
    billing_name: Mapped[str | None] = mapped_column(String(255))
    billing_addr1: Mapped[str | None] = mapped_column(String(255))
    billing_addr2: Mapped[str | None] = mapped_column(String(255))
    billing_city: Mapped[str | None] = mapped_column(String(100))
    billing_state_province: Mapped[str | None] = mapped_column(String(100))
    billing_postal_code: Mapped[str | None] = mapped_column(String(20))
    billing_country_code: Mapped[str | None] = mapped_column(String(10))
    shipping_name: Mapped[str | None] = mapped_column(String(255))
    shipping_addr1: Mapped[str | None] = mapped_column(String(255))
    shipping_addr2: Mapped[str | None] = mapped_column(String(255))
    shipping_city: Mapped[str | None] = mapped_column(String(100))
    shipping_state_province: Mapped[str | None] = mapped_column(String(100))
    shipping_postal_code: Mapped[str | None] = mapped_column(String(20))
    shipping_country_code: Mapped[str | None] = mapped_column(String(10))
    name_format: Mapped[str | None] = mapped_column(String(100))
    total_part_amount: Mapped[float] = mapped_column(Float, default=0)
    total_item_amount: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    grand_total: Mapped[float] = mapped_column(Float, default=0)
    received_total: Mapped[float] = mapped_column(Float, default=0)
    last_signed_by: Mapped[str | None] = mapped_column(String(255))
    last_signed: Mapped[str | None] = mapped_column(String(255))
    last_signed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    region_id: Mapped[str | None] = mapped_column(String(100))
    region_name: Mapped[str | None] = mapped_column(String(255))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cost_centers.id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"))
    originator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("personnel.id"))
    po_status_category: Mapped[int | None] = mapped_column(Integer)
    last_reminded_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_auto_generate: Mapped[bool] = mapped_column(Boolean, default=False)
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)


class PurchaseOrderLine(Base, TimestampMixin):
    __tablename__ = "purchase_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    part_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parts.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_received: Mapped[float] = mapped_column(Float, default=0)


# --- 6. Meters ---


class MeterGroup(Base, TimestampMixin):
    __tablename__ = "meter_groups"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(50))


class Meter(Base, TimestampMixin):
    __tablename__ = "meters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    meter_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meter_groups.id"), nullable=False)
    asset_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("asset_tasks.id"))
    current_reading: Mapped[float] = mapped_column(Float, default=0)
    rollover_point: Mapped[float | None] = mapped_column(Float)
    rollover_count: Mapped[int] = mapped_column(Integer, default=0)
    rollover_meter: Mapped[str | None] = mapped_column(String(50))
    rollover_frequency: Mapped[str | None] = mapped_column(String(50))


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meters.id"), nullable=False)
    reading: Mapped[float] = mapped_column(Float, nullable=False)
    rollover: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    recorded_by: Mapped[str | None] = mapped_column(String(255))


class MeterHistory(Base):
    __tablename__ = "meter_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meters.id"), nullable=False)
    reading: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- 9. Integration & audit ---


class WebhookSubscription(Base, TimestampMixin):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False)
    event_type: Mapped[WebhookEvent] = mapped_column(Enum(WebhookEvent), nullable=False)
    callback_url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webhook_subscriptions.id"), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    actor_email: Mapped[str | None] = mapped_column(String(255))
    before_state: Mapped[dict | None] = mapped_column(JSON)
    after_state: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
