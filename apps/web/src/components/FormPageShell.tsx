import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface FormPageShellProps {
  title: string;
  description?: string;
  backTo: string;
  backLabel?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export default function FormPageShell({
  title,
  description,
  backTo,
  backLabel = 'Back to list',
  children,
  footer,
}: FormPageShellProps) {
  return (
    <div className="form-page">
      <Link to={backTo} className="form-page-back">
        ← {backLabel}
      </Link>
      <header className="form-page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          {description && <p className="page-description">{description}</p>}
        </div>
      </header>
      <div className="form-page-body card">{children}</div>
      {footer && <div className="form-page-footer">{footer}</div>}
    </div>
  );
}

export function FormActions({
  onCancel,
  submitLabel = 'Save',
  pending = false,
  cancelLabel = 'Cancel',
}: {
  onCancel: () => void;
  submitLabel?: string;
  pending?: boolean;
  cancelLabel?: string;
}) {
  return (
    <>
      <button type="button" className="btn btn-secondary" onClick={onCancel}>
        {cancelLabel}
      </button>
      <button type="submit" className="btn btn-primary" disabled={pending}>
        {pending ? 'Saving…' : submitLabel}
      </button>
    </>
  );
}
