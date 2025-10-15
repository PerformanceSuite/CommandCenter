import React from 'react';
import {
  Calendar,
  User,
  FileText,
  Trash2,
  Edit,
  Eye,
  Clock,
  CheckCircle2,
  AlertCircle,
  Pause,
  XCircle,
} from 'lucide-react';
import type { ResearchTask, TaskStatus } from '../../types/researchTask';

interface ResearchTaskCardProps {
  task: ResearchTask;
  onView?: (task: ResearchTask) => void;
  onEdit?: (task: ResearchTask) => void;
  onDelete?: (taskId: number) => void;
}

const statusConfig: Record<
  TaskStatus,
  { color: string; icon: React.ReactNode; label: string }
> = {
  pending: {
    color: 'bg-slate-800 text-slate-300 border-gray-300',
    icon: <Clock size={14} />,
    label: 'Pending',
  },
  in_progress: {
    color: 'bg-blue-100 text-blue-700 border-blue-300',
    icon: <AlertCircle size={14} />,
    label: 'In Progress',
  },
  blocked: {
    color: 'bg-red-100 text-red-700 border-red-300',
    icon: <Pause size={14} />,
    label: 'Blocked',
  },
  completed: {
    color: 'bg-green-100 text-green-700 border-green-300',
    icon: <CheckCircle2 size={14} />,
    label: 'Completed',
  },
  cancelled: {
    color: 'bg-slate-800 text-slate-500 border-gray-300',
    icon: <XCircle size={14} />,
    label: 'Cancelled',
  },
};

export const ResearchTaskCard: React.FC<ResearchTaskCardProps> = ({
  task,
  onView,
  onEdit,
  onDelete,
}) => {
  const status = statusConfig[task.status];
  const isOverdue =
    task.due_date &&
    !task.completed_at &&
    new Date(task.due_date) < new Date();

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-lg text-white mb-1">
            {task.title}
          </h3>
          {task.description && (
            <p className="text-sm text-slate-400 line-clamp-2">
              {task.description}
            </p>
          )}
        </div>
        <div className="ml-3 flex gap-2">
          {onView && (
            <button
              onClick={() => onView(task)}
              className="p-1.5 text-slate-500 hover:text-primary-600 hover:bg-slate-800 rounded transition-colors"
              title="View Details"
            >
              <Eye size={18} />
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(task)}
              className="p-1.5 text-slate-500 hover:text-primary-600 hover:bg-slate-800 rounded transition-colors"
              title="Edit"
            >
              <Edit size={18} />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(task.id)}
              className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
              title="Delete"
            >
              <Trash2 size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-3">
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${status.color}`}
        >
          {status.icon}
          {status.label}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>Progress</span>
          <span className="font-medium">{task.progress_percentage}%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all"
            style={{ width: `${task.progress_percentage}%` }}
          />
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-3 text-sm text-slate-400">
        {task.assigned_to && (
          <div className="flex items-center gap-1.5">
            <User size={14} />
            <span>{task.assigned_to}</span>
          </div>
        )}
        {task.due_date && (
          <div
            className={`flex items-center gap-1.5 ${
              isOverdue ? 'text-red-600 font-medium' : ''
            }`}
          >
            <Calendar size={14} />
            <span>{formatDate(task.due_date)}</span>
            {isOverdue && <span className="text-xs">(Overdue)</span>}
          </div>
        )}
        {task.uploaded_documents && task.uploaded_documents.length > 0 && (
          <div className="flex items-center gap-1.5">
            <FileText size={14} />
            <span>{task.uploaded_documents.length} document(s)</span>
          </div>
        )}
      </div>

      {/* Hours */}
      {(task.estimated_hours || task.actual_hours) && (
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-4 text-xs text-slate-400">
          {task.estimated_hours && (
            <div>
              <span className="font-medium">Estimated:</span>{' '}
              {task.estimated_hours}h
            </div>
          )}
          {task.actual_hours && (
            <div>
              <span className="font-medium">Actual:</span> {task.actual_hours}h
            </div>
          )}
        </div>
      )}
    </div>
  );
};
