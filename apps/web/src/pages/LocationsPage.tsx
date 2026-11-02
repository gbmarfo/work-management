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
import { CRITICALITY_FILTER } from '../lib/listFilters';
import { api } from '../api';

interface Location {
  id: string;
  number: string;
  name: string;
  criticality: string | null;
}

const emptyForm = { number: '', name: '', criticality: 'MEDIUM' };

export default function LocationsPage() {
  return (
    <Routes>
      <Route index element={<LocationsList />} />
      <Route path="new" element={<LocationForm />} />
      <Route path=":id/edit" element={<LocationForm />} />
    </Routes>
  );
}

function LocationsList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
    extra: siteId ? { site_id: siteId } : undefined,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['locations', queryString],
    queryFn: () => api<Location[]>(`/v1/locations${queryString}`),
    enabled: !!siteId,
  });

  const items = data ?? [];
  const total = items.length;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/locations/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['locations'] }),
  });

  return (
    <div>
      <PageHeader
        title="Locations"
        description="Define site locations for assets, work orders, and inventory storage."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/locations/new')}>
            <IconPlus size={16} />
            New Location
          </button>
        }
      />

      {isLoading ? (
        <LoadingState label="Loading locations…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No locations" description="Add locations to organize assets and work by building or area." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search locations…"
            filters={[CRITICALITY_FILTER]}
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
                <th>Criticality</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((loc) => (
                <tr key={loc.id}>
                  <td><code>{loc.number}</code></td>
                  <td>{loc.name}</td>
                  <td>{loc.criticality ?? '—'}</td>
                  <RowActions
                    onEdit={() => navigate(`/locations/${loc.id}/edit`)}
                    onDelete={() => confirm(`Delete ${loc.name}?`) && deleteMutation.mutate(loc.id)}
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

function LocationForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState(emptyForm);

  const { data: locations, isLoading } = useQuery({
    queryKey: ['locations', siteId],
    queryFn: () => api<Location[]>(`/v1/locations${siteId ? `?site_id=${siteId}` : ''}`),
    enabled: isEdit && !!siteId,
  });

  useEffect(() => {
    if (isEdit && locations) {
      const loc = locations.find((l) => l.id === id);
      if (loc) {
        setForm({ number: loc.number, name: loc.name, criticality: loc.criticality ?? 'MEDIUM' });
      }
    }
  }, [isEdit, locations, id]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/locations/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/locations', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['locations'] });
      navigate('/locations');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading location…" />;

  return (
    <FormPageShell title={isEdit ? 'Edit Location' : 'New Location'} backTo="/locations" backLabel="Back to locations">
      <form onSubmit={(e) => {
        e.preventDefault();
        if (!siteId) return;
        if (isEdit) {
          saveMutation.mutate({ number: form.number, name: form.name, criticality: form.criticality });
        } else {
          saveMutation.mutate({ site_id: siteId, number: form.number, name: form.name, criticality: form.criticality });
        }
      }}>
        <div className="form-group">
          <label>Location Number</label>
          <input value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} required />
        </div>
        <div className="form-group">
          <label>Name</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div className="form-group">
          <label>Criticality</label>
          <select value={form.criticality} onChange={(e) => setForm({ ...form, criticality: e.target.value })}>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </div>
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/locations')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
