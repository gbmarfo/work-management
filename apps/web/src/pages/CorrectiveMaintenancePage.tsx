import { useEffect, useMemo, useState } from 'react';
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
import { PRIORITY_FILTER, SR_STATUS_FILTER, WO_STATUS_FILTER, filterItems } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import {
  CM_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';

interface CMWorkOrder {
  id: string;
  number: string;
  status: string;
  title: string;
  priority: string | null;
  date_due: string | null;
  problem: string | null;
  waiting_for_parts: boolean;
  asset_id: string | null;
}

interface ServiceRequest {
  id: string;
  number: string;
  status: string;
  problem: string;
  priority: string | null;
  requested_by: string | null;
  work_order_id: string | null;
}

function statusBadge(status: string) {
  if (status === 'COMPLETED') return 'badge-completed';
  if (status === 'IN_PROGRESS') return 'badge-progress';
  return 'badge-open';
}

export default function CorrectiveMaintenancePage() {
  return (
    <Routes>
      <Route index element={<CorrectiveMaintenanceList />} />
      <Route path="new" element={<CMForm />} />
      <Route path=":id/edit" element={<CMForm />} />
    </Routes>
  );
}

function CorrectiveMaintenanceList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [tab, setTab] = useState<'jobs' | 'requests'>('jobs');

  const jobsFilters = useListFilters({
    pageSize: 100,
    extra: siteId ? { type: 'CORRECTIVE', site_id: siteId } : { type: 'CORRECTIVE' },
  });

  const requestsFilters = useListFilters({ pageSize: 100 });

  const { data, isLoading } = useQuery({
    queryKey: ['corrective-maintenance', jobsFilters.queryString],
    queryFn: () => api<Paginated<CMWorkOrder>>(`/v1/work-orders${jobsFilters.queryString}`),
    enabled: !!siteId,
  });

  const { data: serviceRequests, isLoading: srLoading } = useQuery({
    queryKey: ['cm-service-requests', siteId],
    queryFn: () => api<Paginated<ServiceRequest>>(`/v1/service-requests?page_size=100${siteId ? `&site_id=${siteId}` : ''}`),
    enabled: !!siteId && tab === 'requests',
  });

  const jobs = data?.items ?? [];
  const jobsTotal = data?.total_items ?? 0;

  const allRequests = serviceRequests?.items ?? [];
  const filteredRequests = useMemo(
    () => filterItems(
      allRequests,
      requestsFilters.search,
      ['number', 'problem', 'requested_by'],
      requestsFilters.filters,
    ),
    [allRequests, requestsFilters.search, requestsFilters.filters],
  );

  const stats = useMemo(() => ({
    open: jobs.filter((j) => j.status === 'OPEN').length,
    inProgress: jobs.filter((j) => j.status === 'IN_PROGRESS').length,
    waitingParts: jobs.filter((j) => j.waiting_for_parts).length,
  }), [jobs]);

  const pendingRequests = (serviceRequests?.items ?? []).filter(
    (sr) => sr.status === 'OPEN' && !sr.work_order_id,
  );

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/work-orders/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['corrective-maintenance'] });
      qc.invalidateQueries({ queryKey: ['work-orders'] });
    },
  });

  const completeMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/work-orders/${id}/complete`, { method: 'PUT' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['corrective-maintenance'] });
      qc.invalidateQueries({ queryKey: ['work-orders'] });
    },
  });

  const convertMutation = useMutation({
    mutationFn: (srId: string) => api(`/v1/service-requests/${srId}/convert-to-work-order`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['corrective-maintenance'] });
      qc.invalidateQueries({ queryKey: ['cm-service-requests'] });
      qc.invalidateQueries({ queryKey: ['service-requests'] });
      qc.invalidateQueries({ queryKey: ['work-orders'] });
      setTab('jobs');
    },
  });

  return (
    <div>
      <PageHeader
        title="Corrective Maintenance"
        description="Manage breakdown and repair work orders — failures, faults, and reactive maintenance."
        actions={
          tab === 'jobs' ? (
            <button type="button" className="btn btn-primary" onClick={() => navigate('/corrective-maintenance/new')}>
              <IconPlus size={16} />
              New CM Job
            </button>
          ) : undefined
        }
      />

      <div className="card-grid" style={{ marginBottom: '1.25rem' }}>
        <div className="stat-card stat-card--danger">
          <div className="label">Open CM Jobs</div>
          <div className="value">{stats.open}</div>
          <div className="hint">Awaiting assignment or start</div>
        </div>
        <div className="stat-card stat-card--warning">
          <div className="label">In Progress</div>
          <div className="value">{stats.inProgress}</div>
          <div className="hint">Active corrective work</div>
        </div>
        <div className="stat-card stat-card--info">
          <div className="label">Waiting for Parts</div>
          <div className="value">{stats.waitingParts}</div>
          <div className="hint">Jobs on hold</div>
        </div>
        <div className="stat-card stat-card--success">
          <div className="label">Pending Requests</div>
          <div className="value">{pendingRequests.length}</div>
          <div className="hint">Service requests to convert</div>
        </div>
      </div>

      <div className="tab-bar">
        <button type="button" className={`btn btn-sm ${tab === 'jobs' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('jobs')}>
          CM Work Orders
        </button>
        <button type="button" className={`btn btn-sm ${tab === 'requests' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('requests')}>
          Incoming Requests
        </button>
      </div>

      {tab === 'jobs' && (
        isLoading ? (
          <LoadingState label="Loading corrective maintenance jobs…" />
        ) : !jobsFilters.hasActive && jobsTotal === 0 ? (
          <div className="table-card">
            <EmptyState
              title="No corrective maintenance jobs"
              description="Create a CM job for equipment failures, or convert an incoming service request."
            />
          </div>
        ) : (
          <div className="table-card">
            <ListToolbar
              search={jobsFilters.search}
              onSearchChange={jobsFilters.setSearch}
              searchPlaceholder="Search CM jobs…"
              filters={[WO_STATUS_FILTER, PRIORITY_FILTER]}
              filterValues={jobsFilters.filters}
              onFilterChange={jobsFilters.setFilter}
              onReset={jobsFilters.hasActive ? jobsFilters.reset : undefined}
              resultCount={jobs.length}
              totalCount={jobsTotal}
            />
            {jobsFilters.hasActive && jobs.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr>
                  <th>CM Number</th>
                  <th>Problem / Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Due</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((wo) => (
                  <tr key={wo.id}>
                    <td><code>{wo.number}</code></td>
                    <td>
                      <div>{wo.title}</div>
                      {wo.problem && (
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
                          {wo.problem.slice(0, 80)}{wo.problem.length > 80 ? '…' : ''}
                        </div>
                      )}
                      {wo.waiting_for_parts && (
                        <span className="badge badge-warning" style={{ marginTop: 4 }}>Waiting for Parts</span>
                      )}
                    </td>
                    <td><span className={`badge ${statusBadge(wo.status)}`}>{wo.status}</span></td>
                    <td>{wo.priority ?? '—'}</td>
                    <td>{wo.date_due ? new Date(wo.date_due).toLocaleDateString() : '—'}</td>
                    <td className="actions-cell">
                      <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate(`/corrective-maintenance/${wo.id}/edit`)}>Edit</button>
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
        )
      )}

      {tab === 'requests' && (
        srLoading ? (
          <LoadingState label="Loading service requests…" />
        ) : !requestsFilters.hasActive && allRequests.length === 0 ? (
          <div className="table-card">
            <EmptyState title="No pending requests" description="Open service requests ready for CM conversion will appear here." />
          </div>
        ) : (
          <div className="table-card">
            <ListToolbar
              search={requestsFilters.search}
              onSearchChange={requestsFilters.setSearch}
              searchPlaceholder="Search requests…"
              filters={[SR_STATUS_FILTER, PRIORITY_FILTER]}
              filterValues={requestsFilters.filters}
              onFilterChange={requestsFilters.setFilter}
              onReset={requestsFilters.hasActive ? requestsFilters.reset : undefined}
              resultCount={filteredRequests.length}
              totalCount={allRequests.length}
            />
            {requestsFilters.hasActive && filteredRequests.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr>
                  <th>SR Number</th>
                  <th>Problem</th>
                  <th>Priority</th>
                  <th>Requester</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequests.map((sr) => (
                  <tr key={sr.id}>
                    <td><code>{sr.number}</code></td>
                    <td>{sr.problem.slice(0, 100)}{sr.problem.length > 100 ? '…' : ''}</td>
                    <td>{sr.priority ?? '—'}</td>
                    <td>{sr.requested_by ?? '—'}</td>
                    <td className="actions-cell">
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={() => convertMutation.mutate(sr.id)}
                        disabled={convertMutation.isPending}
                      >
                        Create CM Job
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
        )
      )}
    </div>
  );
}

function CMForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(CM_FIELDS),
    status: 'OPEN',
    priority: 'MEDIUM',
    title: '',
    problem: '',
  }));

  const { data: record, isLoading } = useQuery({
    queryKey: ['cm-work-order', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/work-orders/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) setForm(recordToForm(record, CM_FIELDS));
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/work-orders/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/work-orders', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['corrective-maintenance'] });
      qc.invalidateQueries({ queryKey: ['work-orders'] });
      qc.invalidateQueries({ queryKey: ['report-summary'] });
      navigate('/corrective-maintenance');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading CM job…" />;

  return (
    <FormPageShell
      title={isEdit ? 'Edit CM Job' : 'New Corrective Maintenance Job'}
      backTo="/corrective-maintenance"
      backLabel="Back to corrective maintenance"
    >
      <form onSubmit={(e) => {
        e.preventDefault();
        if (!siteId) return;
        saveMutation.mutate(formToPayload(form, CM_FIELDS, isEdit ? {} : { site_id: siteId, type: 'CORRECTIVE' }));
      }}>
        <FwFormFields fields={CM_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/corrective-maintenance')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
