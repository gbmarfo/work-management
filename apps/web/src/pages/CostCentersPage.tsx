import { useEffect, useState } from 'react';
import { Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import RowActions from '../components/RowActions';
import FormPageShell, { FormActions } from '../components/FormPageShell';
import LoadingState from '../components/LoadingState';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ListToolbar from '../components/ListToolbar';
import { IconPlus } from '../components/icons';
import { useDefaultSiteId } from '../hooks/useSites';
import { useListFilters } from '../hooks/useListFilters';
import { api } from '../api';

interface CostCenter {
  id: string;
  number: string;
  name: string;
  description: string | null;
  active: boolean;
  color_code: string | null;
  site_name: string | null;
}

const emptyForm = {
  number: '',
  name: '',
  description: '',
  active: true,
  color_code: '',
};

const ACTIVE_FILTER = {
  key: 'active',
  label: 'Status',
  options: [
    { value: '', label: 'All' },
    { value: 'true', label: 'Active' },
    { value: 'false', label: 'Inactive' },
  ],
};

export default function CostCentersPage() {
  return (
    <Routes>
      <Route index element={<CostCentersList />} />
      <Route path="new" element={<CostCenterForm />} />
      <Route path=":id/edit" element={<CostCenterForm />} />
    </Routes>
  );
}

function CostCentersList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
    extra: siteId ? { site_id: siteId } : undefined,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['cost-centers', queryString],
    queryFn: () => api<CostCenter[]>(`/v1/cost-centers${queryString}`),
    enabled: !!siteId,
  });

  const items = data ?? [];
  const total = items.length;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/cost-centers/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cost-centers'] }),
  });

  return (
    <div>
      <PageHeader
        title="Cost Centers"
        description="Manage cost centers for assets, work orders, and purchase orders."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/cost-centers/new')}>
            <IconPlus size={16} />
            New Cost Center
          </button>
        }
      />

      {isLoading ? (
        <LoadingState label="Loading cost centers…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No cost centers" description="Add cost centers to track spending by department or budget code." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search cost centers…"
            filters={[ACTIVE_FILTER]}
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
                  <th>Description</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((cc) => (
                  <tr key={cc.id}>
                    <td>
                      {cc.color_code ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ width: 10, height: 10, borderRadius: '50%', background: cc.color_code, display: 'inline-block' }} />
                          <code>{cc.number}</code>
                        </span>
                      ) : (
                        <code>{cc.number}</code>
                      )}
                    </td>
                    <td>{cc.name}</td>
                    <td>{cc.description ?? '—'}</td>
                    <td>
                      <span className={`badge ${cc.active ? 'badge-completed' : 'badge-warning'}`}>
                        {cc.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <RowActions
                      onEdit={() => navigate(`/cost-centers/${cc.id}/edit`)}
                      onDelete={() => confirm(`Delete cost center ${cc.number}?`) && deleteMutation.mutate(cc.id)}
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

function CostCenterForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState(emptyForm);

  const { data: record, isLoading } = useQuery({
    queryKey: ['cost-center', id],
    queryFn: () => api<CostCenter>(`/v1/cost-centers/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) {
      setForm({
        number: record.number,
        name: record.name,
        description: record.description ?? '',
        active: record.active,
        color_code: record.color_code ?? '',
      });
    }
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/cost-centers/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/cost-centers', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cost-centers'] });
      navigate('/cost-centers');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading cost center…" />;

  return (
    <FormPageShell
      title={isEdit ? 'Edit Cost Center' : 'New Cost Center'}
      description="Cost center fields aligned with Asset Essentials (CostCenterNo, CostCenterName, Description, Active, ColorCode)."
      backTo="/cost-centers"
      backLabel="Back to cost centers"
    >
      {isEdit && record?.site_name && (
        <div className="po-summary-bar">
          <div><span>Site</span><strong>{record.site_name}</strong></div>
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!siteId) return;
          const body = {
            number: form.number,
            name: form.name,
            description: form.description || undefined,
            active: form.active,
            color_code: form.color_code || undefined,
            ...(isEdit ? {} : { site_id: siteId }),
          };
          saveMutation.mutate(body);
        }}
      >
        <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
          <div className="form-group">
            <label>Cost Center No</label>
            <input value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="form-group" style={{ gridColumn: '1 / -1' }}>
            <label>Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
          </div>
          <div className="form-group">
            <label>Color Code</label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="color" value={form.color_code || '#64748b'} onChange={(e) => setForm({ ...form, color_code: e.target.value })} />
              <input value={form.color_code} onChange={(e) => setForm({ ...form, color_code: e.target.value })} placeholder="#64748b" />
            </div>
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 28 }}>
              <input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} />
              Active
            </label>
          </div>
        </div>
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/cost-centers')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
