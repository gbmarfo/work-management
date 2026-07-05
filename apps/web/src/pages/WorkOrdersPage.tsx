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
import { PRIORITY_FILTER, WO_STATUS_FILTER, WO_TYPE_FILTER } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import { WORK_ORDER_FIELDS, emptyFormFromFields, formToPayload, recordToForm } from '../lib/faciliworksFields';
import WorkOrderTasks from '../components/WorkOrderTasks';

interface WorkOrder {
  id: string;
  number: string;
  type: string;
  status: string;
  title: string;
  priority: string | null;
  date_due: string | null;
}

function statusBadge(status: string) {
  if (status === 'COMPLETED') return 'badge-completed';
  if (status === 'IN_PROGRESS') return 'badge-progress';
  return 'badge-open';
}

export default function WorkOrdersPage() {
  return (
    <Routes>
      <Route index element={<WorkOrdersList />} />
      <Route path="new" element={<WorkOrderForm />} />
      <Route path=":id/edit" element={<WorkOrderForm />} />
    </Routes>
  );
}

function WorkOrdersList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['work-orders', queryString],
    queryFn: () => api<Paginated<WorkOrder>>(`/v1/work-orders${queryString}`),
  });

  const items = data?.items ?? [];
  const total = data?.total_items ?? 0;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/work-orders/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['work-orders'] }),
  });
  const completeMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/work-orders/${id}/complete`, { method: 'PUT' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['work-orders'] }),
  });

  return (
    <div>
      <PageHeader
        title="Work Orders"
        description="Track corrective, preventive, and general maintenance work."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/work-orders/new')}>
            <IconPlus size={16} />
            New Work Order
          </button>
        }
      />
      {isLoading ? (
        <LoadingState label="Loading work orders…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card"><EmptyState title="No work orders" description="Create a work order to assign and track maintenance tasks." /></div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search work orders…"
            filters={[WO_STATUS_FILTER, WO_TYPE_FILTER, PRIORITY_FILTER]}
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
              <tr><th>Number</th><th>Type</th><th>Title</th><th>Status</th><th>Priority</th><th>Due</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {items.map((wo) => (
                <tr key={wo.id}>
                  <td><code>{wo.number}</code></td>
                  <td>{wo.type}</td>
                  <td>{wo.title}</td>
                  <td><span className={`badge ${statusBadge(wo.status)}`}>{wo.status}</span></td>
                  <td>{wo.priority ?? '—'}</td>
                  <td>{wo.date_due ? new Date(wo.date_due).toLocaleDateString() : '—'}</td>
                  <td className="actions-cell">
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate(`/work-orders/${wo.id}/edit`)}>Edit</button>
                    {wo.status !== 'COMPLETED' && (
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => completeMutation.mutate(wo.id)}>Complete</button>
                    )}
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => confirm(`Delete ${wo.number}?`) && deleteMutation.mutate(wo.id)}>Delete</button>
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

function WorkOrderForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(WORK_ORDER_FIELDS),
    type: 'CORRECTIVE',
    status: 'OPEN',
    priority: 'MEDIUM',
  }));

  const { data: record, isLoading } = useQuery({
    queryKey: ['work-order', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/work-orders/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) setForm(recordToForm(record, WORK_ORDER_FIELDS));
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: async (body: object) => {
      if (isEdit) {
        await api(`/v1/work-orders/${id}`, { method: 'PUT', body: JSON.stringify(body) });
        return undefined;
      }
      return api<{ id: string }>('/v1/work-orders', { method: 'POST', body: JSON.stringify(body) });
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['work-orders'] });
      if (!isEdit && result?.id) {
        navigate(`/work-orders/${result.id}/edit`);
      } else {
        navigate('/work-orders');
      }
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading work order…" />;

  return (
    <FormPageShell title={isEdit ? 'Edit Work Order' : 'New Work Order'} backTo="/work-orders" backLabel="Back to work orders">
      <form onSubmit={(e) => { e.preventDefault(); if (!siteId) return; saveMutation.mutate(formToPayload(form, WORK_ORDER_FIELDS, isEdit ? {} : { site_id: siteId })); }}>
        <FwFormFields fields={WORK_ORDER_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        {isEdit && id && <WorkOrderTasks workOrderId={id} />}
        {!isEdit && (
          <p className="form-hint">After saving, you can add related tasks on the work order edit page.</p>
        )}
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/work-orders')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
