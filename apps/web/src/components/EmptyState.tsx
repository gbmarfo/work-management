interface EmptyStateProps {
  title: string;
  description?: string;
}

export default function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden>—</div>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
    </div>
  );
}
