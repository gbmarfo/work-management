// Empty base uses Vite dev proxy (same-origin, no CORS). Set VITE_API_URL for production.
const API_BASE = import.meta.env.VITE_API_URL ?? '';

export function getToken(): string | null {
  return localStorage.getItem('eam_token');
}

export function setToken(token: string) {
  localStorage.setItem('eam_token', token);
}

export function clearToken() {
  localStorage.removeItem('eam_token');
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new Error('Cannot reach the API. Make sure the backend is running on port 8000.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(', ') || 'Request failed'
          : 'Request failed';
    throw new Error(message);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Paginated<T> {
  items: T[];
  page_index: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next_page: boolean;
  has_previous_page: boolean;
}

export interface ReportSummary {
  open_work_orders: number;
  overdue_work_orders: number;
  open_corrective_maintenance: number;
  open_service_requests: number;
  parts_below_reorder: number;
  pending_pm_queue: number;
}

export interface WorkOrderTrendPoint {
  month: string;
  completed: number;
  opened: number;
}

export interface WorkOrderMix {
  corrective: number;
  preventive: number;
  general: number;
}

export interface PriorityBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
  other: number;
}

export interface AttentionItem {
  id: string;
  kind: string;
  title: string;
  subtitle: string;
  priority: string | null;
  status: string;
  due_date: string | null;
  path: string;
}

export interface ExecutiveDashboard extends ReportSummary {
  site_name: string;
  generated_at: string;
  health_score: number;
  total_assets: number;
  active_assets: number;
  down_assets: number;
  critical_assets: number;
  asset_availability_pct: number;
  total_asset_value: number;
  pm_compliance_pct: number;
  wo_completion_rate_pct: number;
  completed_last_30_days: number;
  avg_resolution_days: number | null;
  work_order_trend: WorkOrderTrendPoint[];
  work_order_mix: WorkOrderMix;
  priority_breakdown: PriorityBreakdown;
  attention_items: AttentionItem[];
}

export interface AssetAttachment {
  id: string;
  entity_type: string;
  entity_id: string;
  file_name: string;
  content_type: string;
  file_size: number;
  kind: 'PHOTO' | 'DOCUMENT';
  is_primary: boolean;
  created_at: string;
}

export async function uploadAssetAttachments(
  assetId: string,
  files: File[],
  options: { kind?: 'photo' | 'document'; setPrimary?: boolean } = {},
): Promise<AssetAttachment[]> {
  const token = getToken();
  const form = new FormData();
  for (const file of files) {
    form.append('files', file);
  }
  const params = new URLSearchParams();
  if (options.kind) params.set('kind', options.kind);
  if (options.setPrimary) params.set('set_primary', 'true');
  const qs = params.toString();

  const res = await fetch(`${API_BASE}/v1/assets/${assetId}/attachments${qs ? `?${qs}` : ''}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === 'string' ? err.detail : 'Upload failed');
  }
  return res.json();
}

export async function fetchAttachmentBlob(attachmentId: string): Promise<Blob> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/v1/assets/attachments/${attachmentId}/file`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error('Failed to load file');
  return res.blob();
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
