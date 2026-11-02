import { useMemo, useState } from 'react';
import { Route, Routes, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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

interface MeterReading {
  id: string;
  meter_id: string;
  reading: number;
  rollover: boolean;
  recorded_at: string;
  recorded_by: string | null;
  asset_id: string;
  asset_number: string;
  asset_name: string;
  meter_group_id: string;
  meter_group_code: string;
  meter_group_name: string;
  unit_of_measure: string | null;
}

interface MeterGroup {
  id: string;
  site_id: string;
  code: string;
  name: string;
  unit_of_measure: string | null;
}

interface MeterDetail {
  id: string;
  asset_id: string;
  meter_group_id: string;
  current_reading: number;
  rollover_count: number;
  rollover_point: number | null;
  asset_number: string;
  asset_name: string;
  meter_group_code: string;
  meter_group_name: string;
  unit_of_measure: string | null;
}

interface Asset {
  id: string;
  number: string;
  name: string;
}

const emptyReadingForm = {
  asset_id: '',
  meter_group_id: '',
  reading: '',
  rollover: false,
};

const emptyGroupForm = {
  code: '',
  name: '',
  unit_of_measure: '',
};

export default function MeterReadingsPage() {
  return (
    <Routes>
      <Route index element={<MeterReadingsIndex />} />
      <Route path="record" element={<RecordReadingForm />} />
      <Route path="groups/new" element={<MeterGroupForm />} />
    </Routes>
  );
}

function MeterReadingsIndex() {
  const navigate = useNavigate();
  const siteId = useDefaultSiteId();
  const [tab, setTab] = useState<'readings' | 'groups' | 'meters'>('readings');
  const readingsFilters = useListFilters();
  const metersFilters = useListFilters();
  const groupsFilters = useListFilters();

  const siteQuery = siteId ? `?site_id=${siteId}` : '';

  const { data: readings, isLoading: readingsLoading } = useQuery({
    queryKey: ['meter-readings', siteId],
    queryFn: () => api<MeterReading[]>(`/v1/meter-readings${siteQuery}`),
    enabled: !!siteId,
  });

  const { data: groups, isLoading: groupsLoading } = useQuery({
    queryKey: ['meter-groups', siteId],
    queryFn: () => api<MeterGroup[]>(`/v1/meter-readings/groups${siteQuery}`),
    enabled: !!siteId,
  });

  const { data: meters, isLoading: metersLoading } = useQuery({
    queryKey: ['meters', siteId],
    queryFn: () => api<MeterDetail[]>(`/v1/meter-readings/meters${siteQuery}`),
    enabled: !!siteId,
  });

  const allReadings = readings ?? [];
  const allMeters = meters ?? [];
  const allGroups = groups ?? [];

  const filteredReadings = useMemo(
    () => filterItems(allReadings, readingsFilters.search, ['asset_number', 'asset_name', 'meter_group_name', 'recorded_by'], readingsFilters.filters),
    [allReadings, readingsFilters.search, readingsFilters.filters],
  );

  const filteredMeters = useMemo(
    () => filterItems(allMeters, metersFilters.search, ['asset_number', 'asset_name', 'meter_group_code'], metersFilters.filters),
    [allMeters, metersFilters.search, metersFilters.filters],
  );

  const filteredGroups = useMemo(
    () => filterItems(allGroups, groupsFilters.search, ['code', 'name'], groupsFilters.filters),
    [allGroups, groupsFilters.search, groupsFilters.filters],
  );

  const formatReading = (value: number, uom: string | null) =>
    uom ? `${value.toLocaleString()} ${uom}` : value.toLocaleString();

  return (
    <div>
      <PageHeader
        title="Meter Readings"
        description="Record runtime and usage meters on assets to trigger meter-based preventive maintenance."
        actions={
          tab === 'groups' ? (
            <button type="button" className="btn btn-primary" onClick={() => navigate('/meter-readings/groups/new')}>
              <IconPlus size={16} />
              New Meter Group
            </button>
          ) : (
            <button type="button" className="btn btn-primary" onClick={() => navigate('/meter-readings/record')}>
              <IconPlus size={16} />
              Record Reading
            </button>
          )
        }
      />

      <div className="tab-bar">
        <button type="button" className={`btn btn-sm ${tab === 'readings' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('readings')}>
          Reading History
        </button>
        <button type="button" className={`btn btn-sm ${tab === 'meters' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('meters')}>
          Asset Meters
        </button>
        <button type="button" className={`btn btn-sm ${tab === 'groups' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('groups')}>
          Meter Groups
        </button>
      </div>

      {tab === 'readings' && (
        readingsLoading ? (
          <LoadingState label="Loading meter readings…" />
        ) : !readingsFilters.hasActive && allReadings.length === 0 ? (
          <div className="table-card">
            <EmptyState title="No meter readings" description="Record a reading for an asset and meter group to start tracking usage." />
          </div>
        ) : (
          <div className="table-card">
            <ListToolbar
              search={readingsFilters.search}
              onSearchChange={readingsFilters.setSearch}
              searchPlaceholder="Search readings…"
              filterValues={readingsFilters.filters}
              onFilterChange={readingsFilters.setFilter}
              onReset={readingsFilters.hasActive ? readingsFilters.reset : undefined}
              resultCount={filteredReadings.length}
              totalCount={allReadings.length}
            />
            {readingsFilters.hasActive && filteredReadings.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr>
                  <th>Recorded</th>
                  <th>Asset</th>
                  <th>Meter Group</th>
                  <th>Reading</th>
                  <th>Rollover</th>
                  <th>Recorded By</th>
                </tr>
              </thead>
              <tbody>
                {filteredReadings.map((r) => (
                  <tr key={r.id}>
                    <td>{new Date(r.recorded_at).toLocaleString()}</td>
                    <td>
                      <code>{r.asset_number}</code>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.asset_name}</div>
                    </td>
                    <td>
                      <code>{r.meter_group_code}</code>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.meter_group_name}</div>
                    </td>
                    <td>{formatReading(r.reading, r.unit_of_measure)}</td>
                    <td>{r.rollover ? <span className="badge badge-warning">Yes</span> : '—'}</td>
                    <td>{r.recorded_by ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
        )
      )}

      {tab === 'meters' && (
        metersLoading ? (
          <LoadingState label="Loading asset meters…" />
        ) : !metersFilters.hasActive && allMeters.length === 0 ? (
          <div className="table-card">
            <EmptyState title="No asset meters" description="Meters are created automatically when you record the first reading for an asset and meter group." />
          </div>
        ) : (
          <div className="table-card">
            <ListToolbar
              search={metersFilters.search}
              onSearchChange={metersFilters.setSearch}
              searchPlaceholder="Search meters…"
              filterValues={metersFilters.filters}
              onFilterChange={metersFilters.setFilter}
              onReset={metersFilters.hasActive ? metersFilters.reset : undefined}
              resultCount={filteredMeters.length}
              totalCount={allMeters.length}
            />
            {metersFilters.hasActive && filteredMeters.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Meter Group</th>
                  <th>Current Reading</th>
                  <th>Rollover Count</th>
                  <th>Rollover Point</th>
                </tr>
              </thead>
              <tbody>
                {filteredMeters.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <code>{m.asset_number}</code>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{m.asset_name}</div>
                    </td>
                    <td>
                      <code>{m.meter_group_code}</code>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{m.meter_group_name}</div>
                    </td>
                    <td>{formatReading(m.current_reading, m.unit_of_measure)}</td>
                    <td>{m.rollover_count}</td>
                    <td>{m.rollover_point != null ? formatReading(m.rollover_point, m.unit_of_measure) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
        )
      )}

      {tab === 'groups' && (
        groupsLoading ? (
          <LoadingState label="Loading meter groups…" />
        ) : !groupsFilters.hasActive && allGroups.length === 0 ? (
          <div className="table-card">
            <EmptyState title="No meter groups" description="Define meter groups such as run hours, cycles, or mileage before recording readings." />
          </div>
        ) : (
          <div className="table-card">
            <ListToolbar
              search={groupsFilters.search}
              onSearchChange={groupsFilters.setSearch}
              searchPlaceholder="Search groups…"
              filterValues={groupsFilters.filters}
              onFilterChange={groupsFilters.setFilter}
              onReset={groupsFilters.hasActive ? groupsFilters.reset : undefined}
              resultCount={filteredGroups.length}
              totalCount={allGroups.length}
            />
            {groupsFilters.hasActive && filteredGroups.length === 0 ? (
              <EmptyState title="No results match your search or filters." />
            ) : (
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Unit of Measure</th>
                </tr>
              </thead>
              <tbody>
                {filteredGroups.map((g) => (
                  <tr key={g.id}>
                    <td><code>{g.code}</code></td>
                    <td>{g.name}</td>
                    <td>{g.unit_of_measure ?? '—'}</td>
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

function RecordReadingForm() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState(emptyReadingForm);

  const siteQuery = siteId ? `?site_id=${siteId}` : '';

  const { data: groups } = useQuery({
    queryKey: ['meter-groups', siteId],
    queryFn: () => api<MeterGroup[]>(`/v1/meter-readings/groups${siteQuery}`),
    enabled: !!siteId,
  });

  const { data: assets } = useQuery({
    queryKey: ['assets-for-meters'],
    queryFn: () => api<Paginated<Asset>>('/v1/assets?page_size=100'),
  });

  const recordMutation = useMutation({
    mutationFn: (body: object) =>
      api('/v1/meter-readings/batch/by-asset', { method: 'PUT', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['meter-readings'] });
      qc.invalidateQueries({ queryKey: ['meters'] });
      qc.invalidateQueries({ queryKey: ['pm-queue'] });
      navigate('/meter-readings');
    },
  });

  return (
    <FormPageShell title="Record Meter Reading" backTo="/meter-readings" backLabel="Back to meter readings">
      <form onSubmit={(e) => {
        e.preventDefault();
        recordMutation.mutate({
          asset_id: form.asset_id,
          meter_group_id: form.meter_group_id,
          reading: Number(form.reading),
          rollover: form.rollover,
        });
      }}>
        <div className="form-group">
          <label>Asset</label>
          <select
            value={form.asset_id}
            onChange={(e) => setForm({ ...form, asset_id: e.target.value })}
            required
          >
            <option value="">Select asset…</option>
            {(assets?.items ?? []).map((a) => (
              <option key={a.id} value={a.id}>{a.number} — {a.name}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Meter Group</label>
          <select
            value={form.meter_group_id}
            onChange={(e) => setForm({ ...form, meter_group_id: e.target.value })}
            required
          >
            <option value="">Select meter group…</option>
            {(groups ?? []).map((g) => (
              <option key={g.id} value={g.id}>{g.code} — {g.name}{g.unit_of_measure ? ` (${g.unit_of_measure})` : ''}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Reading Value</label>
          <input
            type="number"
            step="any"
            min="0"
            value={form.reading}
            onChange={(e) => setForm({ ...form, reading: e.target.value })}
            required
          />
        </div>
        <label className="form-check">
          <input
            type="checkbox"
            checked={form.rollover}
            onChange={(e) => setForm({ ...form, rollover: e.target.checked })}
          />
          Meter rollover (counter reset)
        </label>
        {recordMutation.isError && (
          <div className="error">{(recordMutation.error as Error).message}</div>
        )}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/meter-readings')} pending={recordMutation.isPending} submitLabel="Save Reading" />
        </div>
      </form>
    </FormPageShell>
  );
}

function MeterGroupForm() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState(emptyGroupForm);

  const groupMutation = useMutation({
    mutationFn: (body: object) =>
      api('/v1/meter-readings/groups', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['meter-groups'] });
      navigate('/meter-readings');
    },
  });

  return (
    <FormPageShell title="New Meter Group" backTo="/meter-readings" backLabel="Back to meter readings">
      <form onSubmit={(e) => {
        e.preventDefault();
        if (!siteId) return;
        groupMutation.mutate({
          site_id: siteId,
          code: form.code,
          name: form.name,
          unit_of_measure: form.unit_of_measure || null,
        });
      }}>
        <div className="form-group">
          <label>Code</label>
          <input
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
            placeholder="RUN-HRS"
            required
          />
        </div>
        <div className="form-group">
          <label>Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Run Hours"
            required
          />
        </div>
        <div className="form-group">
          <label>Unit of Measure</label>
          <input
            value={form.unit_of_measure}
            onChange={(e) => setForm({ ...form, unit_of_measure: e.target.value })}
            placeholder="hours, miles, cycles…"
          />
        </div>
        {groupMutation.isError && (
          <div className="error">{(groupMutation.error as Error).message}</div>
        )}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/meter-readings')} pending={groupMutation.isPending} submitLabel="Create Group" />
        </div>
      </form>
    </FormPageShell>
  );
}
