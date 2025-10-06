import React, { useState } from 'react';
import { Plus, Grid, List, Loader } from 'lucide-react';
import { ResearchTaskCard } from './ResearchTaskCard';
import { ResearchTaskModal } from './ResearchTaskModal';
import { ResearchTaskForm } from './ResearchTaskForm';
import {
  useResearchTasks,
  useCreateResearchTask,
  useDeleteResearchTask,
} from '../../hooks/useResearchTasks';
import type {
  ResearchTask,
  ResearchTaskCreate,
  TaskStatus,
} from '../../types/researchTask';

type ViewMode = 'grid' | 'list';

export const ResearchView: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ResearchTask | null>(null);
  const [taskToEdit, setTaskToEdit] = useState<ResearchTask | null>(null);

  // Fetch tasks with filter
  const {
    data: tasks,
    isLoading,
    error,
  } = useResearchTasks(
    statusFilter !== 'all' ? { status: statusFilter as TaskStatus } : undefined
  );

  const createMutation = useCreateResearchTask();
  const deleteMutation = useDeleteResearchTask();

  const handleCreateTask = async (data: ResearchTaskCreate) => {
    try {
      await createMutation.mutateAsync(data);
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(taskId);
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const handleViewTask = (task: ResearchTask) => {
    setSelectedTask(task);
  };

  const handleEditTask = (task: ResearchTask) => {
    setTaskToEdit(task);
    setShowCreateForm(true);
  };

  const statusFilters: { value: TaskStatus | 'all'; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'blocked', label: 'Blocked' },
    { value: 'completed', label: 'Completed' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Research Tasks</h2>
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex border border-gray-300 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${
                  viewMode === 'grid'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
                title="Grid View"
              >
                <Grid size={20} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${
                  viewMode === 'list'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
                title="List View"
              >
                <List size={20} />
              </button>
            </div>

            {/* Create Task Button */}
            <button
              onClick={() => {
                setTaskToEdit(null);
                setShowCreateForm(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus size={20} />
              Create Task
            </button>
          </div>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto">
          {statusFilters.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setStatusFilter(filter.value)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                statusFilter === filter.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Create/Edit Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
            <h3 className="text-xl font-bold mb-4">
              {taskToEdit ? 'Edit Task' : 'Create New Task'}
            </h3>
            <ResearchTaskForm
              onSubmit={handleCreateTask}
              onCancel={() => {
                setShowCreateForm(false);
                setTaskToEdit(null);
              }}
              initialData={taskToEdit || undefined}
              isLoading={createMutation.isPending}
            />
          </div>
        </div>
      )}

      {/* Task List */}
      <div className="bg-white rounded-lg shadow p-6">
        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader className="animate-spin text-primary-600" size={40} />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-12">
            <p className="text-red-600">Error loading tasks: {error.message}</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && (!tasks || tasks.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No tasks found</p>
            <p className="text-sm">
              {statusFilter !== 'all'
                ? `No tasks with status "${statusFilter}"`
                : 'Create your first research task to get started'}
            </p>
          </div>
        )}

        {/* Tasks Grid/List */}
        {!isLoading && !error && tasks && tasks.length > 0 && (
          <div
            className={
              viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                : 'space-y-4'
            }
          >
            {tasks.map((task) => (
              <ResearchTaskCard
                key={task.id}
                task={task}
                onView={handleViewTask}
                onEdit={handleEditTask}
                onDelete={handleDeleteTask}
              />
            ))}
          </div>
        )}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <ResearchTaskModal
          task={selectedTask}
          isOpen={!!selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </div>
  );
};
