'use client';

import React, { useState } from 'react';
import { useConnectionStatus } from '@/hooks/useMCPData';
import { useAuth } from '@/contexts/AuthContext';
import Badge from '../ui/Badge';
import LoadingSpinner from '../ui/LoadingSpinner';
import { User, LogOut, Settings } from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, sidebarOpen }) => {
  const { isConnected, lastChecked, checkConnection } = useConnectionStatus();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

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

          {/* User Menu */}
          {user && (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 rounded-md p-2 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <div className="flex items-center justify-center w-8 h-8 bg-blue-500 text-white rounded-full">
                  <User className="w-4 h-4" />
                </div>
                <div className="hidden sm:block text-left">
                  <div className="text-sm font-medium">{user.username}</div>
                  <div className="text-xs text-gray-500">
                    {user.is_reviewer ? '审核员' : '用户'}
                  </div>
                </div>
                <svg
                  className="w-4 h-4 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                  />
                </svg>
              </button>

              {/* User dropdown menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                  <div className="py-1">
                    <div className="px-4 py-2 text-sm text-gray-700 border-b border-gray-200">
                      <div className="font-medium">{user.username}</div>
                      <div className="text-gray-500">{user.email}</div>
                    </div>
                    
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        window.location.href = '/users';
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      用户管理
                    </button>
                    
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        logout();
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      退出登录
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;