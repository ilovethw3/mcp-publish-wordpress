import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { clsx } from 'clsx';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color?: 'primary' | 'success' | 'warning' | 'error';
  description?: string;
  loading?: boolean;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  trend,
  icon: Icon,
  color = 'primary',
  description,
  loading = false,
}) => {
  const colorClasses = {
    primary: 'text-blue-600',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    stable: 'text-gray-600',
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    stable: '→',
  };

  if (loading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-600">
            {title}
          </CardTitle>
          {Icon && (
            <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
          )}
        </CardHeader>
        <CardContent>
          <div className="h-8 w-24 bg-gray-200 rounded animate-pulse mb-2" />
          {description && (
            <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">
          {title}
        </CardTitle>
        {Icon && (
          <Icon className={clsx('h-4 w-4', colorClasses[color])} />
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        <div className="flex items-center space-x-2 text-xs text-gray-600 mt-1">
          {change !== undefined && trend && (
            <span className={clsx('flex items-center', trendColors[trend])}>
              <span className="mr-1">{trendIcons[trend]}</span>
              {Math.abs(change)}%
            </span>
          )}
          {description && (
            <span className="text-gray-500">{description}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default StatsCard;