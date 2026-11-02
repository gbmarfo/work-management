interface LoadingStateProps {
  label?: string;
}

export default function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-spinner" aria-hidden />
      <span>{label}</span>
    </div>
  );
}
