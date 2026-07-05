from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.common.pagination import ORMModel, PartialUpdateMixin
from app.schemas.faciliworks_fields import (
    AssetFields,
    AssetTaskFields,
    AssetWarrantyFields,
    PartFields,
    PersonnelFields,
    ServiceRequestFields,
    SupplierFields,
    TrainingFields,
    WorkOrderFields,
    PurchaseOrderFields,
)
from app.models import (
    CustomFieldDataType,
    CustomFieldEntity,
    PersonnelType,
    PurchaseOrderStatus,
    ScheduleType,
    ServiceRequestStatus,
    UserRole,
    WebhookEvent,
    WorkOrderStatus,
    WorkOrderType,
)


# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(ORMModel):
    id: UUID
    email: str
    role: UserRole
    is_active: bool


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] | None = None


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    raw_key: str | None = None


# Organization
class OrganizationCreate(BaseModel):
    name: str
    settings: dict | None = None


class OrganizationResponse(ORMModel):
    id: UUID
    name: str
    settings: dict | None = None


class SiteCreate(BaseModel):
    organization_id: UUID
    code: str
    name: str
    address: str | None = None
    timezone: str = "UTC"


class SiteResponse(ORMModel):
    id: UUID
    organization_id: UUID
    code: str
    name: str
    address: str | None
    timezone: str


class SiteUpdate(PartialUpdateMixin):
    code: str | None = None
    name: str | None = None
    address: str | None = None
    timezone: str | None = None


class LocationCreate(BaseModel):
    site_id: UUID
    parent_id: UUID | None = None
    number: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    criticality: str | None = None


class LocationResponse(ORMModel):
    id: UUID
    site_id: UUID
    parent_id: UUID | None
    number: str
    name: str
    latitude: float | None
    longitude: float | None
    criticality: str | None


class LocationUpdate(PartialUpdateMixin):
    parent_id: UUID | None = None
    number: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    criticality: str | None = None


class CostCenterCreate(BaseModel):
    site_id: UUID
    number: str
    name: str
    description: str | None = None
    active: bool = True
    color_code: str | None = None


class CostCenterUpdate(PartialUpdateMixin, BaseModel):
    number: str | None = None
    name: str | None = None
    description: str | None = None
    active: bool | None = None
    color_code: str | None = None


class CostCenterResponse(ORMModel):
    id: UUID
    site_id: UUID
    number: str
    name: str
    description: str | None = None
    active: bool
    color_code: str | None = None
    created_by: str | None = None
    last_modified_by: str | None = None
    created_at: datetime
    updated_at: datetime
    row_version: int
    site_no: str | None = None
    site_name: str | None = None


class ProjectCreate(BaseModel):
    site_id: UUID
    number: str
    name: str
    description: str | None = None
    status: str = "ACTIVE"


class ProjectResponse(ORMModel):
    id: UUID
    site_id: UUID
    number: str
    name: str
    description: str | None
    status: str


class BudgetYearCreate(BaseModel):
    site_id: UUID
    year: int
    name: str


class BudgetCreate(BaseModel):
    budget_year_id: UUID
    cost_center_id: UUID | None = None
    name: str
    amount: float = 0


class BudgetResponse(ORMModel):
    id: UUID
    budget_year_id: UUID
    cost_center_id: UUID | None
    name: str
    amount: float
    spent: float


# Lookups
class LookupValueCreate(BaseModel):
    code: str
    label: str
    sort_order: int = 0


class LookupValueUpdate(BaseModel):
    code: str | None = None
    label: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class LookupValueResponse(ORMModel):
    id: UUID
    code: str
    label: str
    sort_order: int
    is_active: bool


class LookupTypeResponse(ORMModel):
    id: UUID
    code: str
    name: str
    values: list[LookupValueResponse] = []


class LookupTypeUpdate(BaseModel):
    name: str | None = None


# Assets
class AssetCreate(AssetFields):
    site_id: UUID
    number: str
    name: str
    custom_fields: dict[str, object] | None = None


class AssetUpdate(PartialUpdateMixin, AssetFields):
    name: str | None = None
    status: str | None = None
    is_critical: bool | None = None
    is_auto_generate: bool | None = None
    is_update_medium: bool | None = None
    is_tool_crib: bool | None = None
    is_system: bool | None = None
    is_referenced: bool | None = None
    ref_standard: bool | None = None
    attach_to_event: bool | None = None
    is_retired: bool | None = None
    custom_fields: dict[str, object] | None = None


class AssetResponse(ORMModel, AssetFields):
    id: UUID
    site_id: UUID
    number: str
    name: str
    is_retired: bool
    created_by: str | None = None
    last_modified_by: str | None = None
    created_at: datetime
    updated_at: datetime
    row_version: int
    custom_fields: dict | None = None
    site_no: str | None = None
    site_name: str | None = None
    category_no: str | None = None
    category_name: str | None = None
    cost_center_no: str | None = None
    cost_center_name: str | None = None
    location_no: str | None = None
    location_name: str | None = None
    location_path: str | None = None
    asset_status_name: str | None = None
    asset_status_no: str | None = None
    criticality_no: str | None = None
    criticality_name: str | None = None
    supplier_no: str | None = None
    supplier_name: str | None = None
    warranty_vendor_no: str | None = None
    warranty_vendor_name: str | None = None
    parent_asset_name: str | None = None
    manufacturer_name: str | None = None
    sub_category_name: str | None = None
    photo_name: str | None = None
    photo_url: str | None = None


class AssetRelationshipCreate(BaseModel):
    target_asset_id: UUID
    relationship_type: str


class AssetWarrantyCreate(AssetWarrantyFields):
    pass


class AssetWarrantyResponse(ORMModel, AssetWarrantyFields):
    id: UUID
    asset_id: UUID


class AttachmentResponse(ORMModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    file_name: str
    content_type: str
    file_size: int
    kind: str
    is_primary: bool
    created_at: datetime


# Work orders
class WorkOrderCreate(WorkOrderFields):
    site_id: UUID
    type: WorkOrderType
    title: str
    custom_fields: dict[str, object] | None = None


class WorkOrderUpdate(PartialUpdateMixin, WorkOrderFields):
    title: str | None = None
    status: WorkOrderStatus | None = None
    waiting_for_parts: bool | None = None
    waiting_for_contractor: bool | None = None
    waiting_for_shutdown: bool | None = None
    signed: bool | None = None
    printed: bool | None = None
    custom_fields: dict[str, object] | None = None


class WorkOrderResponse(ORMModel, WorkOrderFields):
    id: UUID
    site_id: UUID
    number: str
    type: WorkOrderType
    status: WorkOrderStatus
    title: str
    date_completed: datetime | None
    row_version: int
    custom_fields: dict | None = None


class WorkOrderSearch(BaseModel):
    status: WorkOrderStatus | None = None
    type: WorkOrderType | None = None
    asset_id: UUID | None = None
    priority: str | None = None
    page: int = 1
    page_size: int = 20


class WorkOrderAssignmentCreate(BaseModel):
    personnel_id: UUID
    craft: str | None = None
    estimated_hours: float | None = None


class WorkOrderPartUsageCreate(BaseModel):
    part_id: UUID
    quantity_used: float
    unit_cost: float | None = None


class WorkOrderCommentCreate(BaseModel):
    body: str


class WorkOrderCommentResponse(ORMModel):
    id: UUID
    author: str
    body: str
    created_at: datetime


class WorkOrderTaskCreate(BaseModel):
    description: str
    estimated_hours: float | None = None
    line_number: int | None = None
    notes: str | None = None


class WorkOrderTaskUpdate(BaseModel):
    description: str | None = None
    estimated_hours: float | None = None
    line_number: int | None = None
    status: str | None = None
    notes: str | None = None


class WorkOrderTaskResponse(ORMModel):
    id: UUID
    work_order_id: UUID
    line_number: int
    description: str
    estimated_hours: float | None = None
    status: str
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# Service requests
class ServiceRequestCreate(ServiceRequestFields):
    site_id: UUID
    problem: str


class ServiceRequestUpdate(PartialUpdateMixin, ServiceRequestFields):
    problem: str | None = None
    progress: str | None = None
    status: ServiceRequestStatus | None = None


class ServiceRequestResponse(ORMModel, ServiceRequestFields):
    id: UUID
    site_id: UUID
    number: str
    status: ServiceRequestStatus
    problem: str
    work_order_id: UUID | None


# PM
class TaskLibraryCreate(BaseModel):
    site_id: UUID
    task_code: str
    description: str
    estimated_hours: float | None = None
    task_type: str | None = None


class TaskLibraryUpdate(PartialUpdateMixin):
    description: str | None = None
    estimated_hours: float | None = None
    task_type: str | None = None


class AssetTaskCreate(AssetTaskFields):
    asset_id: UUID


class AssetTaskResponse(ORMModel, AssetTaskFields):
    id: UUID
    asset_id: UUID
    status: str
    is_active: bool


class AssetTaskUpdate(PartialUpdateMixin, AssetTaskFields):
    task_code: str | None = None
    description: str | None = None
    schedule_type: ScheduleType | None = None
    lead_time_days: int | None = None
    status: str | None = None
    is_active: bool | None = None
    can_detach: bool | None = None


class ChecklistCreate(BaseModel):
    name: str
    description: str | None = None


class ChecklistTestPointCreate(BaseModel):
    name: str
    description: str | None = None
    nominal: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    line_number: int = 1


class ChecklistTestPointUpdate(BaseModel):
    actual_value: float | None = None
    performer_ack: bool | None = None
    reviewer_ack: bool | None = None
    is_complete: bool | None = None


class PMQueueGenerate(BaseModel):
    lead_time_days: int = 0


# Parts
class PartCreate(PartFields):
    site_id: UUID
    part_number: str
    description: str
    custom_fields: dict[str, object] | None = None


class PartUpdate(PartialUpdateMixin, PartFields):
    description: str | None = None
    is_critical: bool | None = None
    custom_fields: dict[str, object] | None = None


class PartResponse(ORMModel, PartFields):
    id: UUID
    site_id: UUID
    part_number: str
    description: str
    custom_fields: dict | None = None


class PartAdjustRequest(BaseModel):
    quantity_delta: float
    reason: str | None = None
    employee_id: str | None = None


class SupplierCreate(SupplierFields):
    site_id: UUID
    name: str


class SupplierResponse(ORMModel, SupplierFields):
    id: UUID
    site_id: UUID
    name: str


class SupplierUpdate(PartialUpdateMixin, SupplierFields):
    name: str | None = None


class PurchaseOrderLineCreate(BaseModel):
    part_id: UUID
    quantity: float
    unit_price: float


class PurchaseOrderLineResponse(ORMModel):
    id: UUID
    part_id: UUID
    quantity: float
    unit_price: float
    quantity_received: float
    part_number: str | None = None
    part_description: str | None = None


class PurchaseOrderCreate(PurchaseOrderFields):
    site_id: UUID
    supplier_id: UUID
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    lines: list[PurchaseOrderLineCreate]


class PurchaseOrderResponse(PurchaseOrderFields, ORMModel):
    id: UUID
    site_id: UUID
    number: str
    supplier_id: UUID
    status: PurchaseOrderStatus
    created_by: str | None = None
    last_modified_by: str | None = None
    created_at: datetime
    updated_at: datetime
    total_part_amount: float
    total_item_amount: float
    total_amount: float
    grand_total: float
    received_total: float
    site_no: str | None = None
    site_name: str | None = None
    supplier_no: str | None = None
    supplier_name: str | None = None
    cost_center_no: str | None = None
    cost_center_name: str | None = None
    project_no: str | None = None
    project_name: str | None = None
    originator_no: str | None = None
    originator_name: str | None = None
    po_status_name: str | None = None
    po_status_no: str | None = None
    lines: list[PurchaseOrderLineResponse] = []


class PurchaseOrderUpdate(PartialUpdateMixin, PurchaseOrderFields):
    status: PurchaseOrderStatus | None = None
    supplier_id: UUID | None = None


# Meters
class MeterGroupCreate(BaseModel):
    site_id: UUID
    code: str
    name: str
    unit_of_measure: str | None = None


class MeterReadingUpdate(BaseModel):
    reading: float
    rollover: bool = False


class MeterReadingBatch(BaseModel):
    asset_id: UUID
    meter_group_id: UUID
    reading: float
    rollover: bool = False


class MeterReadingResponse(ORMModel):
    id: UUID
    meter_id: UUID
    reading: float
    rollover: bool
    recorded_at: datetime
    recorded_by: str | None = None


class MeterGroupResponse(ORMModel):
    id: UUID
    site_id: UUID
    code: str
    name: str
    unit_of_measure: str | None


class MeterResponse(ORMModel):
    id: UUID
    asset_id: UUID
    meter_group_id: UUID
    current_reading: float
    rollover_count: int
    rollover_point: float | None = None


class MeterDetailResponse(MeterResponse):
    asset_number: str
    asset_name: str
    meter_group_code: str
    meter_group_name: str
    unit_of_measure: str | None = None


class MeterReadingDetailResponse(MeterReadingResponse):
    asset_id: UUID
    asset_number: str
    asset_name: str
    meter_group_id: UUID
    meter_group_code: str
    meter_group_name: str
    unit_of_measure: str | None = None


# Personnel
class PersonnelCreate(PersonnelFields):
    site_id: UUID
    personnel_type: PersonnelType = PersonnelType.STAFF
    full_name: str
    email: EmailStr


class PersonnelResponse(ORMModel, PersonnelFields):
    id: UUID
    site_id: UUID
    personnel_type: PersonnelType
    full_name: str
    email: str
    is_active: bool


class PersonnelUpdate(PartialUpdateMixin, PersonnelFields):
    full_name: str | None = None
    email: EmailStr | None = None
    primary_contact: bool | None = None
    reviewer: bool | None = None
    is_active: bool | None = None


class TrainingCreate(TrainingFields):
    pass


# Webhooks
class WebhookSubscriptionCreate(BaseModel):
    site_id: UUID
    event_type: WebhookEvent
    callback_url: str
    secret: str | None = None


class WebhookSubscriptionResponse(ORMModel):
    id: UUID
    site_id: UUID
    event_type: WebhookEvent
    callback_url: str
    is_active: bool


# Custom fields
class CustomFieldDefinitionCreate(BaseModel):
    site_id: UUID
    entity_type: CustomFieldEntity
    name: str
    label: str
    data_type: CustomFieldDataType
    options: list[str] | None = None
    is_required: bool = False


class CustomFieldDefinitionUpdate(BaseModel):
    label: str | None = None
    options: list[str] | None = None
    is_required: bool | None = None


class CustomFieldDefinitionResponse(ORMModel):
    id: UUID
    site_id: UUID
    entity_type: CustomFieldEntity
    name: str
    label: str
    data_type: CustomFieldDataType
    options: list[str] | None = None
    is_required: bool


# Reports
class ReportSummary(BaseModel):
    open_work_orders: int
    overdue_work_orders: int
    open_corrective_maintenance: int
    open_service_requests: int
    parts_below_reorder: int
    pending_pm_queue: int


class WorkOrderTrendPoint(BaseModel):
    month: str
    completed: int
    opened: int


class WorkOrderMix(BaseModel):
    corrective: int
    preventive: int
    general: int


class PriorityBreakdown(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    other: int


class AttentionItem(BaseModel):
    id: str
    kind: str
    title: str
    subtitle: str
    priority: str | None
    status: str
    due_date: datetime | None
    path: str


class ExecutiveDashboard(BaseModel):
    site_name: str
    generated_at: datetime
    health_score: int
    open_work_orders: int
    overdue_work_orders: int
    open_corrective_maintenance: int
    open_service_requests: int
    parts_below_reorder: int
    pending_pm_queue: int
    total_assets: int
    active_assets: int
    down_assets: int
    critical_assets: int
    asset_availability_pct: float
    total_asset_value: float
    pm_compliance_pct: float
    wo_completion_rate_pct: float
    completed_last_30_days: int
    avg_resolution_days: float | None
    work_order_trend: list[WorkOrderTrendPoint]
    work_order_mix: WorkOrderMix
    priority_breakdown: PriorityBreakdown
    attention_items: list[AttentionItem]
