import { useEffect, useState } from 'react';
import { Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import FwFormFields from '../components/FwFormFields';
import FormPageShell, { FormActions } from '../components/FormPageShell';
import LoadingState from '../components/LoadingState';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ListToolbar from '../components/ListToolbar';
import { IconPlus } from '../components/icons';
import { useDefaultSiteId } from '../hooks/useSites';
import { useListFilters } from '../hooks/useListFilters';
import { PO_STATUS_FILTER } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import {
  PURCHASE_ORDER_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';

interface PurchaseOrderLine {
  id: string;
  part_id: string;
  quantity: number;
  unit_price: number;
  quantity_received: number;
  part_number: string | null;
  part_description: string | null;
}

interface PurchaseOrder {
  id: string;
  number: string;
  name: string | null;
  status: string;
  supplier_id: string;
  supplier_name: string | null;
  grand_total: number;
  total_amount: number;
  date_expected: string | null;
  po_status_name: string | null;
  notes: string | null;
  lines?: PurchaseOrderLine[];
  cost_center_id?: string | null;
  project_id?: string | null;
  originator_id?: string | null;
  total_part_amount?: number;
  received_total?: number;
  created_by?: string | null;
}

interface Lookup { id: string; name: string; number?: string; code?: string; full_name?: string; employee_id?: string; part_number?: string; description?: string }

const lineEmpty = { part_id: '', quantity: 1, unit_price: 0 };

export default function PurchaseOrdersPage() {
  return (
    <Routes>
      <Route index element={<PurchaseOrdersList />} />
      <Route path="new" element={<PurchaseOrderForm />} />
      <Route path=":id/edit" element={<PurchaseOrderForm />} />
    </Routes>
  );
}

function PurchaseOrdersList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', queryString],
    queryFn: () => api<PurchaseOrder[]>(`/v1/purchase-orders${queryString}`),
  });

  const items = data ?? [];
  const total = items.length;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/purchase-orders/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['purchase-orders'] }),
  });

  const receiveMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/purchase-orders/${id}/receive`, { method: 'PUT' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['purchase-orders'] });
      qc.invalidateQueries({ queryKey: ['parts'] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Purchase Orders"
        description="Create and track procurement orders for parts and supplies."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/purchase-orders/new')}>
            <IconPlus size={16} />
            New Purchase Order
          </button>
        }
      />

      {isLoading ? (
        <LoadingState label="Loading purchase orders…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No purchase orders" description="Create a purchase order to procure parts from suppliers." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search purchase orders…"
            filters={[PO_STATUS_FILTER]}
            filterValues={filters}
            onFilterChange={setFilter}
            onReset={hasActive ? reset : undefined}
            resultCount={items.length}
            totalCount={total}
          />
          {hasActive && items.length === 0 ? (
            <EmptyState title="No results match your search or filters." />
          ) : (
          <table>
            <thead>
              <tr>
                <th>PO Number</th>
                <th>Name</th>
                <th>Supplier</th>
                <th>Status</th>
                <th>Expected</th>
                <th>Grand Total</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((po) => (
                <tr key={po.id}>
                  <td><code>{po.number}</code></td>
                  <td>{po.name ?? '—'}</td>
                  <td>{po.supplier_name ?? '—'}</td>
                  <td><span className="badge badge-open">{po.po_status_name ?? po.status}</span></td>
                  <td>{po.date_expected ? new Date(po.date_expected).toLocaleDateString() : '—'}</td>
                  <td>${po.grand_total.toFixed(2)}</td>
                  <td className="actions-cell">
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate(`/purchase-orders/${po.id}/edit`)}>Edit</button>
                    {po.status !== 'RECEIVED' && (
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => receiveMutation.mutate(po.id)}>Receive</button>
                    )}
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => confirm(`Delete ${po.number}?`) && deleteMutation.mutate(po.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}
        </div>
      )}
    </div>
  );
}

function PurchaseOrderForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(PURCHASE_ORDER_FIELDS),
    status: 'DRAFT',
  }));
  const [supplierId, setSupplierId] = useState('');
  const [costCenterId, setCostCenterId] = useState('');
  const [projectId, setProjectId] = useState('');
  const [originatorId, setOriginatorId] = useState('');
  const [line, setLine] = useState(lineEmpty);
  const [lines, setLines] = useState<PurchaseOrderLine[]>([]);

  const { data: record, isLoading } = useQuery({
    queryKey: ['purchase-order', id],
    queryFn: () => api<PurchaseOrder>(`/v1/purchase-orders/${id}`),
    enabled: isEdit,
  });

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => api<Lookup[]>('/v1/suppliers'),
  });

  const { data: costCenters } = useQuery({
    queryKey: ['cost-centers'],
    queryFn: () => api<Lookup[]>('/v1/cost-centers'),
  });

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api<Lookup[]>('/v1/projects'),
  });

  const { data: personnel } = useQuery({
    queryKey: ['personnel'],
    queryFn: () => api<Lookup[]>('/v1/personnel'),
  });

  const { data: partsData } = useQuery({
    queryKey: ['parts-for-po'],
    queryFn: () => api<Paginated<Lookup>>('/v1/parts?page_size=100'),
    enabled: !isEdit,
  });

  useEffect(() => {
    if (record) {
      setForm(recordToForm(record as unknown as Record<string, unknown>, PURCHASE_ORDER_FIELDS));
      setSupplierId(record.supplier_id);
      setCostCenterId(record.cost_center_id ?? '');
      setProjectId(record.project_id ?? '');
      setOriginatorId(record.originator_id ?? '');
      setLines(record.lines ?? []);
    }
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/purchase-orders/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/purchase-orders', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['purchase-orders'] });
      navigate('/purchase-orders');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading purchase order…" />;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!siteId) return;
    const payload = formToPayload(form, PURCHASE_ORDER_FIELDS, {
      supplier_id: supplierId || undefined,
      cost_center_id: costCenterId || undefined,
      project_id: projectId || undefined,
      originator_id: originatorId || undefined,
    });
    if (isEdit) {
      saveMutation.mutate(payload);
    } else {
      if (!supplierId || !line.part_id) return;
      saveMutation.mutate({
        ...payload,
        site_id: siteId,
        lines: [{ part_id: line.part_id, quantity: Number(line.quantity), unit_price: Number(line.unit_price) }],
      });
    }
  };

  return (
    <FormPageShell
      title={isEdit ? `Edit PO ${record?.number ?? ''}` : 'New Purchase Order'}
      backTo="/purchase-orders"
      backLabel="Back to purchase orders"
    >
      <form onSubmit={handleSubmit}>
        {isEdit && record && (
          <div className="po-summary-bar">
            <div><span>PO Number</span><strong>{record.number}</strong></div>
            <div><span>Part Total</span><strong>${(record.total_part_amount ?? record.total_amount).toFixed(2)}</strong></div>
            <div><span>Grand Total</span><strong>${record.grand_total.toFixed(2)}</strong></div>
            <div><span>Received</span><strong>${(record.received_total ?? 0).toFixed(2)}</strong></div>
            {record.created_by && <div><span>Created By</span><strong>{record.created_by}</strong></div>}
          </div>
        )}

        <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px', marginBottom: 16 }}>
          <div className="form-group">
            <label>Supplier *</label>
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required disabled={isEdit}>
              <option value="">Select supplier…</option>
              {(suppliers ?? []).map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Cost Center</label>
            <select value={costCenterId} onChange={(e) => setCostCenterId(e.target.value)}>
              <option value="">—</option>
              {(costCenters ?? []).map((c) => (
                <option key={c.id} value={c.id}>{c.number} — {c.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Project</label>
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">—</option>
              {(projects ?? []).map((p) => (
                <option key={p.id} value={p.id}>{p.number} — {p.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Originator</label>
            <select value={originatorId} onChange={(e) => setOriginatorId(e.target.value)}>
              <option value="">—</option>
              {(personnel ?? []).map((p) => (
                <option key={p.id} value={p.id}>{p.employee_id ? `${p.employee_id} — ` : ''}{p.full_name ?? p.name}</option>
              ))}
            </select>
          </div>
        </div>

        <FwFormFields fields={PURCHASE_ORDER_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />

        {!isEdit ? (
          <details open style={{ marginTop: 16 }}>
            <summary style={{ fontWeight: 600, marginBottom: 8, cursor: 'pointer' }}>Line Items</summary>
            <div className="form-row">
              <div className="form-group">
                <label>Part *</label>
                <select value={line.part_id} onChange={(e) => setLine({ ...line, part_id: e.target.value })} required>
                  <option value="">Select part…</option>
                  {(partsData?.items ?? []).map((p) => (
                    <option key={p.id} value={p.id}>{p.part_number} — {p.description}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity</label>
                <input type="number" min="1" value={line.quantity} onChange={(e) => setLine({ ...line, quantity: Number(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label>Unit Price</label>
                <input type="number" min="0" step="0.01" value={line.unit_price} onChange={(e) => setLine({ ...line, unit_price: Number(e.target.value) })} required />
              </div>
            </div>
          </details>
        ) : lines.length > 0 && (
          <div className="table-card" style={{ marginTop: 16 }}>
            <table>
              <thead>
                <tr><th>Part</th><th>Description</th><th>Qty</th><th>Unit Price</th><th>Received</th><th>Line Total</th></tr>
              </thead>
              <tbody>
                {lines.map((row) => (
                  <tr key={row.id}>
                    <td><code>{row.part_number}</code></td>
                    <td>{row.part_description}</td>
                    <td>{row.quantity}</td>
                    <td>${row.unit_price.toFixed(2)}</td>
                    <td>{row.quantity_received}</td>
                    <td>${(row.quantity * row.unit_price).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/purchase-orders')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
