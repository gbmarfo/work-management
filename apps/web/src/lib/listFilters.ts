export interface ListFilterOption {
  value: string;
  label: string;
}

export interface ListFilterDef {
  key: string;
  label: string;
  options: ListFilterOption[];
}

export function buildListQuery(
  params: Record<string, string | number | boolean | undefined | null>,
): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      sp.set(key, String(value));
    }
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : '';
}

export function filterItems<T extends object>(
  items: T[],
  search: string,
  searchFields: (keyof T)[],
  filters: Record<string, string>,
): T[] {
  let result = items;
  const q = search.trim().toLowerCase();
  if (q) {
    result = result.filter((item) =>
      searchFields.some((field) => String(item[field] ?? '').toLowerCase().includes(q)),
    );
  }
  for (const [key, value] of Object.entries(filters)) {
    if (!value) continue;
    result = result.filter((item) => String(item[key as keyof T] ?? '') === value);
  }
  return result;
}

export const PRIORITY_FILTER = {
  key: 'priority',
  label: 'Priority',
  options: [
    { value: 'LOW', label: 'Low' },
    { value: 'MEDIUM', label: 'Medium' },
    { value: 'HIGH', label: 'High' },
    { value: 'CRITICAL', label: 'Critical' },
  ],
};

export const WO_STATUS_FILTER = {
  key: 'status',
  label: 'Status',
  options: [
    { value: 'OPEN', label: 'Open' },
    { value: 'IN_PROGRESS', label: 'In Progress' },
    { value: 'WAITING_PARTS', label: 'Waiting Parts' },
    { value: 'COMPLETED', label: 'Completed' },
    { value: 'CANCELLED', label: 'Cancelled' },
  ],
};

export const WO_TYPE_FILTER = {
  key: 'type',
  label: 'Type',
  options: [
    { value: 'CORRECTIVE', label: 'Corrective' },
    { value: 'PREVENTIVE', label: 'Preventive' },
    { value: 'GENERAL', label: 'General' },
  ],
};

export const ASSET_STATUS_FILTER = {
  key: 'status',
  label: 'Status',
  options: [
    { value: 'ACTIVE', label: 'Active' },
    { value: 'INACTIVE', label: 'Inactive' },
    { value: 'DOWN', label: 'Down' },
    { value: 'RETIRED', label: 'Retired' },
  ],
};

export const SR_STATUS_FILTER = {
  key: 'status',
  label: 'Status',
  options: [
    { value: 'OPEN', label: 'Open' },
    { value: 'FOR_REVIEW', label: 'For Review' },
    { value: 'CLOSED', label: 'Closed' },
    { value: 'DECLINED', label: 'Declined' },
  ],
};

export const PO_STATUS_FILTER = {
  key: 'status',
  label: 'Status',
  options: [
    { value: 'DRAFT', label: 'Draft' },
    { value: 'SUBMITTED', label: 'Submitted' },
    { value: 'APPROVED', label: 'Approved' },
    { value: 'RECEIVED', label: 'Received' },
    { value: 'CANCELLED', label: 'Cancelled' },
  ],
};

export const PERSONNEL_TYPE_FILTER = {
  key: 'personnel_type',
  label: 'Type',
  options: [
    { value: 'STAFF', label: 'Staff' },
    { value: 'CONTRACTOR', label: 'Contractor' },
  ],
};

export const PART_STATUS_FILTER = {
  key: 'status',
  label: 'Status',
  options: [
    { value: 'ACTIVE', label: 'Active' },
    { value: 'INACTIVE', label: 'Inactive' },
  ],
};

export const CRITICALITY_FILTER = {
  key: 'criticality',
  label: 'Criticality',
  options: [
    { value: 'LOW', label: 'Low' },
    { value: 'MEDIUM', label: 'Medium' },
    { value: 'HIGH', label: 'High' },
    { value: 'CRITICAL', label: 'Critical' },
  ],
};
