import { useEffect, useMemo, useState } from 'react';
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
import { filterItems } from '../lib/listFilters';
import { api, type Paginated } from '../api';
import {
  ASSET_TASK_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';

interface PMQueueEntry {
  id: string;
  asset_task_id: string;
  due_date: string | null;
  status: string;
}

interface AssetTask {
  id: string;
  asset_id: string;
  task_code: string;
  description: string;
  schedule_type: string;
  due_date: string | null;
  status: string;
  is_active: boolean;
}

interface Asset {
  id: string;
  number: string;
  name: string;
}

const TASK_STATUS_FILTER = {
  key: 'status',
  label: 'Status',
  options: [
    { value: 'ACTIVE', label: 'Active' },
    { value: 'INACTIVE', label: 'Inactive' },
  ],
};

export default function PMPage() {
  return (
    <Routes>
      <Route index element={<PMIndex />} />
      <Route path="tasks/new" element={<AssetTaskForm />} />
      <Route path="tasks/:id/edit" element={<AssetTaskForm />} />
    </Routes>
  );
}

function PMIndex() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [tab, setTab] = useState<'queue' | 'tasks'>('queue');

  const queueFilters = useListFilters();
  const tasksFilters = useListFilters({
    pageSize: 100,
    extra: siteId ? { site_id: siteId } : undefined,
  });

  const { data: queue, isLoading: queueLoading } = useQuery({
    queryKey: ['pm-queue'],
    queryFn: () => api<PMQueueEntry[]>('/v1/pm-queue'),
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['asset-tasks', tasksFilters.queryString],
    queryFn: () => api<AssetTask[]>(`/v1/asset-tasks${tasksFilters.queryString}`),
    enabled: !!siteId,
  });

  const allQueue = queue ?? [];
  const filteredQueue = useMemo(
    () => filterItems(allQueue, queueFilters.search, ['status'], queueFilters.filters),
    [allQueue, queueFilters.search, queueFilters.filters],
  );

  const taskItems = tasks ?? [];
  const tasksTotal = taskItems.length;

  const { data: assets } = useQuery({
    queryKey: ['assets-for-pm'],
    queryFn: () => api<Paginated<Asset>>('/v1/assets?page_size=100'),
  });

  const generateMutation = useMutation({
    mutationFn: () =>
      api('/v1/pm-queue/generate', { method: 'POST', body: JSON.stringify({ lead_time_days: 7 }) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pm-queue'] });
      qc.invalidateQueries({ queryKey: ['work-orders'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/asset-tasks/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['asset-tasks'] });
      qc.invalidateQueries({ queryKey: ['pm-queue'] });
    },
  });

  const assetLabel = (id: string) => {
    const a = assets?.items.find((x) => x.id === id);
    return a ? `${a.number} — ${a.name}` : id.slice(0, 8);
  };

  return (
    <div>
      <PageHeader
        title="Preventive Maintenance"
        description="Schedule asset tasks and generate work orders from the PM queue."
        actions={
          tab === 'tasks' ? (
            <button type="button" className="btn btn-primary" onClick={() => navigate('/pm/tasks/new')}>
              <IconPlus size={16} />
              New Asset Task
            </button>
          ) : (
            <button type="button" className="btn btn-primary" onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
              {generateMutation.isPending ? 'Generating…' : 'Generate Work Orders'}
            </button>
          )
        }
      />

      <div className="tab-bar">
        <button type="button" className={`btn btn-sm ${tab === 'queue' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('queue')}>PM Queue</button>
        <button type="button" className={`btn btn-sm ${tab === 'tasks' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('tasks')}>Asset Tasks</button>
      </div>

      {tab === 'queue' && (
        queueLoading ? <LoadingState label="Loading PM queue…" /> : (
          !queueFilters.hasActive && allQueue.length === 0 ? (
            <div className="table-card">
              <EmptyState title="Queue is empty" description="Generate work orders from due preventive maintenance tasks." />
            </div>
          ) : (
          <div className="table-card">
            <ListToolbar
              search={queueFilters.search}
              onSearchChange={queueFilters.setSearch}
              searchPlaceholder="Search by status…"
              filterValues={queueFilters.filters}
              onFilterChange={queueFilters.setFilter}
              onReset={queueFilters.hasActive ? queueFilters.reset : undefined}
              resultCount={filteredQueue.length}
              totalCount={allQueue.length}
            />
            {queueFilters.hasActive && filteredQueue.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr><th>Task ID</th><th>Due Date</th><th>Status</th></tr>
              </thead>
              <tbody>
                {filteredQueue.map((e) => (
                  <tr key={e.id}>
                    <td><code>{e.asset_task_id.slice(0, 8)}…</code></td>
                    <td>{e.due_date ? new Date(e.due_date).toLocaleDateString() : '—'}</td>
                    <td><span className="badge badge-open">{e.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
          )
        )
      )}

      {tab === 'tasks' && (
        tasksLoading ? <LoadingState label="Loading asset tasks…" /> : (
          !tasksFilters.hasActive && tasksTotal === 0 ? (
            <div className="table-card">
              <EmptyState title="No asset tasks" description="Create PM tasks and link them to assets for scheduled maintenance." />
            </div>
          ) : (
          <div className="table-card">
            <ListToolbar
              search={tasksFilters.search}
              onSearchChange={tasksFilters.setSearch}
              searchPlaceholder="Search asset tasks…"
              filters={[TASK_STATUS_FILTER]}
              filterValues={tasksFilters.filters}
              onFilterChange={tasksFilters.setFilter}
              onReset={tasksFilters.hasActive ? tasksFilters.reset : undefined}
              resultCount={taskItems.length}
              totalCount={tasksTotal}
            />
            {tasksFilters.hasActive && taskItems.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Description</th>
                  <th>Asset</th>
                  <th>Schedule</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {taskItems.map((t) => (
                  <tr key={t.id}>
                    <td><code>{t.task_code}</code></td>
                    <td>{t.description}</td>
                    <td>{assetLabel(t.asset_id)}</td>
                    <td>{t.schedule_type}</td>
                    <td>{t.status}</td>
                    <RowActions
                      onEdit={() => navigate(`/pm/tasks/${t.id}/edit`)}
                      onDelete={() => confirm(`Delete task ${t.task_code}?`) && deleteMutation.mutate(t.id)}
                    />
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
          )
        )
      )}
    </div>
  );
}

function AssetTaskForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [assetId, setAssetId] = useState('');
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(ASSET_TASK_FIELDS),
    schedule_type: 'TIME',
    can_detach: true,
    is_active: true,
    status: 'ACTIVE',
  }));

  const { data: assets } = useQuery({
    queryKey: ['assets-for-pm'],
    queryFn: () => api<Paginated<Asset>>('/v1/assets?page_size=100'),
  });

  const { data: record, isLoading } = useQuery({
    queryKey: ['asset-task', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/asset-tasks/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) setForm(recordToForm(record, ASSET_TASK_FIELDS));
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/asset-tasks/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/asset-tasks', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['asset-tasks'] });
      qc.invalidateQueries({ queryKey: ['pm-queue'] });
      navigate('/pm');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading asset task…" />;

  return (
    <FormPageShell
      title={isEdit ? 'Edit Asset Task' : 'New Asset Task'}
      backTo="/pm"
      backLabel="Back to preventive maintenance"
    >
      <form onSubmit={(e) => {
        e.preventDefault();
        saveMutation.mutate(formToPayload(form, ASSET_TASK_FIELDS, isEdit ? {} : { asset_id: assetId }));
      }}>
        {!isEdit && (
          <div className="form-group">
            <label>Asset</label>
            <select value={assetId} onChange={(e) => setAssetId(e.target.value)} required>
              <option value="">Select asset…</option>
              {(assets?.items ?? []).map((a) => (
                <option key={a.id} value={a.id}>{a.number} — {a.name}</option>
              ))}
            </select>
          </div>
        )}
        <FwFormFields fields={ASSET_TASK_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/pm')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
