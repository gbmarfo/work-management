import type { FwFieldDef } from '../lib/faciliworksFields';

interface Props {
  fields: FwFieldDef[];
  form: Record<string, string | boolean | number>;
  setForm: (form: Record<string, string | boolean | number>) => void;
  mode: 'create' | 'edit';
}

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FwFieldDef;
  value: string | boolean | number;
  onChange: (v: string | boolean | number) => void;
}) {
  if (field.type === 'checkbox') {
    return (
      <label className="form-check">
        <input type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)} />
        {field.label}
      </label>
    );
  }
  if (field.type === 'textarea') {
    return (
      <textarea
        rows={3}
        value={String(value ?? '')}
        onChange={(e) => onChange(e.target.value)}
        required={field.required}
      />
    );
  }
  if (field.type === 'select' && field.options) {
    return (
      <select value={String(value ?? '')} onChange={(e) => onChange(e.target.value)} required={field.required}>
        {!field.required && <option value="">—</option>}
        {field.options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    );
  }
  return (
    <input
      type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
      value={value === '' || value == null ? '' : String(value)}
      onChange={(e) => onChange(field.type === 'number' ? e.target.value : e.target.value)}
      required={field.required}
      step={field.type === 'number' ? 'any' : undefined}
    />
  );
}

export default function FwFormFields({ fields, form, setForm, mode }: Props) {
  const visible = fields.filter((f) => !(f.createOnly && mode === 'edit'));
  const sections = [...new Set(visible.map((f) => f.section ?? 'General'))];

  return (
    <div className="fw-form-sections">
      {sections.map((section) => (
        <details key={section} open={section === sections[0]}>
          <summary style={{ fontWeight: 600, marginBottom: 8, cursor: 'pointer' }}>{section}</summary>
          <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px', marginBottom: 16 }}>
            {visible
              .filter((f) => (f.section ?? 'General') === section)
              .map((field) =>
                field.type === 'checkbox' ? (
                  <div key={field.key} style={{ gridColumn: '1 / -1' }}>
                    <FieldInput
                      field={field}
                      value={form[field.key]}
                      onChange={(v) => setForm({ ...form, [field.key]: v })}
                    />
                  </div>
                ) : (
                  <div key={field.key} className="form-group" style={field.type === 'textarea' ? { gridColumn: '1 / -1' } : undefined}>
                    <label>{field.label}</label>
                    <FieldInput
                      field={field}
                      value={form[field.key]}
                      onChange={(v) => setForm({ ...form, [field.key]: v })}
                    />
                  </div>
                ),
              )}
          </div>
        </details>
      ))}
    </div>
  );
}
