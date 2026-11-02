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
import { PERSONNEL_TYPE_FILTER } from '../lib/listFilters';
import { api } from '../api';
import {
  PERSONNEL_FIELDS,
  emptyFormFromFields,
  formToPayload,
  recordToForm,
} from '../lib/faciliworksFields';

interface Personnel {
  id: string;
  full_name: string;
  email: string;
  personnel_type: string;
  craft: string | null;
  is_active: boolean;
}

export default function PersonnelPage() {
  return (
    <Routes>
      <Route index element={<PersonnelList />} />
      <Route path="new" element={<PersonnelForm />} />
      <Route path=":id/edit" element={<PersonnelForm />} />
    </Routes>
  );
}

function PersonnelList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { search, setSearch, filters, setFilter, queryString, reset, hasActive } = useListFilters({
    pageSize: 100,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['personnel', queryString],
    queryFn: () => api<Personnel[]>(`/v1/personnel${queryString}`),
  });

  const items = data ?? [];
  const total = data?.length ?? 0;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/personnel/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['personnel'] }),
  });

  return (
    <div>
      <PageHeader
        title="Personnel"
        description="Manage staff, contractors, crafts, and contact information."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => navigate('/personnel/new')}>
            <IconPlus size={16} />
            New Person
          </button>
        }
      />

      {isLoading ? (
        <LoadingState label="Loading personnel…" />
      ) : !hasActive && total === 0 ? (
        <div className="table-card">
          <EmptyState title="No personnel records" description="Add team members to assign work orders and track labor." />
        </div>
      ) : (
        <div className="table-card">
          <ListToolbar
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search personnel…"
            filters={[PERSONNEL_TYPE_FILTER]}
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
                <th>Name</th>
                <th>Email</th>
                <th>Type</th>
                <th>Craft</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td>{p.full_name}</td>
                  <td>{p.email}</td>
                  <td>{p.personnel_type}</td>
                  <td>{p.craft ?? '—'}</td>
                  <td>{p.is_active ? 'Active' : 'Inactive'}</td>
                  <RowActions
                    onEdit={() => navigate(`/personnel/${p.id}/edit`)}
                    onDelete={() => confirm(`Delete ${p.full_name}?`) && deleteMutation.mutate(p.id)}
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

function PersonnelForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => ({
    ...emptyFormFromFields(PERSONNEL_FIELDS),
    personnel_type: 'STAFF',
    is_active: true,
  }));

  const { data: record, isLoading } = useQuery({
    queryKey: ['personnel-detail', id],
    queryFn: () => api<Record<string, unknown>>(`/v1/personnel/${id}`),
    enabled: isEdit,
  });

  useEffect(() => {
    if (record) setForm(recordToForm(record, PERSONNEL_FIELDS));
  }, [record]);

  const saveMutation = useMutation({
    mutationFn: (body: object) =>
      isEdit
        ? api(`/v1/personnel/${id}`, { method: 'PUT', body: JSON.stringify(body) })
        : api('/v1/personnel', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['personnel'] });
      navigate('/personnel');
    },
  });

  if (isEdit && isLoading) return <LoadingState label="Loading personnel…" />;

  return (
    <FormPageShell title={isEdit ? 'Edit Personnel' : 'New Personnel'} backTo="/personnel" backLabel="Back to personnel">
      <form onSubmit={(e) => { e.preventDefault(); if (!siteId) return; saveMutation.mutate(formToPayload(form, PERSONNEL_FIELDS, isEdit ? {} : { site_id: siteId })); }}>
        <FwFormFields fields={PERSONNEL_FIELDS} form={form} setForm={setForm} mode={isEdit ? 'edit' : 'create'} />
        {saveMutation.isError && <div className="error">{(saveMutation.error as Error).message}</div>}
        <div className="form-page-footer">
          <FormActions onCancel={() => navigate('/personnel')} pending={saveMutation.isPending} />
        </div>
      </form>
    </FormPageShell>
  );
}
