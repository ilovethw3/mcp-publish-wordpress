'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';

const navigation = [
  { name: '仪表板', href: '/', icon: '🏠' },
  { name: '文章管理', href: '/articles', icon: '📄' },
  { name: '代理管理', href: '/agents', icon: '👥' },
  { name: '站点管理', href: '/sites', icon: '🖥️' },
  { name: '安全监控', href: '/security', icon: '🔒' },
  { name: '统计分析', href: '/analytics', icon: '📊' },
  { name: '系统设置', href: '/settings', icon: '⚙️' },
];

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ open = true, onClose }) => {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-lg transition-transform duration-300 ease-in-out lg:static lg:translate-x-0',
          {
            'translate-x-0': open,
            '-translate-x-full': !open,
          }
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600">
                <span className="text-sm font-bold text-white">MCP</span>
              </div>
              <div className="ml-3">
                <h1 className="text-sm font-semibold text-gray-900">WordPress Publisher</h1>
                <p className="text-xs text-gray-500">v2.1.0</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    {
                      'bg-blue-50 text-blue-700': isActive,
                      'text-gray-700 hover:bg-gray-50 hover:text-gray-900': !isActive,
                    }
                  )}
                >
                  <span className="mr-3 text-lg">
                    {item.icon}
                  </span>
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-gray-200 p-4">
            <div className="text-xs text-gray-500">
              <div>多代理多站点</div>
              <div>WordPress发布管理</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;