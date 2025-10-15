import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GitBranch,
  Database,
  CheckCircle,
  FileText,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { ActivityEvent } from '../../services/dashboardApi';

export interface ActivityFeedProps {
  activities: ActivityEvent[];
  isLoading?: boolean;
}

const getActivityIcon = (type: string, action: string) => {
  if (action === 'completed') {
    return { Icon: CheckCircle, color: 'text-green-600 bg-green-100' };
  }

  switch (type) {
    case 'repository':
      return { Icon: GitBranch, color: 'text-blue-600 bg-blue-100' };
    case 'technology':
      return { Icon: Database, color: 'text-purple-600 bg-purple-100' };
    case 'task':
      return { Icon: AlertCircle, color: 'text-orange-600 bg-orange-100' };
    case 'document':
      return { Icon: FileText, color: 'text-slate-400 bg-slate-800' };
    default:
      return { Icon: Clock, color: 'text-slate-400 bg-slate-800' };
  }
};

const getActivityText = (activity: ActivityEvent): string => {
  const actionText = {
    created: 'created',
    updated: 'updated',
    completed: 'completed',
  }[activity.action] || 'updated';

  const typeText = {
    repository: 'repository',
    technology: 'technology',
    task: 'task',
    document: 'document',
  }[activity.type] || 'item';

  return `${actionText} ${typeText}`;
};

const formatTimestamp = (timestamp: string): string => {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString();
  }
};

const getNavigationPath = (activity: ActivityEvent): string => {
  switch (activity.type) {
    case 'repository':
      return `/repositories/${activity.id}`;
    case 'technology':
      return `/technologies/${activity.id}`;
    case 'task':
      return `/research/${activity.id}`;
    case 'document':
      return `/knowledge/${activity.id}`;
    default:
      return '#';
  }
};

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities, isLoading = false }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-start space-x-4 animate-pulse">
            <div className="w-10 h-10 bg-slate-700 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-700 rounded w-3/4" />
              <div className="h-3 bg-slate-700 rounded w-1/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <Clock size={48} className="mx-auto mb-2 opacity-50" />
        <p>No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" role="list">
      {activities.map((activity) => {
        const { Icon, color } = getActivityIcon(activity.type, activity.action);
        const navigationPath = getNavigationPath(activity);

        return (
          <div
            key={`${activity.type}-${activity.id}-${activity.timestamp}`}
            className="flex items-start space-x-4 pb-4 border-b last:border-b-0 cursor-pointer hover:bg-slate-900 rounded p-2 -m-2 transition-colors"
            role="listitem"
            onClick={() => navigate(navigationPath)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                navigate(navigationPath);
              }
            }}
            tabIndex={0}
          >
            <div className={`${color} p-2 rounded-full flex-shrink-0`}>
              <Icon size={20} aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{activity.title}</p>
              <p className="text-sm text-slate-400">{getActivityText(activity)}</p>
              {activity.status && (
                <span className="inline-block mt-1 px-2 py-1 text-xs font-medium rounded bg-slate-800 text-slate-300">
                  {activity.status}
                </span>
              )}
            </div>
            <div className="flex-shrink-0 text-xs text-gray-400">
              <time dateTime={activity.timestamp}>{formatTimestamp(activity.timestamp)}</time>
            </div>
          </div>
        );
      })}
    </div>
  );
};
