import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import EmptyState from './EmptyState';
import ListToolbar from './ListToolbar';
import { IconPlus } from './icons';
import { useDefaultSiteId } from '../hooks/useSites';
import { useListFilters } from '../hooks/useListFilters';
import { api } from '../api';
import type { CustomFieldDefinition } from './CustomFieldInputs';

const DATA_TYPES = [
  { value: 'STRING', label: 'Text' },
  { value: 'NUMBER', label: 'Number' },
  { value: 'BOOLEAN', label: 'Yes/No' },
  { value: 'DATE', label: 'Date' },
  { value: 'SELECT', label: 'Dropdown' },
] as const;

const emptyForm = {
  name: '',
  label: '',
  data_type: 'STRING' as CustomFieldDefinition['data_type'],
  options: '',
  is_required: false,
};

export default function AssetCustomFieldsPanel() {
  const qc = useQueryClient();
  const siteId = useDefaultSiteId();
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ label: '', options: '', is_required: false });
  const { search, setSearch, reset, hasActive } = useListFilters();

  const { data: fields, isLoading } = useQuery({
    queryKey: ['custom-fields', 'ASSET', siteId],
    queryFn: () => api<CustomFieldDefinition[]>(`/v1/custom-fields?entity_type=ASSET${siteId ? `&site_id=${siteId}` : ''}`),
    enabled: !!siteId,
  });

  const items = (fields ?? []).filter((f) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return f.name.toLowerCase().includes(q) || f.label.toLowerCase().includes(q);
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['custom-fields'] });

  const createMutation = useMutation({
    mutationFn: (body: object) => api('/v1/custom-fields', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      invalidate();
      setAddForm(emptyForm);
      setShowAdd(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: object }) =>
      api(`/v1/custom-fields/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    onSuccess: () => {
      invalidate();
      setEditingId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/custom-fields/${id}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  });

  if (!siteId) {
    return <EmptyState title="No site selected" description="Select a site to manage asset custom fields." />;
  }

  if (isLoading) return null;

  return (
    <div>
      <div className="config-panel-header" style={{ marginBottom: 16 }}>
        <div>
          <h3 style={{ margin: 0 }}>Asset Custom Fields</h3>
          <p className="form-hint" style={{ margin: '4px 0 0' }}>
            Define extra fields shown on asset create/edit forms. Values are stored per asset.
          </p>
        </div>
        <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowAdd((v) => !v)}>
          <IconPlus size={14} />
          New Field
        </button>
      </div>

      {showAdd && (
        <form
          className="config-add-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (!addForm.name.trim() || !addForm.label.trim()) return;
            createMutation.mutate({
              site_id: siteId,
              entity_type: 'ASSET',
              name: addForm.name.trim(),
              label: addForm.label.trim(),
              data_type: addForm.data_type,
              is_required: addForm.is_required,
              options: addForm.data_type === 'SELECT'
                ? addForm.options.split(',').map((s) => s.trim()).filter(Boolean)
                : undefined,
            });
          }}
        >
          <div className="form-row">
            <div className="form-group">
              <label>Field Key</label>
              <input
                value={addForm.name}
                onChange={(e) => setAddForm({ ...addForm, name: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                required
                placeholder="e.g. building_zone"
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
              <label>Type</label>
              <select
                value={addForm.data_type}
                onChange={(e) => setAddForm({ ...addForm, data_type: e.target.value as CustomFieldDefinition['data_type'] })}
              >
                {DATA_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>
          {addForm.data_type === 'SELECT' && (
            <div className="form-group">
              <label>Options (comma-separated)</label>
              <input
                value={addForm.options}
                onChange={(e) => setAddForm({ ...addForm, options: e.target.value })}
                placeholder="North, South, East, West"
                required
              />
            </div>
          )}
          <label className="form-check">
            <input
              type="checkbox"
              checked={addForm.is_required}
              onChange={(e) => setAddForm({ ...addForm, is_required: e.target.checked })}
            />
            Required on asset forms
          </label>
          {createMutation.isError && <div className="error">{(createMutation.error as Error).message}</div>}
          <div className="config-add-actions">
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowAdd(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary btn-sm" disabled={createMutation.isPending}>Create Field</button>
          </div>
        </form>
      )}

      <div className="table-card">
        {!hasActive && (fields?.length ?? 0) === 0 ? (
          <EmptyState
            title="No custom fields"
            description="Create custom fields to capture site-specific asset data such as zones, departments, or compliance tags."
          />
        ) : (
          <>
            <ListToolbar
              search={search}
              onSearchChange={setSearch}
              searchPlaceholder="Search fields…"
              onReset={hasActive ? reset : undefined}
              resultCount={items.length}
              totalCount={fields?.length ?? 0}
            />
            {hasActive && items.length === 0 ? (
              <EmptyState title="No results match your search." />
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Label</th>
                    <th>Type</th>
                    <th>Required</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((field) => (
                    <tr key={field.id}>
                      {editingId === field.id ? (
                        <>
                          <td><code>{field.name}</code></td>
                          <td>
                            <input
                              value={editForm.label}
                              onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                            />
                          </td>
                          <td>{field.data_type}</td>
                          <td>
                            <input
                              type="checkbox"
                              checked={editForm.is_required}
                              onChange={(e) => setEditForm({ ...editForm, is_required: e.target.checked })}
                            />
                          </td>
                          <td className="actions-cell">
                            <button
                              type="button"
                              className="btn btn-primary btn-sm"
                              disabled={updateMutation.isPending}
                              onClick={() => updateMutation.mutate({
                                id: field.id,
                                body: {
                                  label: editForm.label.trim(),
                                  is_required: editForm.is_required,
                                  options: field.data_type === 'SELECT'
                                    ? editForm.options.split(',').map((s) => s.trim()).filter(Boolean)
                                    : undefined,
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
                          <td><code>{field.name}</code></td>
                          <td>{field.label}</td>
                          <td>{field.data_type}{field.options?.length ? ` (${field.options.join(', ')})` : ''}</td>
                          <td>{field.is_required ? 'Yes' : 'No'}</td>
                          <td className="actions-cell">
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => {
                                setEditingId(field.id);
                                setEditForm({
                                  label: field.label,
                                  is_required: field.is_required,
                                  options: (field.options ?? []).join(', '),
                                });
                              }}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => confirm(`Delete custom field "${field.label}"?`) && deleteMutation.mutate(field.id)}
                            >
                              Delete
                            </button>
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
      <p className="form-hint" style={{ marginTop: 12 }}>
        Custom fields appear on the <Link to="/assets/new">asset form</Link> under the Custom Fields section.
      </p>
    </div>
  );
}
