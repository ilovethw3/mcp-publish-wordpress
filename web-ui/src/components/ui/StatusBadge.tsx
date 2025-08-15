import React from 'react';
import Badge from './Badge';
import { getStatusColor } from '@/lib/api';
import { clsx } from 'clsx';

interface StatusBadgeProps {
  status: string;
  variant?: 'default' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

const statusLabels: Record<string, string> = {
  'published': '已发布',
  'pending_review': '待审核',
  'approved': '已通过',
  'publishing': '发布中',
  'rejected': '已拒绝',
  'publish_failed': '发布失败',
  'healthy': '健康',
  'warning': '警告',
  'error': '错误',
  'unknown': '未知',
  'active': '活跃',
  'inactive': '不活跃',
  'locked': '已锁定',
};

const statusVariants: Record<string, 'success' | 'warning' | 'error' | 'secondary'> = {
  'published': 'success',
  'pending_review': 'warning',
  'approved': 'success',
  'publishing': 'secondary',
  'rejected': 'error',
  'publish_failed': 'error',
  'healthy': 'success',
  'warning': 'warning',
  'error': 'error',
  'unknown': 'secondary',
  'active': 'success',
  'inactive': 'secondary',
  'locked': 'error',
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  variant = 'default', 
  size = 'md' 
}) => {
  const displayText = statusLabels[status] || status;
  const badgeVariant = statusVariants[status] || 'secondary';

  if (variant === 'outline') {
    const colorClass = getStatusColor(status);
    return (
      <span
        className={clsx(
          'inline-flex items-center rounded-full border font-medium',
          colorClass.replace('bg-', 'border-').replace('-50', '-200'),
          colorClass.replace('bg-', 'text-').replace('-50', '-700'),
          {
            'px-1.5 py-0.5 text-xs': size === 'sm',
            'px-2.5 py-0.5 text-xs': size === 'md',
            'px-3 py-1 text-sm': size === 'lg',
          }
        )}
      >
        {displayText}
      </span>
    );
  }

  return (
    <Badge variant={badgeVariant} size={size}>
      {displayText}
    </Badge>
  );
};

export default StatusBadge;