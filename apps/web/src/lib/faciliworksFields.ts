export type FwFieldType = 'text' | 'number' | 'date' | 'checkbox' | 'textarea' | 'select';

export interface FwFieldDef {
  key: string;
  label: string;
  type: FwFieldType;
  section?: string;
  required?: boolean;
  createOnly?: boolean;
  options?: { value: string; label: string }[];
}

export { ASSET_FIELDS } from './assetFields';

export const WORK_ORDER_FIELDS: FwFieldDef[] = [
  { key: 'type', label: 'Type', type: 'select', section: 'General', required: true, createOnly: true, options: [
    { value: 'CORRECTIVE', label: 'Corrective' }, { value: 'PREVENTIVE', label: 'Preventive' }, { value: 'GENERAL', label: 'General' },
  ]},
  { key: 'title', label: 'Title', type: 'text', section: 'General', required: true },
  { key: 'status', label: 'Status', type: 'select', section: 'General', options: [
    { value: 'OPEN', label: 'Open' }, { value: 'IN_PROGRESS', label: 'In Progress' }, { value: 'COMPLETED', label: 'Completed' }, { value: 'CANCELLED', label: 'Cancelled' },
  ]},
  { key: 'priority', label: 'Priority', type: 'select', section: 'General', options: [
    { value: 'LOW', label: 'Low' }, { value: 'MEDIUM', label: 'Medium' }, { value: 'HIGH', label: 'High' }, { value: 'CRITICAL', label: 'Critical' },
  ]},
  { key: 'description', label: 'Job Notes', type: 'textarea', section: 'General' },
  { key: 'problem', label: 'Problem', type: 'textarea', section: 'General' },
  { key: 'action_taken', label: 'Action Taken', type: 'textarea', section: 'General' },
  { key: 'root_cause', label: 'Root Cause', type: 'text', section: 'General' },
  { key: 'date_due', label: 'Due Date', type: 'date', section: 'Scheduling' },
  { key: 'downtime_date', label: 'Downtime Date', type: 'date', section: 'Scheduling' },
  { key: 'last_maint_date', label: 'Last Maint Date', type: 'date', section: 'Scheduling' },
  { key: 'estimated_hours', label: 'Est. Hours', type: 'number', section: 'Labor' },
  { key: 'actual_hours', label: 'Actual Hours', type: 'number', section: 'Labor' },
  { key: 'time_maint_hours', label: 'Time Maint Hours', type: 'number', section: 'Labor' },
  { key: 'time_maint_done', label: 'Time Maint Done', type: 'number', section: 'Labor' },
  { key: 'shift', label: 'Shift', type: 'text', section: 'Labor' },
  { key: 'entered_by', label: 'Entered By', type: 'text', section: 'Labor' },
  { key: 'wo_notes', label: 'Notes', type: 'textarea', section: 'Other' },
  { key: 'print_info', label: 'Print Info', type: 'text', section: 'Other' },
  { key: 'job_disposition', label: 'Job Disposition', type: 'text', section: 'Other' },
  { key: 'user_def1', label: 'User Def 1', type: 'text', section: 'User Defined' },
  { key: 'user_def2', label: 'User Def 2', type: 'text', section: 'User Defined' },
  { key: 'waiting_for_parts', label: 'Waiting for Parts', type: 'checkbox', section: 'Flags' },
  { key: 'waiting_for_contractor', label: 'Waiting for Contractor', type: 'checkbox', section: 'Flags' },
  { key: 'waiting_for_shutdown', label: 'Waiting for Shutdown', type: 'checkbox', section: 'Flags' },
  { key: 'signed', label: 'Signed', type: 'checkbox', section: 'Flags' },
  { key: 'printed', label: 'Printed', type: 'checkbox', section: 'Flags' },
];

export const CM_FIELDS: FwFieldDef[] = WORK_ORDER_FIELDS.filter((f) => f.key !== 'type');

export const PART_FIELDS: FwFieldDef[] = [
  { key: 'part_number', label: 'Part Number', type: 'text', section: 'Identification', required: true, createOnly: true },
  { key: 'description', label: 'Description', type: 'text', section: 'Identification', required: true },
  { key: 'manufacturer_part_number', label: 'Mfg Part Number', type: 'text', section: 'Identification' },
  { key: 'manufacturer', label: 'Manufacturer', type: 'text', section: 'Identification' },
  { key: 'model', label: 'Model', type: 'text', section: 'Identification' },
  { key: 'category', label: 'Category', type: 'text', section: 'Classification' },
  { key: 'sub_category', label: 'Sub Category', type: 'text', section: 'Classification' },
  { key: 'substatus', label: 'Substatus', type: 'text', section: 'Classification' },
  { key: 'status', label: 'Status', type: 'select', section: 'Classification', options: [
    { value: 'ACTIVE', label: 'Active' }, { value: 'INACTIVE', label: 'Inactive' },
  ]},
  { key: 'look_ahead', label: 'Look Ahead', type: 'text', section: 'Classification' },
  { key: 'is_critical', label: 'Critical Part', type: 'checkbox', section: 'Classification' },
  { key: 'quantity_on_hand', label: 'Qty On Hand', type: 'number', section: 'Inventory' },
  { key: 'quantity_on_order', label: 'Qty On Order', type: 'number', section: 'Inventory' },
  { key: 'quantity_on_back_order', label: 'Qty On Back Order', type: 'number', section: 'Inventory' },
  { key: 'reorder_point', label: 'Reorder Point', type: 'number', section: 'Inventory' },
  { key: 'max_quantity', label: 'Max Quantity', type: 'number', section: 'Inventory' },
  { key: 'unit_cost', label: 'Unit Cost', type: 'number', section: 'Financial' },
  { key: 'cost_from_mfg', label: 'Cost from Mfg', type: 'number', section: 'Financial' },
  { key: 'notes', label: 'Notes', type: 'textarea', section: 'Other' },
  { key: 'part_user1', label: 'Part User 1', type: 'text', section: 'User Defined' },
  { key: 'part_user2', label: 'Part User 2', type: 'text', section: 'User Defined' },
];

export const PERSONNEL_FIELDS: FwFieldDef[] = [
  { key: 'full_name', label: 'Full Name', type: 'text', section: 'Identity', required: true },
  { key: 'email', label: 'Email', type: 'text', section: 'Identity', required: true },
  { key: 'employee_id', label: 'Employee ID', type: 'text', section: 'Identity' },
  { key: 'job_title', label: 'Job Title', type: 'text', section: 'Identity' },
  { key: 'craft', label: 'Craft', type: 'text', section: 'Identity' },
  { key: 'department', label: 'Department', type: 'text', section: 'Identity' },
  { key: 'category', label: 'Category', type: 'text', section: 'Identity' },
  { key: 'crew', label: 'Crew', type: 'text', section: 'Identity' },
  { key: 'specialty', label: 'Specialty', type: 'text', section: 'Identity' },
  { key: 'phone', label: 'Work Phone', type: 'text', section: 'Contact' },
  { key: 'work_phone_ext', label: 'Work Phone Ext', type: 'text', section: 'Contact' },
  { key: 'home_phone', label: 'Home Phone', type: 'text', section: 'Contact' },
  { key: 'address', label: 'Address', type: 'text', section: 'Address' },
  { key: 'address2', label: 'Address 2', type: 'text', section: 'Address' },
  { key: 'city', label: 'City', type: 'text', section: 'Address' },
  { key: 'state', label: 'State', type: 'text', section: 'Address' },
  { key: 'zip_code', label: 'Zip Code', type: 'text', section: 'Address' },
  { key: 'country', label: 'Country', type: 'text', section: 'Address' },
  { key: 'date_hired', label: 'Date Hired', type: 'date', section: 'Employment' },
  { key: 'retire_date', label: 'Retire Date', type: 'date', section: 'Employment' },
  { key: 'lead_time', label: 'Lead Time', type: 'number', section: 'Employment' },
  { key: 'license_type', label: 'License Type', type: 'text', section: 'Employment' },
  { key: 'hourly_rate', label: 'Hourly Rate', type: 'number', section: 'Compensation' },
  { key: 'salary', label: 'Salary', type: 'number', section: 'Compensation' },
  { key: 'salary_overtime', label: 'Salary Overtime', type: 'number', section: 'Compensation' },
  { key: 'primary_contact', label: 'Primary Contact', type: 'checkbox', section: 'Flags' },
  { key: 'reviewer', label: 'Reviewer', type: 'checkbox', section: 'Flags' },
  { key: 'is_active', label: 'Active', type: 'checkbox', section: 'Flags' },
  { key: 'personnel_type', label: 'Personnel Type', type: 'select', section: 'Identity', createOnly: true, options: [
    { value: 'STAFF', label: 'Staff' }, { value: 'CONTRACTOR', label: 'Contractor' },
  ]},
];

export const SERVICE_REQUEST_FIELDS: FwFieldDef[] = [
  { key: 'problem', label: 'Problem', type: 'textarea', section: 'Request', required: true },
  { key: 'requested_by', label: 'Requested By', type: 'text', section: 'Request' },
  { key: 'requester_email', label: 'Requester Email', type: 'text', section: 'Request' },
  { key: 'requester_phone', label: 'Requester Phone', type: 'text', section: 'Request' },
  { key: 'instructions', label: 'Instructions', type: 'textarea', section: 'Request' },
  { key: 'priority', label: 'Priority', type: 'select', section: 'Request', options: [
    { value: 'LOW', label: 'Low' }, { value: 'MEDIUM', label: 'Medium' }, { value: 'HIGH', label: 'High' },
  ]},
  { key: 'cas_type', label: 'CAS Type', type: 'text', section: 'CAS' },
  { key: 'cas_date', label: 'CAS Date', type: 'date', section: 'CAS' },
  { key: 'done_date', label: 'Done Date', type: 'date', section: 'CAS' },
  { key: 'status', label: 'Status', type: 'select', section: 'Status', options: [
    { value: 'OPEN', label: 'Open' }, { value: 'IN_PROGRESS', label: 'In Progress' }, { value: 'CLOSED', label: 'Closed' },
  ]},
  { key: 'progress', label: 'Progress', type: 'text', section: 'Status' },
];

export const ASSET_TASK_FIELDS: FwFieldDef[] = [
  { key: 'task_code', label: 'Task Code', type: 'text', section: 'Task', required: true },
  { key: 'task_id', label: 'Task ID', type: 'text', section: 'Task' },
  { key: 'description', label: 'Description', type: 'text', section: 'Task', required: true },
  { key: 'task_type', label: 'Task Type', type: 'text', section: 'Task' },
  { key: 'schedule_type', label: 'Schedule Type', type: 'select', section: 'Schedule', options: [
    { value: 'TIME', label: 'Time' }, { value: 'METER', label: 'Meter' }, { value: 'BOTH', label: 'Both' },
  ]},
  { key: 'due_date', label: 'Due Date', type: 'date', section: 'Schedule' },
  { key: 'due_meter', label: 'Due Meter', type: 'number', section: 'Schedule' },
  { key: 'meter_frequency', label: 'Meter Frequency', type: 'number', section: 'Schedule' },
  { key: 'lead_time_days', label: 'Lead Time (days)', type: 'number', section: 'Schedule' },
  { key: 'priority', label: 'Priority', type: 'select', section: 'Schedule', options: [
    { value: 'LOW', label: 'Low' }, { value: 'MEDIUM', label: 'Medium' }, { value: 'HIGH', label: 'High' },
  ]},
  { key: 'estimated_hours', label: 'Est. Hours', type: 'number', section: 'Schedule' },
  { key: 'shift', label: 'Shift', type: 'text', section: 'Other' },
  { key: 'hyperlink', label: 'Hyperlink', type: 'text', section: 'Other' },
  { key: 'notes', label: 'Notes', type: 'textarea', section: 'Other' },
  { key: 'user_def1', label: 'User Def 1', type: 'text', section: 'User Defined' },
  { key: 'user_def2', label: 'User Def 2', type: 'text', section: 'User Defined' },
  { key: 'can_detach', label: 'Can Detach', type: 'checkbox', section: 'Other' },
  { key: 'status', label: 'Status', type: 'select', section: 'Status', options: [
    { value: 'ACTIVE', label: 'Active' }, { value: 'INACTIVE', label: 'Inactive' },
  ]},
  { key: 'is_active', label: 'Active', type: 'checkbox', section: 'Status' },
];

export const PURCHASE_ORDER_FIELDS: FwFieldDef[] = [
  { key: 'name', label: 'Name', type: 'text', section: 'General' },
  { key: 'account_no', label: 'Account No', type: 'text', section: 'General' },
  { key: 'status', label: 'Status', type: 'select', section: 'General', options: [
    { value: 'DRAFT', label: 'Draft' }, { value: 'SUBMITTED', label: 'Submitted' },
    { value: 'APPROVED', label: 'Approved' }, { value: 'RECEIVED', label: 'Received' }, { value: 'CANCELLED', label: 'Cancelled' },
  ]},
  { key: 'name_format', label: 'Name Format', type: 'text', section: 'General' },
  { key: 'correlation_id', label: 'Correlation ID', type: 'text', section: 'General' },
  { key: 'region_id', label: 'Region ID', type: 'text', section: 'General' },
  { key: 'region_name', label: 'Region Name', type: 'text', section: 'General' },
  { key: 'po_status_category', label: 'PO Status Category', type: 'number', section: 'General' },
  { key: 'date_originated', label: 'Date Originated', type: 'date', section: 'Dates' },
  { key: 'date_submitted', label: 'Date Submitted', type: 'date', section: 'Dates' },
  { key: 'date_expected', label: 'Date Expected', type: 'date', section: 'Dates' },
  { key: 'date_received', label: 'Date Received', type: 'date', section: 'Dates' },
  { key: 'date_completed', label: 'Date Completed', type: 'date', section: 'Dates' },
  { key: 'last_reminded_on', label: 'Last Reminded On', type: 'date', section: 'Dates' },
  { key: 'total_tax', label: 'Total Tax', type: 'number', section: 'Totals' },
  { key: 'total_shipping', label: 'Total Shipping', type: 'number', section: 'Totals' },
  { key: 'total_other', label: 'Total Other', type: 'number', section: 'Totals' },
  { key: 'billing_name', label: 'Billing Name', type: 'text', section: 'Billing Address' },
  { key: 'billing_addr1', label: 'Billing Address 1', type: 'text', section: 'Billing Address' },
  { key: 'billing_addr2', label: 'Billing Address 2', type: 'text', section: 'Billing Address' },
  { key: 'billing_city', label: 'Billing City', type: 'text', section: 'Billing Address' },
  { key: 'billing_state_province', label: 'Billing State/Province', type: 'text', section: 'Billing Address' },
  { key: 'billing_postal_code', label: 'Billing Postal Code', type: 'text', section: 'Billing Address' },
  { key: 'billing_country_code', label: 'Billing Country Code', type: 'text', section: 'Billing Address' },
  { key: 'shipping_name', label: 'Shipping Name', type: 'text', section: 'Shipping Address' },
  { key: 'shipping_addr1', label: 'Shipping Address 1', type: 'text', section: 'Shipping Address' },
  { key: 'shipping_addr2', label: 'Shipping Address 2', type: 'text', section: 'Shipping Address' },
  { key: 'shipping_city', label: 'Shipping City', type: 'text', section: 'Shipping Address' },
  { key: 'shipping_state_province', label: 'Shipping State/Province', type: 'text', section: 'Shipping Address' },
  { key: 'shipping_postal_code', label: 'Shipping Postal Code', type: 'text', section: 'Shipping Address' },
  { key: 'shipping_country_code', label: 'Shipping Country Code', type: 'text', section: 'Shipping Address' },
  { key: 'last_signed_by', label: 'Last Signed By', type: 'text', section: 'Signatures' },
  { key: 'last_signed', label: 'Last Signed', type: 'text', section: 'Signatures' },
  { key: 'last_signed_on', label: 'Last Signed On', type: 'date', section: 'Signatures' },
  { key: 'notes', label: 'Note', type: 'textarea', section: 'Other' },
  { key: 'is_auto_generate', label: 'Auto Generate', type: 'checkbox', section: 'Other' },
  { key: 'medium_count', label: 'Medium Count', type: 'number', section: 'Other' },
];

/** Build empty form state from field definitions */
export function emptyFormFromFields(fields: FwFieldDef[]): Record<string, string | boolean | number> {
  const form: Record<string, string | boolean | number> = {};
  for (const f of fields) {
    if (f.type === 'checkbox') form[f.key] = false;
    else if (f.type === 'number') form[f.key] = '';
    else form[f.key] = '';
  }
  return form;
}

/** Map API record to form values */
export function recordToForm(record: Record<string, unknown>, fields: FwFieldDef[]): Record<string, string | boolean | number> {
  const form = emptyFormFromFields(fields);
  for (const f of fields) {
    const v = record[f.key];
    if (v == null) continue;
    if (f.type === 'checkbox') form[f.key] = Boolean(v);
    else if (f.type === 'date' && typeof v === 'string') form[f.key] = v.slice(0, 10);
    else if (f.type === 'number') form[f.key] = v as number;
    else form[f.key] = String(v);
  }
  return form;
}

/** Serialize form to API payload, omitting empty strings */
export function formToPayload(
  form: Record<string, string | boolean | number>,
  fields: FwFieldDef[],
  extra: Record<string, unknown> = {},
): Record<string, unknown> {
  const body: Record<string, unknown> = { ...extra };
  for (const f of fields) {
    const v = form[f.key];
    if (f.type === 'checkbox') {
      body[f.key] = Boolean(v);
    } else if (f.type === 'number') {
      if (v !== '' && v != null) body[f.key] = Number(v);
    } else if (typeof v === 'string') {
      if (v.trim() !== '') body[f.key] = v.trim();
      else if (f.required) body[f.key] = v;
    }
  }
  return body;
}
