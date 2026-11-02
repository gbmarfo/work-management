export interface CustomFieldDefinition {
  id: string;
  name: string;
  label: string;
  data_type: 'STRING' | 'NUMBER' | 'BOOLEAN' | 'DATE' | 'SELECT';
  options: string[] | null;
  is_required: boolean;
}

interface Props {
  definitions: CustomFieldDefinition[];
  values: Record<string, string | number | boolean>;
  onChange: (values: Record<string, string | number | boolean>) => void;
}

export function emptyCustomFieldValues(definitions: CustomFieldDefinition[]): Record<string, string | number | boolean> {
  const out: Record<string, string | number | boolean> = {};
  for (const def of definitions) {
    out[def.name] = def.data_type === 'BOOLEAN' ? false : '';
  }
  return out;
}

export function customFieldsFromRecord(
  definitions: CustomFieldDefinition[],
  record: Record<string, unknown> | undefined,
): Record<string, string | number | boolean> {
  const base = emptyCustomFieldValues(definitions);
  const stored = record?.custom_fields;
  if (!stored || typeof stored !== 'object') return base;
  for (const def of definitions) {
    const val = (stored as Record<string, unknown>)[def.name];
    if (val == null) continue;
    if (def.data_type === 'BOOLEAN') base[def.name] = Boolean(val);
    else if (def.data_type === 'NUMBER') base[def.name] = Number(val);
    else base[def.name] = String(val);
  }
  return base;
}

export default function CustomFieldInputs({ definitions, values, onChange }: Props) {
  if (definitions.length === 0) return null;

  const set = (name: string, value: string | number | boolean) => onChange({ ...values, [name]: value });

  return (
    <details open style={{ marginBottom: 16 }}>
      <summary style={{ fontWeight: 600, marginBottom: 8, cursor: 'pointer' }}>Custom Fields</summary>
      <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
        {definitions.map((def) => (
          <div
            key={def.id}
            className="form-group"
            style={def.data_type === 'BOOLEAN' ? { gridColumn: '1 / -1' } : def.data_type === 'STRING' ? undefined : undefined}
          >
            {def.data_type === 'BOOLEAN' ? (
              <label className="form-check" style={{ marginTop: 8 }}>
                <input
                  type="checkbox"
                  checked={Boolean(values[def.name])}
                  onChange={(e) => set(def.name, e.target.checked)}
                />
                {def.label}
                {def.is_required && ' *'}
              </label>
            ) : (
              <>
                <label>
                  {def.label}
                  {def.is_required && ' *'}
                </label>
                {def.data_type === 'SELECT' && def.options?.length ? (
                  <select
                    value={String(values[def.name] ?? '')}
                    onChange={(e) => set(def.name, e.target.value)}
                    required={def.is_required}
                  >
                    {!def.is_required && <option value="">—</option>}
                    {def.options.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : def.data_type === 'NUMBER' ? (
                  <input
                    type="number"
                    step="any"
                    value={values[def.name] === '' ? '' : String(values[def.name] ?? '')}
                    onChange={(e) => set(def.name, e.target.value === '' ? '' : Number(e.target.value))}
                    required={def.is_required}
                  />
                ) : def.data_type === 'DATE' ? (
                  <input
                    type="date"
                    value={String(values[def.name] ?? '')}
                    onChange={(e) => set(def.name, e.target.value)}
                    required={def.is_required}
                  />
                ) : (
                  <input
                    type="text"
                    value={String(values[def.name] ?? '')}
                    onChange={(e) => set(def.name, e.target.value)}
                    required={def.is_required}
                  />
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </details>
  );
}
