interface RowActionsProps {
  onEdit: () => void;
  onDelete: () => void;
  deleteLabel?: string;
}

export default function RowActions({ onEdit, onDelete, deleteLabel = 'Delete' }: RowActionsProps) {
  return (
    <td className="actions-cell">
      <button type="button" className="btn btn-secondary btn-sm" onClick={onEdit}>
        Edit
      </button>
      <button type="button" className="btn btn-danger btn-sm" onClick={onDelete}>
        {deleteLabel}
      </button>
    </td>
  );
}
