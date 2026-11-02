import { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../AuthContext';
import LoadingState from '../components/LoadingState';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ListToolbar from '../components/ListToolbar';
import { IconPlus } from '../components/icons';
import { useListFilters } from '../hooks/useListFilters';
import { filterItems } from '../lib/listFilters';
import { api } from '../api';
import AssetCustomFieldsPanel from '../components/AssetCustomFieldsPanel';

interface LookupValue {
  id: string;
  code: string;
  label: string;
  sort_order: number;
  is_active: boolean;
}

interface LookupType {
  id: string;
  code: string;
  name: string;
  values: LookupValue[];
}

const emptyValue = { code: '', label: '', sort_order: 0, is_active: true };

export default function ConfigurationsPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [tab, setTab] = useState<'lookups' | 'asset-fields'>('lookups');
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [typeName, setTypeName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState(emptyValue);
  const [addForm, setAddForm] = useState(emptyValue);
  const [showAdd, setShowAdd] = useState(false);
  const { search, setSearch, filters, setFilter, reset, hasActive } = useListFilters();

  const { data: lookups, isLoading } = useQuery({
    queryKey: ['lookups', 'all'],
    queryFn: () => api<LookupType[]>('/v1/lookups?include_inactive=true'),
    enabled: user?.role === 'ADMIN',
  });

  useEffect(() => {
    if (lookups?.length && !selectedCode) {
      setSelectedCode(lookups[0].code);
    }
  }, [lookups, selectedCode]);

  const selected = lookups?.find((lt) => lt.code === selectedCode) ?? null;

  const filteredValues = useMemo(
    () => selected ? filterItems(selected.values, search, ['code', 'label'], filters) : [],
    [selected, search, filters],
  );

  useEffect(() => {
    if (selected) setTypeName(selected.name);
  }, [selected]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ['lookups'] });

  const updateTypeMutation = useMutation({
    mutationFn: ({ code, name }: { code: string; name: string }) =>
      api(`/v1/lookups/${code}`, { method: 'PUT', body: JSON.stringify({ name }) }),
    onSuccess: invalidate,
  });

  const addValueMutation = useMutation({
    mutationFn: ({ code, body }: { code: string; body: typeof emptyValue }) =>
      api(`/v1/lookups/${code}/values`, { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      invalidate();
      setAddForm(emptyValue);
      setShowAdd(false);
    },
  });

  const updateValueMutation = useMutation({
    mutationFn: ({ code, id, body }: { code: string; id: string; body: Partial<typeof emptyValue> }) =>
      api(`/v1/lookups/${code}/values/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    onSuccess: () => {
      invalidate();
      setEditingId(null);
    },
  });

  if (user?.role !== 'ADMIN') {
    return <Navigate to="/" replace />;
  }

  if (isLoading) return <LoadingState label="Loading configurations…" />;

  const startEdit = (value: LookupValue) => {
    setEditingId(value.id);
    setEditForm({
      code: value.code,
      label: value.label,
      sort_order: value.sort_order,
      is_active: value.is_active,
    });
  };

  const saveTypeName = () => {
    if (!selected || typeName.trim() === '' || typeName === selected.name) return;
    updateTypeMutation.mutate({ code: selected.code, name: typeName.trim() });
  };

  return (
    <div>
      <PageHeader
        title="Configurations"
        description="Manage reference data, lookup values, and asset custom fields."
      />

      <div className="tab-bar form-page-tabs" style={{ marginBottom: 16 }}>
        <button type="button" className={`btn btn-sm ${tab === 'lookups' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('lookups')}>
          Lookups
        </button>
        <button type="button" className={`btn btn-sm ${tab === 'asset-fields' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('asset-fields')}>
          Asset Custom Fields
        </button>
      </div>

      {tab === 'asset-fields' ? (
        <AssetCustomFieldsPanel />
      ) : !lookups?.length ? (
        <EmptyState title="No lookup types" description="Seed the database to create default lookup types." />
      ) : (
        <div className="config-layout">
          <aside className="config-types">
            <div className="config-types-header">Lookup Types</div>
            <ul>
              {lookups.map((lt) => (
                <li key={lt.code}>
                  <button
                    type="button"
                    className={`config-type-btn${lt.code === selectedCode ? ' active' : ''}`}
                    onClick={() => { setSelectedCode(lt.code); setEditingId(null); setShowAdd(false); reset(); }}
                  >
                    <span className="config-type-name">{lt.name}</span>
                    <span className="config-type-code">{lt.code}</span>
                    <span className="config-type-count">{lt.values.length}</span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          <section className="config-panel">
            {selected ? (
              <>
                <div className="config-panel-header">
                  <div className="config-type-edit">
                    <label htmlFor="lookup-type-name">Display Name</label>
                    <div className="config-type-edit-row">
                      <input
                        id="lookup-type-name"
                        value={typeName}
                        onChange={(e) => setTypeName(e.target.value)}
                      />
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={updateTypeMutation.isPending || typeName.trim() === selected.name}
                        onClick={saveTypeName}
                      >
                        Save Name
                      </button>
                    </div>
                    <span className="config-type-meta">Code: <code>{selected.code}</code></span>
                  </div>
                  <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowAdd((v) => !v)}>
                    <IconPlus size={14} />
                    Add Value
                  </button>
                </div>

                {showAdd && (
                  <form
                    className="config-add-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (!addForm.code.trim() || !addForm.label.trim()) return;
                      addValueMutation.mutate({
                        code: selected.code,
                        body: {
                          ...addForm,
                          code: addForm.code.trim().toUpperCase(),
                          label: addForm.label.trim(),
                          sort_order: Number(addForm.sort_order),
                        },
                      });
                    }}
                  >
                    <div className="form-row">
                      <div className="form-group">
                        <label>Code</label>
                        <input
                          value={addForm.code}
                          onChange={(e) => setAddForm({ ...addForm, code: e.target.value.toUpperCase() })}
                          required
                          placeholder="e.g. HIGH"
                        />
                      </div>
                      <div className="form-group">
                        <label>Label</label>
                        <input
                          value={addForm.label}
                          onChange={(e) => setAddForm({ ...addForm, label: e.target.value })}
                          required
                          placeholder="Display label"
                        />
                      </div>
                      <div className="form-group">
                        <label>Sort Order</label>
                        <input
                          type="number"
                          value={addForm.sort_order}
                          onChange={(e) => setAddForm({ ...addForm, sort_order: Number(e.target.value) })}
                        />
                      </div>
                    </div>
                    {addValueMutation.isError && (
                      <div className="error">{(addValueMutation.error as Error).message}</div>
                    )}
                    <div className="config-add-actions">
                      <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowAdd(false)}>Cancel</button>
                      <button type="submit" className="btn btn-primary btn-sm" disabled={addValueMutation.isPending}>Add</button>
                    </div>
                  </form>
                )}

                <div className="table-card">
                  {!hasActive && selected.values.length === 0 ? (
                    <EmptyState title="No values" description="Add a lookup value for this type." />
                  ) : (
                    <>
                  <ListToolbar
                    search={search}
                    onSearchChange={setSearch}
                    searchPlaceholder="Search values…"
                    filterValues={filters}
                    onFilterChange={setFilter}
                    onReset={hasActive ? reset : undefined}
                    resultCount={filteredValues.length}
                    totalCount={selected.values.length}
                  />
                  {hasActive && filteredValues.length === 0 ? (
                    <EmptyState title="No results match your search or filters." />
                  ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Label</th>
                        <th>Sort</th>
                        <th>Active</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredValues.map((value) => (
                        <tr key={value.id} className={!value.is_active ? 'config-row-inactive' : undefined}>
                          {editingId === value.id ? (
                            <>
                              <td>
                                <input
                                  value={editForm.code}
                                  onChange={(e) => setEditForm({ ...editForm, code: e.target.value.toUpperCase() })}
                                />
                              </td>
                              <td>
                                <input
                                  value={editForm.label}
                                  onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                                />
                              </td>
                              <td>
                                <input
                                  type="number"
                                  value={editForm.sort_order}
                                  onChange={(e) => setEditForm({ ...editForm, sort_order: Number(e.target.value) })}
                                  style={{ width: 72 }}
                                />
                              </td>
                              <td>
                                <label className="form-check">
                                  <input
                                    type="checkbox"
                                    checked={editForm.is_active}
                                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                                  />
                                  Active
                                </label>
                              </td>
                              <td className="actions-cell">
                                <button
                                  type="button"
                                  className="btn btn-primary btn-sm"
                                  disabled={updateValueMutation.isPending}
                                  onClick={() => updateValueMutation.mutate({
                                    code: selected.code,
                                    id: value.id,
                                    body: {
                                      code: editForm.code.trim(),
                                      label: editForm.label.trim(),
                                      sort_order: Number(editForm.sort_order),
                                      is_active: editForm.is_active,
                                    },
                                  })}
                                >
                                  Save
                                </button>
                                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>Cancel</button>
                              </td>
                            </>
                          ) : (
                            <>
                              <td><code>{value.code}</code></td>
                              <td>{value.label}</td>
                              <td>{value.sort_order}</td>
                              <td>
                                <span className={`badge ${value.is_active ? 'badge-completed' : 'badge-open'}`}>
                                  {value.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </td>
                              <td className="actions-cell">
                                <button type="button" className="btn btn-secondary btn-sm" onClick={() => startEdit(value)}>Edit</button>
                              </td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  )}
                    </>
                  )}
                </div>
                {updateValueMutation.isError && editingId && (
                  <div className="error" style={{ marginTop: 12 }}>{(updateValueMutation.error as Error).message}</div>
                )}
              </>
            ) : (
              <EmptyState title="Select a lookup type" description="Choose a lookup type from the list to view and edit its values." />
            )}
          </section>
        </div>
      )}
    </div>
  );
}
