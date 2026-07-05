import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { IconPlus } from './icons';
import { api } from '../api';

export interface WorkOrderTask {
  id: string;
  work_order_id: string;
  line_number: number;
  description: string;
  estimated_hours: number | null;
  status: string;
  completed_at: string | null;
  notes: string | null;
}

const emptyTask = {
  description: '',
  estimated_hours: '',
  notes: '',
};

interface Props {
  workOrderId: string;
}

export default function WorkOrderTasks({ workOrderId }: Props) {
  const qc = useQueryClient();
  const [draft, setDraft] = useState(emptyTask);
  const [showAdd, setShowAdd] = useState(false);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['work-order-tasks', workOrderId],
    queryFn: () => api<WorkOrderTask[]>(`/v1/work-orders/${workOrderId}/tasks`),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['work-order-tasks', workOrderId] });

  const createMutation = useMutation({
    mutationFn: (body: object) =>
      api(`/v1/work-orders/${workOrderId}/tasks`, { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => {
      invalidate();
      setDraft(emptyTask);
      setShowAdd(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ taskId, body }: { taskId: string; body: object }) =>
      api(`/v1/work-orders/${workOrderId}/tasks/${taskId}`, { method: 'PUT', body: JSON.stringify(body) }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) =>
      api(`/v1/work-orders/${workOrderId}/tasks/${taskId}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  });

  const items = tasks ?? [];
  const completedCount = items.filter((t) => t.status === 'COMPLETED').length;

  return (
    <details open style={{ marginTop: 16 }}>
      <summary style={{ fontWeight: 600, marginBottom: 8, cursor: 'pointer' }}>
        Related Tasks {items.length > 0 && `(${completedCount}/${items.length} complete)`}
      </summary>

      {isLoading ? (
        <p className="form-hint">Loading tasks…</p>
      ) : (
        <>
          {items.length > 0 && (
            <div className="table-card" style={{ marginBottom: 12 }}>
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Description</th>
                    <th>Est. Hours</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((task) => (
                    <tr key={task.id}>
                      <td>{task.line_number}</td>
                      <td>
                        {task.description}
                        {task.notes && <div className="form-hint" style={{ marginTop: 4 }}>{task.notes}</div>}
                      </td>
                      <td>{task.estimated_hours ?? '—'}</td>
                      <td>
                        <span className={`badge ${task.status === 'COMPLETED' ? 'badge-completed' : 'badge-open'}`}>
                          {task.status === 'COMPLETED' ? 'Complete' : 'Pending'}
                        </span>
                      </td>
                      <td className="actions-cell">
                        {task.status !== 'COMPLETED' ? (
                          <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            onClick={() => updateMutation.mutate({ taskId: task.id, body: { status: 'COMPLETED' } })}
                          >
                            Complete
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => updateMutation.mutate({ taskId: task.id, body: { status: 'PENDING' } })}
                          >
                            Reopen
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => confirm('Delete this task?') && deleteMutation.mutate(task.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {showAdd ? (
            <form
              className="config-add-form"
              onSubmit={(e) => {
                e.preventDefault();
                if (!draft.description.trim()) return;
                createMutation.mutate({
                  description: draft.description.trim(),
                  estimated_hours: draft.estimated_hours ? Number(draft.estimated_hours) : undefined,
                  notes: draft.notes.trim() || undefined,
                });
              }}
            >
              <div className="form-row">
                <div className="form-group" style={{ flex: 2 }}>
                  <label>Task Description *</label>
                  <input
                    value={draft.description}
                    onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                    required
                    placeholder="e.g. Inspect belt tension and alignment"
                  />
                </div>
                <div className="form-group">
                  <label>Est. Hours</label>
                  <input
                    type="number"
                    min="0"
                    step="0.25"
                    value={draft.estimated_hours}
                    onChange={(e) => setDraft({ ...draft, estimated_hours: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Notes</label>
                <input
                  value={draft.notes}
                  onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
                  placeholder="Optional instructions"
                />
              </div>
              {createMutation.isError && <div className="error">{(createMutation.error as Error).message}</div>}
              <div className="config-add-actions">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowAdd(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={createMutation.isPending}>Add Task</button>
              </div>
            </form>
          ) : (
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowAdd(true)}>
              <IconPlus size={14} />
              Add Task
            </button>
          )}
        </>
      )}
    </details>
  );
}
