import React from 'react';
import { clsx } from 'clsx';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <div
        className={clsx(
          'inline-flex items-center rounded-full border font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          {
            'border-transparent bg-gray-900 text-gray-50 hover:bg-gray-900/80': variant === 'default',
            'border-transparent bg-gray-100 text-gray-900 hover:bg-gray-100/80': variant === 'secondary',
            'border-transparent bg-green-100 text-green-800': variant === 'success',
            'border-transparent bg-yellow-100 text-yellow-800': variant === 'warning',
            'border-transparent bg-red-100 text-red-800': variant === 'error',
            'text-gray-950': variant === 'outline',
          },
          {
            'px-1.5 py-0.5 text-xs': size === 'sm',
            'px-2.5 py-0.5 text-xs': size === 'md',
            'px-3 py-1 text-sm': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Badge.displayName = 'Badge';

export default Badge;