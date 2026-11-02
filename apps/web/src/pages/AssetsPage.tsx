import { useEffect, useState } from 'react';
import { Route, Routes, useNavigate, useParams, NavLink, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import RowActions from '../components/RowActions';
import FwFormFields from '../components/FwFormFields';
import AssetAttachments from '../components/AssetAttachments';
import FormPageShell, { FormActions } from '../components/FormPageShell';
import LoadingState from '../components/LoadingState';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ListToolbar from '../components/ListToolbar';
import { IconPlus } from '../components/icons';
import { useDefaultSiteId } from '../hooks/useSites';
import { useListFilters } from '../hooks/useListFilters';
import { ASSET_STATUS_FILTER } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import {
  ASSET_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';
import CustomFieldInputs, {
  customFieldsFromRecord,
  emptyCustomFieldValues,
  type CustomFieldDefinition,
} from '../components/CustomFieldInputs';

interface Asset {
  id: string;
  number: string;
  name: string;
  category: string | null;
  status: string;
  priority: string | null;
  is_critical: boolean;
}

export default function AssetsPage() {
  return (
    <Routes>
      <Route index element={<AssetsList />} />
      <Route path="new" element={<AssetForm />} />
      <Route path=":id/edit" element={<AssetForm />} />
      <Route path=":id/attachments" element={<AssetAttachmentsPage />} />
    </Routes>
  );
}

function AssetsList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['assets', queryString],
    queryFn: () => api<Paginated<Asset>>(`/v1/assets${queryString}`),
  });

  const items = data?.items ?? [];
  const total = data?.total_items ?? 0;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/assets/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assets'] }),
  });

  return (
    <div>
      <PageHeader
        title="Assets"
        description="Register and manage equipment, facilities, and critical assets."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/assets/new')}>
            <IconPlus size={16} />
            New Asset
          </button>
        }
      />
      {isLoading ? (
        <LoadingState label="Loading assets…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No assets yet" description="Create your first asset to begin tracking equipment and facilities." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search assets…"
            filters={[ASSET_STATUS_FILTER]}
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
                <th>Number</th>
                <th>Name</th>
                <th>Category</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id}>
                  <td><code>{a.number}</code></td>
                  <td>{a.name}{a.is_critical && <span className="badge badge-critical" style={{ marginLeft: 8 }}>Critical</span>}</td>
                  <td>{a.category ?? '—'}</td>
                  <td><span className="badge badge-open">{a.status}</span></td>
                  <td>{a.priority ?? '—'}</td>
                  <RowActions
                    onEdit={() => navigate(`/assets/${a.id}/edit`)}
                    onDelete={() => confirm(`Delete asset ${a.number}?`) && deleteMutation.mutate(a.id)}
                  />
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

function AssetForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() =>
    isEdit ? emptyFormFromFields(ASSET_FIELDS) : {
      ...emptyFormFromFields(ASSET_FIELDS),
      number: `AST-${Date.now().toString().slice(-6)}`,
      status: 'ACTIVE',
      priority: 'MEDIUM',
    },
  );
  const [lookups, setLookups] = useState({
    current_location_id: '',
    cost_center_id: '',
    supplier_id: '',
    warranty_vendor_id: '',
    parent_asset_id: '',
  });
  const [customFieldValues, setCustomFieldValues] = useState<Record<string, string | number | boolean>>({});

  const { data: record, isLoading } = useQuery({
    queryKey: ['asset', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/assets/${id}`),
    enabled: isEdit,
  });

  const { data: locations } = useQuery({
    queryKey: ['locations', siteId],
    queryFn: () => api<{ id: string; number: string; name: string }[]>(`/v1/locations${siteId ? `?site_id=${siteId}` : ''}`),
    enabled: !!siteId,
  });

  const { data: costCenters } = useQuery({
    queryKey: ['cost-centers', siteId],
    queryFn: () => api<{ id: string; number: string; name: string }[]>(`/v1/cost-centers${siteId ? `?site_id=${siteId}` : ''}`),
    enabled: !!siteId,
  });

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers', siteId],
    queryFn: () => api<{ id: string; name: string }[]>(`/v1/suppliers${siteId ? `?site_id=${siteId}` : ''}`),
    enabled: !!siteId,
  });

  const { data: assetsList } = useQuery({
    queryKey: ['assets-for-parent', siteId],
    queryFn: () => api<Paginated<{ id: string; number: string; name: string }>>(`/v1/assets?page_size=100${siteId ? `&site_id=${siteId}` : ''}`),
    enabled: !!siteId,
  });

  const { data: customFieldDefs } = useQuery({
    queryKey: ['custom-fields', 'ASSET', siteId],
    queryFn: () => api<CustomFieldDefinition[]>(`/v1/custom-fields?entity_type=ASSET${siteId ? `&site_id=${siteId}` : ''}`),
    enabled: !!siteId,
  });

  useEffect(() => {
    if (customFieldDefs && !record) {
      setCustomFieldValues(emptyCustomFieldValues(customFieldDefs));
    }
  }, [customFieldDefs, record]);

  useEffect(() => {
    if (record) {
      setForm(recordToForm(record, ASSET_FIELDS));
      setLookups({
        current_location_id: String(record.current_location_id ?? ''),
        cost_center_id: String(record.cost_center_id ?? ''),
        supplier_id: String(record.supplier_id ?? ''),
        warranty_vendor_id: String(record.warranty_vendor_id ?? ''),
        parent_asset_id: String(record.parent_asset_id ?? ''),
      });
      if (customFieldDefs) {
        setCustomFieldValues(customFieldsFromRecord(customFieldDefs, record));
      }
    }
  }, [record, customFieldDefs]);

  const saveMutation = useMutation({
    mutationFn: async (body: object) => {
      if (isEdit) {
        await api(`/v1/assets/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        return undefined;
      }
      return api<{ id: string }>('/v1/assets', { method: 'POST', body: JSON.stringify(body) });
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['assets'] });
      if (!isEdit && result?.id) {
        navigate(`/assets/${result.id}/attachments`);
      } else {
        navigate('/assets');
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!siteId) return;
    const defs = customFieldDefs ?? [];
    for (const def of defs) {
      if (!def.is_required) continue;
      const val = customFieldValues[def.name];
      if (def.data_type === 'BOOLEAN') continue;
      if (val === '' || val == null) {
        alert(`${def.label} is required.`);
        return;
      }
    }
    const custom_fields: Record<string, string | number | boolean> = {};
    for (const def of defs) {
      const val = customFieldValues[def.name];
      if (val !== '' && val != null) custom_fields[def.name] = val;
    }
    const body = formToPayload(form, ASSET_FIELDS, {
      ...(isEdit ? {} : { site_id: siteId }),
      current_location_id: lookups.current_location_id || undefined,
      cost_center_id: lookups.cost_center_id || undefined,
      supplier_id: lookups.supplier_id || undefined,
      warranty_vendor_id: lookups.warranty_vendor_id || undefined,
      parent_asset_id: lookups.parent_asset_id || undefined,
      ...(Object.keys(custom_fields).length ? { custom_fields } : {}),
    });
    saveMutation.mutate(body);
  };

  if (isEdit && isLoading) return <LoadingState label="Loading asset…" />;

  return (
    <FormPageShell
      title={isEdit ? 'Edit Asset' : 'New Asset'}
      description={isEdit ? 'Update asset details, classification, and custom fields.' : 'Register a new asset in the registry.'}
      backTo="/assets"
      backLabel="Back to assets"
    >
      {isEdit && id && (
        <div className="tab-bar form-page-tabs">
          <NavLink to={`/assets/${id}/edit`} className={({ isActive }) => `btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}>
            Details
          </NavLink>
          <NavLink to={`/assets/${id}/attachments`} className={({ isActive }) => `btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}>
            Photos & Attachments
          </NavLink>
        </div>
      )}
      {!isEdit && (
        <p className="form-hint">After saving, you will go to the attachments page to add photos and documents.</p>
      )}
      <form onSubmit={handleSubmit}>
        {isEdit && record && (
          <div className="po-summary-bar">
            {Boolean(record.site_name) && <div><span>Site</span><strong>{String(record.site_name)}</strong></div>}
            {Boolean(record.location_name) && <div><span>Location</span><strong>{String(record.location_name)}</strong></div>}
            {Boolean(record.location_path) && <div><span>Path</span><strong>{String(record.location_path)}</strong></div>}
            {Boolean(record.asset_status_name) && <div><span>Status</span><strong>{String(record.asset_status_name)}</strong></div>}
            {Boolean(record.photo_url) && <div><span>Photo</span><strong>{String(record.photo_name ?? 'Attached')}</strong></div>}
          </div>
        )}
        <details open style={{ marginBottom: 16 }}>
          <summary style={{ fontWeight: 600, marginBottom: 8, cursor: 'pointer' }}>References</summary>
          <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <div className="form-group">
              <label>Location</label>
              <select value={lookups.current_location_id} onChange={(e) => setLookups({ ...lookups, current_location_id: e.target.value })}>
                <option value="">—</option>
                {(locations ?? []).map((l) => <option key={l.id} value={l.id}>{l.number} — {l.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Cost Center</label>
              <select value={lookups.cost_center_id} onChange={(e) => setLookups({ ...lookups, cost_center_id: e.target.value })}>
                <option value="">—</option>
                {(costCenters ?? []).map((c) => <option key={c.id} value={c.id}>{c.number} — {c.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Supplier</label>
              <select value={lookups.supplier_id} onChange={(e) => setLookups({ ...lookups, supplier_id: e.target.value })}>
                <option value="">—</option>
                {(suppliers ?? []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Warranty Vendor</label>
              <select value={lookups.warranty_vendor_id} onChange={(e) => setLookups({ ...lookups, warranty_vendor_id: e.target.value })}>
                <option value="">—</option>
                {(suppliers ?? []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Parent Asset</label>
              <select value={lookups.parent_asset_id} onChange={(e) => setLookups({ ...lookups, parent_asset_id: e.target.value })}>
                <option value="">—</option>
                {(assetsList?.items ?? []).filter((a) => a.id !== id).map((a) => (
                  <option key={a.id} value={a.id}>{a.number} — {a.name}</option>
                ))}
              </select>
            </div>
          </div>
        </details>
        <FwFormFields fields={ASSET_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        <CustomFieldInputs
          definitions={customFieldDefs ?? []}
          values={customFieldValues}
          onChange={setCustomFieldValues}
        />
        {(customFieldDefs?.length ?? 0) === 0 && (
          <p className="form-hint">
            Need extra asset attributes?{' '}
            <Link to="/configurations">Create custom fields</Link> under Configurations → Asset Custom Fields.
          </p>
        )}
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/assets')} submitLabel={isEdit ? 'Save' : 'Save & add attachments'} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}

function AssetAttachmentsPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: record, isLoading } = useQuery({
    queryKey: ['asset', id],
    queryFn: () => api<{ number: string; name: string }>(`/v1/assets/${id}`),
    enabled: !!id,
  });

  if (!id) return null;
  if (isLoading) return <LoadingState label="Loading asset…" />;

  return (
    <FormPageShell
      title={record ? `${record.number} — ${record.name}` : 'Asset attachments'}
      description="Upload photos and attach manuals, spec sheets, and other documents."
      backTo="/assets"
      backLabel="Back to assets"
      footer={
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/assets')}>
          Done
        </button>
      }
    >
      <div className="tab-bar form-page-tabs">
        <NavLink to={`/assets/${id}/edit`} className={({ isActive }) => `btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}>
          Details
        </NavLink>
        <NavLink to={`/assets/${id}/attachments`} className={({ isActive }) => `btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}>
          Photos & Attachments
        </NavLink>
      </div>
      <AssetAttachments assetId={id} />
    </FormPageShell>
  );
}
