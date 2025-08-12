/**
 * Agent Form Modal Component
 * Handles adding and editing agents
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { X, Copy, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { FullConfigAgent } from '@/types';

interface AgentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent?: FullConfigAgent;
  onSave: (agent: Omit<FullConfigAgent, 'created_at'>) => Promise<void>;
  isLoading?: boolean;
}

const AgentFormModal: React.FC<AgentFormModalProps> = ({
  isOpen,
  onClose,
  agent,
  onSave,
  isLoading = false
}) => {
  const isEditing = !!agent;
  const [formData, setFormData] = useState<Omit<FullConfigAgent, 'created_at'>>({
    id: '',
    name: '',
    description: '',
    api_key: '',
    rate_limit: {
      requests_per_minute: 10,
      requests_per_hour: 100,
      requests_per_day: 500,
    },
    permissions: {
      can_submit_articles: true,
      can_edit_own_articles: true,
      can_delete_own_articles: false,
      can_view_statistics: true,
      allowed_categories: [],
      allowed_tags: [],
    },
    notifications: {
      on_approval: false,
      on_rejection: true,
      on_publish_success: true,
      on_publish_failure: true,
    },
    status: 'active',
  });

  const [showApiKey, setShowApiKey] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);

  // Initialize form data when agent prop changes
  useEffect(() => {
    if (agent) {
      setFormData({
        id: agent.id,
        name: agent.name,
        description: agent.description,
        api_key: agent.api_key,
        rate_limit: { ...agent.rate_limit },
        permissions: { ...agent.permissions },
        notifications: { ...agent.notifications },
        status: agent.status,
      });
    } else {
      // Reset for new agent
      setFormData({
        id: '',
        name: '',
        description: '',
        api_key: '',
        rate_limit: {
          requests_per_minute: 10,
          requests_per_hour: 100,
          requests_per_day: 500,
        },
        permissions: {
          can_submit_articles: true,
          can_edit_own_articles: true,
          can_delete_own_articles: false,
          can_view_statistics: true,
          allowed_categories: [],
          allowed_tags: [],
        },
        notifications: {
          on_approval: false,
          on_rejection: true,
          on_publish_success: true,
          on_publish_failure: true,
        },
        status: 'active',
      });
    }
    setErrors({});
    setIsDirty(false);
  }, [agent, isOpen]);

  // Generate API key
  const generateApiKey = () => {
    const newApiKey = `agent_${uuidv4().replace(/-/g, '')}`;
    setFormData(prev => ({ ...prev, api_key: newApiKey }));
    setIsDirty(true);
  };

  // Copy API key to clipboard
  const copyApiKey = async () => {
    if (formData.api_key) {
      await navigator.clipboard.writeText(formData.api_key);
    }
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = '代理名称为必填项';
    }

    if (!formData.description.trim()) {
      newErrors.description = '代理描述为必填项';
    }

    if (!isEditing && !formData.id.trim()) {
      newErrors.id = '代理ID为必填项';
    }

    if (formData.id && !/^[a-zA-Z0-9-_]+$/.test(formData.id)) {
      newErrors.id = '代理ID只能包含字母、数字、连字符和下划线';
    }

    if (!formData.api_key.trim()) {
      newErrors.api_key = 'API密钥为必填项';
    }

    if (formData.rate_limit.requests_per_minute <= 0) {
      newErrors.requests_per_minute = '每分钟请求数必须大于0';
    }

    if (formData.rate_limit.requests_per_hour <= 0) {
      newErrors.requests_per_hour = '每小时请求数必须大于0';
    }

    if (formData.rate_limit.requests_per_day <= 0) {
      newErrors.requests_per_day = '每日请求数必须大于0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Failed to save agent:', error);
    }
  };

  // Update form field
  const updateField = (path: string, value: any) => {
    setFormData(prev => {
      const newData = { ...prev };
      const keys = path.split('.');
      let current = newData as any;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
          current[keys[i]] = {};
        }
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newData;
    });
    setIsDirty(true);
  };

  // Handle array field changes
  const handleArrayField = (field: string, value: string) => {
    const items = value.split(',').map(item => item.trim()).filter(item => item.length > 0);
    updateField(field, items);
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-4xl w-full bg-white rounded-lg shadow-xl max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              {isEditing ? '编辑代理' : '添加新代理'}
            </Dialog.Title>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-900">基本信息</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    代理名称 *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入代理名称"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    代理ID * {isEditing && '(不可修改)'}
                  </label>
                  <input
                    type="text"
                    value={formData.id}
                    onChange={(e) => updateField('id', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入代理ID"
                    disabled={isEditing}
                  />
                  {errors.id && (
                    <p className="mt-1 text-sm text-red-600">{errors.id}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  描述 *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入代理描述"
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-red-600">{errors.description}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API密钥 *
                </label>
                <div className="flex space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={formData.api_key}
                      onChange={(e) => updateField('api_key', e.target.value)}
                      className="w-full px-3 py-2 pr-20 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="输入或生成API密钥"
                    />
                    <div className="absolute right-2 top-2 flex space-x-1">
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      {formData.api_key && (
                        <button
                          type="button"
                          onClick={copyApiKey}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={generateApiKey}
                    className="flex items-center"
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    生成
                  </Button>
                </div>
                {errors.api_key && (
                  <p className="mt-1 text-sm text-red-600">{errors.api_key}</p>
                )}
              </div>
            </div>

            {/* Rate Limiting */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-900">速率限制</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    每分钟请求数
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.rate_limit.requests_per_minute}
                    onChange={(e) => updateField('rate_limit.requests_per_minute', parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {errors.requests_per_minute && (
                    <p className="mt-1 text-sm text-red-600">{errors.requests_per_minute}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    每小时请求数
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.rate_limit.requests_per_hour}
                    onChange={(e) => updateField('rate_limit.requests_per_hour', parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {errors.requests_per_hour && (
                    <p className="mt-1 text-sm text-red-600">{errors.requests_per_hour}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    每日请求数
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.rate_limit.requests_per_day}
                    onChange={(e) => updateField('rate_limit.requests_per_day', parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {errors.requests_per_day && (
                    <p className="mt-1 text-sm text-red-600">{errors.requests_per_day}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Permissions */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-900">权限设置</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_submit_articles}
                      onChange={(e) => updateField('permissions.can_submit_articles', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    可提交文章
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_edit_own_articles}
                      onChange={(e) => updateField('permissions.can_edit_own_articles', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    可编辑自己的文章
                  </label>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_delete_own_articles}
                      onChange={(e) => updateField('permissions.can_delete_own_articles', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    可删除自己的文章
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_view_statistics}
                      onChange={(e) => updateField('permissions.can_view_statistics', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    可查看统计信息
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    允许的分类（逗号分隔）
                  </label>
                  <input
                    type="text"
                    value={formData.permissions.allowed_categories.join(', ')}
                    onChange={(e) => handleArrayField('permissions.allowed_categories', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="技术, AI, 编程"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    允许的标签（逗号分隔）
                  </label>
                  <input
                    type="text"
                    value={formData.permissions.allowed_tags.join(', ')}
                    onChange={(e) => handleArrayField('permissions.allowed_tags', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ai, tech, tutorial"
                  />
                </div>
              </div>
            </div>

            {/* Notifications */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-900">通知设置</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.notifications.on_approval}
                      onChange={(e) => updateField('notifications.on_approval', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    文章通过审核时通知
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.notifications.on_rejection}
                      onChange={(e) => updateField('notifications.on_rejection', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    文章被拒绝时通知
                  </label>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.notifications.on_publish_success}
                      onChange={(e) => updateField('notifications.on_publish_success', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    发布成功时通知
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.notifications.on_publish_failure}
                      onChange={(e) => updateField('notifications.on_publish_failure', e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    发布失败时通知
                  </label>
                </div>
              </div>
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                状态
              </label>
              <select
                value={formData.status}
                onChange={(e) => updateField('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="active">活跃</option>
                <option value="inactive">不活跃</option>
              </select>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="flex items-center"
              >
                {isLoading && <LoadingSpinner size="sm" className="mr-2" />}
                {isEditing ? '保存更改' : '创建代理'}
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default AgentFormModal;