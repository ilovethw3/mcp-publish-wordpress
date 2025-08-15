/**
 * Site Form Modal Component
 * Handles adding and editing sites
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { X, TestTube, CheckCircle, XCircle } from 'lucide-react';

interface SiteFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  site?: any;
  onSave: (site: any) => Promise<void>;
  isLoading?: boolean;
}

const SiteFormModal: React.FC<SiteFormModalProps> = ({
  isOpen,
  onClose,
  site,
  onSave,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<any>({
    name: '',
    description: '',
    wordpress_config: {
      api_url: '',
      username: '',
      app_password: '',
      default_status: 'publish',
      default_comment_status: 'closed',
      default_ping_status: 'closed',
      category_mapping: {},
      tag_auto_create: true,
    },
    publishing_rules: {
      allowed_agents: [],
      allowed_categories: [],
      min_word_count: 100,
      max_word_count: 10000,
      require_featured_image: false,
      auto_approve: false,
      auto_publish_approved: true,
    },
    rate_limit: {
      max_posts_per_hour: 10,
      max_posts_per_day: 50,
      max_concurrent_publishes: 3,
    },
    notifications: {
      on_publish_success: true,
      on_publish_failure: true,
      on_connection_error: true,
    },
    status: 'active',
    priority: 1,
  });

  const [testResult, setTestResult] = useState<any>(null);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  // Initialize form data when site prop changes
  useEffect(() => {
    if (site) {
      setFormData({
        name: site.name || '',
        description: site.description || '',
        wordpress_config: site.wordpress_config || {
          api_url: '',
          username: '',
          app_password: '',
          default_status: 'publish',
          default_comment_status: 'closed',
          default_ping_status: 'closed',
          category_mapping: {},
          tag_auto_create: true,
        },
        publishing_rules: site.publishing_rules || {
          allowed_agents: [],
          allowed_categories: [],
          min_word_count: 100,
          max_word_count: 10000,
          require_featured_image: false,
          auto_approve: false,
          auto_publish_approved: true,
        },
        rate_limit: site.rate_limit || {
          max_posts_per_hour: 10,
          max_posts_per_day: 50,
          max_concurrent_publishes: 3,
        },
        notifications: site.notifications || {
          on_publish_success: true,
          on_publish_failure: true,
          on_connection_error: true,
        },
        status: site.status || 'active',
        priority: site.priority || 1,
      });
    }
  }, [site]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error saving site:', error);
    }
  };

  const testConnection = async () => {
    setIsTestingConnection(true);
    setTestResult(null);

    try {
      const response = await fetch('/api/config/sites/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wordpress_config: {
            api_url: formData.wordpress_config.api_url,
            username: formData.wordpress_config.username,
            app_password: formData.wordpress_config.app_password,
          }
        }),
      });

      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: `连接测试失败: ${error instanceof Error ? error.message : '未知错误'}`,
      });
    } finally {
      setIsTestingConnection(false);
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {/* Background backdrop */}
      <div className="fixed inset-0 bg-black/25" aria-hidden="true" />
      
      {/* Container to center the panel */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <Dialog.Title className="text-xl font-semibold text-gray-900">
                {site ? '编辑站点' : '添加站点'}
              </Dialog.Title>
              <Button variant="outline" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">基本信息</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    站点名称 *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    状态
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="active">活跃</option>
                    <option value="inactive">不活跃</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  站点描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  rows={3}
                />
              </div>
            </div>

            {/* WordPress Configuration */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">WordPress 配置</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API URL *
                  </label>
                  <input
                    type="url"
                    value={formData.wordpress_config.api_url}
                    onChange={(e) => setFormData({
                      ...formData,
                      wordpress_config: {
                        ...formData.wordpress_config,
                        api_url: e.target.value,
                      },
                    })}
                    placeholder="https://example.com/wp-json/wp/v2"
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      用户名 *
                    </label>
                    <input
                      type="text"
                      value={formData.wordpress_config.username}
                      onChange={(e) => setFormData({
                        ...formData,
                        wordpress_config: {
                          ...formData.wordpress_config,
                          username: e.target.value,
                        },
                      })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      应用密码 *
                    </label>
                    <input
                      type="password"
                      value={formData.wordpress_config.app_password}
                      onChange={(e) => setFormData({
                        ...formData,
                        wordpress_config: {
                          ...formData.wordpress_config,
                          app_password: e.target.value,
                        },
                      })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                  </div>
                </div>

                {/* Connection Test */}
                <div className="flex items-center space-x-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={testConnection}
                    disabled={isTestingConnection || !formData.wordpress_config.api_url}
                    className="flex items-center"
                  >
                    {isTestingConnection ? (
                      <LoadingSpinner size="sm" className="mr-2" />
                    ) : (
                      <TestTube className="w-4 h-4 mr-2" />
                    )}
                    测试连接
                  </Button>
                  
                  {testResult && (
                    <div className={`flex items-center text-sm ${
                      testResult.success ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {testResult.success ? (
                        <CheckCircle className="w-4 h-4 mr-1" />
                      ) : (
                        <XCircle className="w-4 h-4 mr-1" />
                      )}
                      {testResult.message || (testResult.success ? '连接成功' : '连接失败')}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <Button type="button" variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading && <LoadingSpinner size="sm" className="mr-2" />}
                {site ? '更新站点' : '添加站点'}
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default SiteFormModal;