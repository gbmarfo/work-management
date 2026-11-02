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
import { PRIORITY_FILTER, SR_STATUS_FILTER } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import {
  SERVICE_REQUEST_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';

interface ServiceRequest {
  id: string;
  number: string;
  status: string;
  problem: string;
  requested_by: string | null;
  priority: string | null;
}

export default function ServiceRequestsPage() {
  return (
    <Routes>
      <Route index element={<ServiceRequestsList />} />
      <Route path="new" element={<ServiceRequestForm />} />
      <Route path=":id/edit" element={<ServiceRequestForm />} />
    </Routes>
  );
}

function ServiceRequestsList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['service-requests', queryString],
    queryFn: () => api<Paginated<ServiceRequest>>(`/v1/service-requests${queryString}`),
  });

  const items = data?.items ?? [];
  const total = data?.total_items ?? 0;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/service-requests/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['service-requests'] }),
  });

  const convertMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/service-requests/${id}/convert-to-work-order`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['service-requests'] });
      qc.invalidateQueries({ queryKey: ['work-orders'] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Service Requests"
        description="Intake and triage maintenance requests from building occupants and staff."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/service-requests/new')}>
            <IconPlus size={16} />
            New Request
          </button>
        }
      />

      {isLoading ? (
        <LoadingState label="Loading requests…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No service requests" description="Submit a request to report a maintenance issue or facility need." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search service requests…"
            filters={[SR_STATUS_FILTER, PRIORITY_FILTER]}
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
                <th>Problem</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Requester</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((sr) => (
                <tr key={sr.id}>
                  <td><code>{sr.number}</code></td>
                  <td>{sr.problem.slice(0, 80)}{sr.problem.length > 80 ? '…' : ''}</td>
                  <td><span className="badge badge-open">{sr.status}</span></td>
                  <td>{sr.priority ?? '—'}</td>
                  <td>{sr.requested_by ?? '—'}</td>
                  <td className="actions-cell">
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate(`/service-requests/${sr.id}/edit`)}>Edit</button>
                    {!sr.status.includes('CLOSED') && (
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => convertMutation.mutate(sr.id)}>To WO</button>
                    )}
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => confirm(`Delete ${sr.number}?`) && deleteMutation.mutate(sr.id)}>Delete</button>
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

function ServiceRequestForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(SERVICE_REQUEST_FIELDS),
    priority: 'MEDIUM',
    status: 'OPEN',
  }));

  const { data: record, isLoading } = useQuery({
    queryKey: ['service-request', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/service-requests/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) setForm(recordToForm(record, SERVICE_REQUEST_FIELDS));
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/service-requests/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/service-requests', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['service-requests'] });
      navigate('/service-requests');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading service request…" />;

  return (
    <FormPageShell title={isEdit ? 'Edit Service Request' : 'New Service Request'} backTo="/service-requests" backLabel="Back to service requests">
      <form onSubmit={(e) => { e.preventDefault(); if (!siteId) return; saveMutation.mutate(formToPayload(form, SERVICE_REQUEST_FIELDS, isEdit ? {} : { site_id: siteId })); }}>
        <FwFormFields fields={SERVICE_REQUEST_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/service-requests')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
