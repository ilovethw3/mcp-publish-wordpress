'use client';

import React from 'react';
import { useConnectionStatus } from '@/hooks/useMCPData';
import Badge from '../ui/Badge';
import LoadingSpinner from '../ui/LoadingSpinner';

interface HeaderProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, sidebarOpen }) => {
  const { isConnected, lastChecked, checkConnection } = useConnectionStatus();

  const getConnectionStatus = () => {
    if (isConnected === null) {
      return { variant: 'secondary' as const, text: '检查中...', icon: <LoadingSpinner size="sm" /> };
    }
    if (isConnected) {
      return { variant: 'success' as const, text: '已连接', icon: '🟢' };
    }
    return { variant: 'error' as const, text: '连接断开', icon: '🔴' };
  };

  const connectionStatus = getConnectionStatus();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Left side */}
        <div className="flex items-center">
          {/* Mobile menu button */}
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 lg:hidden"
            onClick={onMenuClick}
          >
            <span className="sr-only">打开侧边栏</span>
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"
              />
            </svg>
          </button>

          {/* Page title */}
          <div className="ml-4 lg:ml-0">
            <h1 className="text-lg font-semibold text-gray-900">
              MCP WordPress Publisher 管理控制台
            </h1>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Connection status */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">MCP服务器:</span>
            <Badge variant={connectionStatus.variant} size="sm">
              <span className="flex items-center space-x-1">
                {typeof connectionStatus.icon === 'string' ? (
                  <span>{connectionStatus.icon}</span>
                ) : (
                  connectionStatus.icon
                )}
                <span>{connectionStatus.text}</span>
              </span>
            </Badge>
          </div>

          {/* Last check time */}
          {lastChecked && (
            <div className="text-xs text-gray-500">
              最后检查: {lastChecked.toLocaleTimeString('zh-CN')}
            </div>
          )}

          {/* Refresh button */}
          <button
            onClick={checkConnection}
            className="rounded-md p-1 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            title="检查连接状态"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;