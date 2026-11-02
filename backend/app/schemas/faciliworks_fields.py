"""FaciliWorks-aligned field sets shared across Create/Update/Response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models import (
    PersonnelType,
    PurchaseOrderStatus,
    ScheduleType,
    ServiceRequestStatus,
    WorkOrderStatus,
    WorkOrderType,
)


class AssetFields(BaseModel):
    description: str | None = None
    asset_no: str | None = None
    serial_number: str | None = None
    make: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    manufacturer_no: str | None = None
    bar_code: str | None = None
    rfid: str | None = None
    tag_number: str | None = None
    category: str | None = None
    sub_category: str | None = None
    sub_category_no: str | None = None
    status: str = "ACTIVE"
    substatus: str | None = None
    asset_status_category: int | None = None
    asset_condition_no: str | None = None
    asset_condition_name: str | None = None
    priority: str | None = None
    criticality: str | None = None
    criticality_weight: float | None = None
    cost: float | None = None
    replacement_cost: float | None = None
    salvage_value: float | None = None
    purchase_date: datetime | None = None
    invoice_no: str | None = None
    invoice_date: datetime | None = None
    purchase_note: str | None = None
    equipment_life: float | None = None
    warranty_expiration_date: datetime | None = None
    warranty_title: str | None = None
    warranty_note: str | None = None
    service_date: datetime | None = None
    retirement_date: datetime | None = None
    retirement_reason: str | None = None
    manufacture_on: datetime | None = None
    out_of_service_begin_date: datetime | None = None
    out_of_service_end_date: datetime | None = None
    placed_on: datetime | None = None
    removed_on: datetime | None = None
    condition_date: datetime | None = None
    estimated_replacement_date: datetime | None = None
    last_checked_out_date: datetime | None = None
    current_location_id: UUID | None = None
    cost_center_id: UUID | None = None
    supplier_id: UUID | None = None
    warranty_vendor_id: UUID | None = None
    parent_asset_id: UUID | None = None
    is_critical: bool = False
    is_auto_generate: bool = False
    is_update_medium: bool = False
    is_tool_crib: bool = False
    is_system: bool = False
    is_referenced: bool = False
    notes: str | None = None
    assessment_note: str | None = None
    tool_crib_note: str | None = None
    emergency_note: str | None = None
    safety_note: str | None = None
    training_note: str | None = None
    shutdown_procedure: str | None = None
    loto_procedure: str | None = None
    hyperlink: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    medium_ids: str | None = None
    total_cost: float = 0
    total_hours: float = 0
    total_downtime: float = 0
    estimated_hours: float | None = None
    measurement_unit_id: int | None = None
    uom_cost: float | None = None
    uom_quantity: float | None = None
    system_name: str | None = None
    correlation_id: str | None = None
    security_group_id: UUID | None = None
    fs_type: str | None = None
    nist: str | None = None
    ref_standard: bool = False
    attach_to_event: bool = False
    asset_disposition: str | None = None
    user_def1: str | None = None
    user_def2: str | None = None
    user_def3: str | None = None


class WorkOrderFields(BaseModel):
    description: str | None = None
    priority: str | None = None
    asset_id: UUID | None = None
    location_id: UUID | None = None
    project_id: UUID | None = None
    cost_center_id: UUID | None = None
    date_due: datetime | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    problem: str | None = None
    action_taken: str | None = None
    root_cause: str | None = None
    downtime_date: datetime | None = None
    waiting_for_parts: bool = False
    waiting_for_contractor: bool = False
    waiting_for_shutdown: bool = False
    time_maint_hours: float | None = None
    time_maint_done: float | None = None
    last_maint_date: datetime | None = None
    wo_notes: str | None = None
    entered_by: str | None = None
    print_info: str | None = None
    shift: str | None = None
    job_disposition: str | None = None
    user_def1: str | None = None
    user_def2: str | None = None
    signed: bool = False
    printed: bool = False


class PartFields(BaseModel):
    manufacturer: str | None = None
    model: str | None = None
    category: str | None = None
    reorder_point: float = 0
    quantity_on_hand: float = 0
    unit_cost: float | None = None
    is_critical: bool = False
    status: str = "ACTIVE"
    storage_location_id: UUID | None = None
    supplier_id: UUID | None = None
    manufacturer_part_number: str | None = None
    cost_from_mfg: float | None = None
    max_quantity: float | None = None
    notes: str | None = None
    sub_category: str | None = None
    substatus: str | None = None
    look_ahead: str | None = None
    part_user1: str | None = None
    part_user2: str | None = None
    quantity_on_order: float = 0
    quantity_on_back_order: float = 0


class PersonnelFields(BaseModel):
    employee_id: str | None = None
    phone: str | None = None
    craft: str | None = None
    department: str | None = None
    hourly_rate: float | None = None
    address: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    home_phone: str | None = None
    work_phone_ext: str | None = None
    date_hired: datetime | None = None
    retire_date: datetime | None = None
    primary_contact: bool = False
    reviewer: bool = False
    job_title: str | None = None
    category: str | None = None
    crew: str | None = None
    specialty: str | None = None
    lead_time: int | None = None
    license_type: str | None = None
    salary: float | None = None
    salary_overtime: float | None = None


class ServiceRequestFields(BaseModel):
    requested_by: str | None = None
    requester_email: str | None = None
    requester_phone: str | None = None
    instructions: str | None = None
    priority: str | None = None
    asset_id: UUID | None = None
    location_id: UUID | None = None
    cas_type: str | None = None
    cas_date: datetime | None = None
    done_date: datetime | None = None


class AssetTaskFields(BaseModel):
    task_code: str
    description: str
    schedule_type: ScheduleType = ScheduleType.TIME
    recurrence_pattern: dict | None = None
    meter_frequency: float | None = None
    lead_time_days: int = 0
    due_date: datetime | None = None
    due_meter: float | None = None
    priority: str | None = None
    estimated_hours: float | None = None
    task_id: str | None = None
    task_type: str | None = None
    notes: str | None = None
    user_def1: str | None = None
    user_def2: str | None = None
    shift: str | None = None
    meter_group_id: UUID | None = None
    hyperlink: str | None = None
    can_detach: bool = True


class AssetWarrantyFields(BaseModel):
    provider: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    terms: str | None = None
    warranty_item_name: str | None = None
    account_no: str | None = None
    contact: str | None = None
    phone: str | None = None
    contract_type: str | None = None
    description: str | None = None
    invoice: str | None = None
    last_warranty_date: datetime | None = None
    next_warranty_due: datetime | None = None
    note: str | None = None
    warranty_amount: float | None = None
    warranty_frequency: int | None = None
    warranty_frequency_uom: str | None = None
    expired: bool = False


class TrainingFields(BaseModel):
    name: str
    completed_date: datetime | None = None
    expiry_date: datetime | None = None
    certification: str | None = None
    cert_type: str | None = None
    cert_term: int | None = None
    cert_term_uom: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    cost: float | None = None
    comments: str | None = None


class SupplierFields(BaseModel):
    contact_email: str | None = None
    contact_phone: str | None = None
    supplier_code: str | None = None
    contact: str | None = None
    phone: str | None = None
    address: str | None = None


class PurchaseOrderFields(BaseModel):
    name: str | None = None
    account_no: str | None = None
    date_submitted: datetime | None = None
    date_received: datetime | None = None
    date_completed: datetime | None = None
    date_expected: datetime | None = None
    date_originated: datetime | None = None
    total_tax: float = 0
    total_shipping: float = 0
    total_other: float = 0
    billing_name: str | None = None
    billing_addr1: str | None = None
    billing_addr2: str | None = None
    billing_city: str | None = None
    billing_state_province: str | None = None
    billing_postal_code: str | None = None
    billing_country_code: str | None = None
    shipping_name: str | None = None
    shipping_addr1: str | None = None
    shipping_addr2: str | None = None
    shipping_city: str | None = None
    shipping_state_province: str | None = None
    shipping_postal_code: str | None = None
    shipping_country_code: str | None = None
    notes: str | None = None
    name_format: str | None = None
    last_signed_by: str | None = None
    last_signed: str | None = None
    last_signed_on: datetime | None = None
    region_id: str | None = None
    region_name: str | None = None
    cost_center_id: UUID | None = None
    project_id: UUID | None = None
    originator_id: UUID | None = None
    po_status_category: int | None = None
    last_reminded_on: datetime | None = None
    is_auto_generate: bool = False
    correlation_id: str | None = None
    medium_count: int = 0
