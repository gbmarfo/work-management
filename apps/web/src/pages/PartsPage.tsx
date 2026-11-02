import { useEffect, useState } from 'react';
import { Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import RowActions from '../components/RowActions';
import FwFormFields from '../components/FwFormFields';
import FormPageShell, { FormActions } from '../components/FormPageShell';
import LoadingState from '../components/LoadingState';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ListToolbar from '../components/ListToolbar';
import { IconPlus } from '../components/icons';
import { useDefaultSiteId } from '../hooks/useSites';
import { useListFilters } from '../hooks/useListFilters';
import { PART_STATUS_FILTER } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import {
  PART_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';

interface Part {
  id: string;
  part_number: string;
  description: string;
  quantity_on_hand: number;
  reorder_point: number;
  unit_cost: number | null;
  is_critical: boolean;
}

export default function PartsPage() {
  return (
    <Routes>
      <Route index element={<PartsList />} />
      <Route path="new" element={<PartForm />} />
      <Route path=":id/edit" element={<PartForm />} />
    </Routes>
  );
}

function PartsList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['parts', queryString],
    queryFn: () => api<Paginated<Part>>(`/v1/parts${queryString}`),
  });

  const items = data?.items ?? [];
  const total = data?.total_items ?? 0;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/parts/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['parts'] }),
  });

  return (
    <div>
      <PageHeader
        title="Parts Inventory"
        description="Manage spare parts, stock levels, and reorder thresholds."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/parts/new')}>
            <IconPlus size={16} />
            New Part
          </button>
        }
      />

      {isLoading ? (
        <LoadingState label="Loading parts…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No parts in inventory" description="Add parts to track stock and link them to work orders." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search parts…"
            filters={[PART_STATUS_FILTER]}
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
                <th>Part Number</th>
                <th>Description</th>
                <th>On Hand</th>
                <th>Reorder Point</th>
                <th>Unit Cost</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td><code>{p.part_number}</code></td>
                  <td>{p.description}</td>
                  <td>
                    {p.quantity_on_hand}
                    {p.quantity_on_hand <= p.reorder_point && (
                      <span className="badge badge-critical" style={{ marginLeft: 8 }}>Low</span>
                    )}
                  </td>
                  <td>{p.reorder_point}</td>
                  <td>{p.unit_cost != null ? `$${p.unit_cost.toFixed(2)}` : '—'}</td>
                  <RowActions
                    onEdit={() => navigate(`/parts/${p.id}/edit`)}
                    onDelete={() => confirm(`Delete ${p.part_number}?`) && deleteMutation.mutate(p.id)}
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

function PartForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(PART_FIELDS),
    status: 'ACTIVE',
  }));

  const { data: record, isLoading } = useQuery({
    queryKey: ['part', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/parts/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) setForm(recordToForm(record, PART_FIELDS));
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/parts/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/parts', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['parts'] });
      navigate('/parts');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading part…" />;

  return (
    <FormPageShell title={isEdit ? 'Edit Part' : 'New Part'} backTo="/parts" backLabel="Back to parts">
      <form onSubmit={(e) => { e.preventDefault(); if (!siteId) return; saveMutation.mutate(formToPayload(form, PART_FIELDS, isEdit ? {} : { site_id: siteId })); }}>
        <FwFormFields fields={PART_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/parts')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
