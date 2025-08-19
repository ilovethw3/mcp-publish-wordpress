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
import { RoleTemplate } from '@/types/role-templates';

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
      can_edit_others_articles: false,
      can_approve_articles: false,
      can_publish_articles: false,
      can_view_statistics: true,
      can_review_agents: [],
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
    role_template_id: undefined,
    permissions_override: {},
  });

  const [showApiKey, setShowApiKey] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);
  const [roleTemplates, setRoleTemplates] = useState<RoleTemplate[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<RoleTemplate | null>(null);
  const [useTemplatePermissions, setUseTemplatePermissions] = useState(true);
  const [availableAgents, setAvailableAgents] = useState<{id: string, name: string}[]>([]);

  // Load role templates
  useEffect(() => {
    const loadRoleTemplates = async () => {
      if (!isOpen) return;
      
      setLoadingRoles(true);
      try {
        const response = await fetch('/api/role-templates');
        const result = await response.json();
        if (result.success) {
          setRoleTemplates(result.data.roles.filter((role: RoleTemplate) => role.is_active));
        }
      } catch (error) {
        console.error('Failed to load role templates:', error);
      } finally {
        setLoadingRoles(false);
      }
    };

    loadRoleTemplates();
  }, [isOpen]);

  // Load available agents for review selection
  useEffect(() => {
    const loadAvailableAgents = async () => {
      if (!isOpen) return;
      
      try {
        const response = await fetch('/api/config/agents');
        const result = await response.json();
        if (result.success) {
          const agents = result.data.agents.map((agent: any) => ({
            id: agent.id,
            name: agent.name
          })).filter((agent: any) => agent.id !== formData.id); // Exclude current agent
          setAvailableAgents(agents);
        }
      } catch (error) {
        console.error('Failed to load available agents:', error);
      }
    };

    loadAvailableAgents();
  }, [isOpen, formData.id]);

  // Initialize form data when agent prop changes
  useEffect(() => {
    if (agent) {
      setFormData({
        id: agent.id,
        name: agent.name,
        description: agent.description,
        api_key: agent.api_key_display || '',  // 使用掩码显示
        rate_limit: { ...agent.rate_limit },
        permissions: { 
          ...agent.permissions,
          can_review_agents: agent.permissions.can_review_agents || [],
          allowed_categories: agent.permissions.allowed_categories || [],
          allowed_tags: agent.permissions.allowed_tags || []
        },
        notifications: { ...agent.notifications },
        status: agent.status,
        role_template_id: agent.role_template_id,
        permissions_override: agent.permissions_override ? { ...agent.permissions_override } : {},
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
          can_edit_others_articles: false,
          can_approve_articles: false,
          can_publish_articles: false,
          can_view_statistics: true,
          can_review_agents: [],
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
        role_template_id: undefined,
        permissions_override: {},
      });
    }
    setErrors({});
    setIsDirty(false);
  }, [agent, isOpen]);

  // Handle role template selection change
  useEffect(() => {
    if (formData.role_template_id) {
      const template = roleTemplates.find(t => t.id === formData.role_template_id);
      setSelectedTemplate(template || null);
      
      // Apply template permissions if using template permissions
      if (template && useTemplatePermissions) {
        setFormData(prev => ({
          ...prev,
          permissions: {
            ...template.permissions
          }
        }));
      }
    } else {
      setSelectedTemplate(null);
    }
  }, [formData.role_template_id, roleTemplates, useTemplatePermissions]);

  // Toggle between template permissions and custom permissions
  const togglePermissionMode = () => {
    setUseTemplatePermissions(!useTemplatePermissions);
    
    if (!useTemplatePermissions && selectedTemplate) {
      // Switching to template permissions - apply template
      setFormData(prev => ({
        ...prev,
        permissions: {
          ...selectedTemplate.permissions
        }
      }));
    }
  };

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

    // API key validation - only required for new agents
    if (!isEditing && !formData.api_key?.trim()) {
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
      // Prepare data for submission
      const submitData = { ...formData };
      
      // If editing and API key looks like a mask, don't include it in submission
      if (isEditing && formData.api_key && formData.api_key.includes('*')) {
        delete submitData.api_key;
      }
      
      
      await onSave(submitData);
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
          <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${isEditing ? 'bg-blue-100' : 'bg-green-100'}`}>
                {isEditing ? (
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                )}
              </div>
              <div>
                <Dialog.Title className="text-lg font-semibold text-gray-900">
                  {isEditing ? '编辑代理配置' : '创建新代理'}
                </Dialog.Title>
                <p className="text-sm text-gray-600 mt-1">
                  {isEditing 
                    ? `正在编辑代理 "${formData.name || '未命名'}" 的配置信息`
                    : '配置新代理的基本信息、权限设置和通知规则'
                  }
                </p>
              </div>
            </div>
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
                
                {/* API Key input */}
                <div className="flex space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={formData.api_key}
                      onChange={(e) => updateField('api_key', e.target.value)}
                      readOnly={!!(isEditing && formData.api_key && formData.api_key.includes('*'))}
                      className="w-full px-3 py-2 pr-20 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 read-only:bg-gray-50 read-only:text-gray-600"
                      placeholder={isEditing ? "当前API密钥（掩码显示）" : "输入或生成API密钥"}
                    />
                    <div className="absolute right-2 top-2 flex space-x-1">
                      {!(isEditing && formData.api_key && formData.api_key.includes('*')) && (
                        <>
                          <button
                            type="button"
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </>
                      )}
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
                    {isEditing ? '重新生成' : '生成'}
                  </Button>
                </div>
                {errors.api_key && (
                  <p className="mt-1 text-sm text-red-600">{errors.api_key}</p>
                )}
              </div>
            </div>

            {/* Role Template Selection */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-900">角色模板 (可选)</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择角色模板
                </label>
                {loadingRoles ? (
                  <div className="flex items-center space-x-2">
                    <LoadingSpinner size="sm" />
                    <span className="text-sm text-gray-600">加载角色模板...</span>
                  </div>
                ) : (
                  <select
                    value={formData.role_template_id || ''}
                    onChange={(e) => {
                      const value = e.target.value;
                      updateField('role_template_id', value === '' ? null : value);
                      setUseTemplatePermissions(true); // 选择模板时默认使用模板权限
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">自定义权限（不使用模板）</option>
                    {roleTemplates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name} - {template.description}
                      </option>
                    ))}
                  </select>
                )}
                
                {/* 模板权限预览 */}
                {selectedTemplate && (
                  <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-md">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700">模板权限预览</h4>
                      <button
                        type="button"
                        onClick={togglePermissionMode}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        {useTemplatePermissions ? '切换到自定义权限' : '使用模板权限'}
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(selectedTemplate.permissions)
                        .filter(([key, value]) => typeof value === 'boolean' && value)
                        .map(([key]) => (
                          <div key={key} className="flex items-center space-x-1">
                            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                            <span className="text-gray-600">
                              {key === 'can_submit_articles' && '可提交文章'}
                              {key === 'can_edit_own_articles' && '可编辑自己文章'}
                              {key === 'can_edit_others_articles' && '可编辑他人文章'}
                              {key === 'can_approve_articles' && '可审批文章'}
                              {key === 'can_publish_articles' && '可发布文章'}
                              {key === 'can_view_statistics' && '可查看统计'}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
                
                <p className="mt-1 text-sm text-gray-500">
                  {selectedTemplate 
                    ? `已选择"${selectedTemplate.name}"模板。${useTemplatePermissions ? '将使用模板权限设置。' : '使用自定义权限设置。'}`
                    : '选择角色模板将自动设置基本权限，或选择"自定义权限"手动配置。'
                  }
                </p>
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
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-md font-medium text-gray-900">权限设置</h3>
                <div className="flex items-center space-x-2">
                  {formData.role_template_id && useTemplatePermissions && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                      使用模板权限
                    </span>
                  )}
                  {formData.role_template_id && !useTemplatePermissions && (
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
                      自定义权限
                    </span>
                  )}
                  {!formData.role_template_id && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
                      完全自定义
                    </span>
                  )}
                </div>
              </div>

              {formData.role_template_id && useTemplatePermissions && (
                <div className="bg-green-50 border border-green-200 rounded-md p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-green-800">
                      正在使用"{selectedTemplate?.name}"模板权限。权限设置已自动配置。
                    </p>
                    <button
                      type="button"
                      onClick={togglePermissionMode}
                      className="text-sm text-green-700 hover:text-green-900 underline"
                    >
                      切换到自定义
                    </button>
                  </div>
                </div>
              )}

              {formData.role_template_id && !useTemplatePermissions && (
                <div className="bg-orange-50 border border-orange-200 rounded-md p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-orange-800">
                      正在自定义权限设置。您可以手动调整所有权限。
                    </p>
                    <button
                      type="button"
                      onClick={togglePermissionMode}
                      className="text-sm text-orange-700 hover:text-orange-900 underline"
                    >
                      使用模板权限
                    </button>
                  </div>
                </div>
              )}
              
              {/* 文章管理权限 */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">📝 文章管理权限</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <label className={`flex items-center ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_submit_articles}
                      onChange={(e) => updateField('permissions.can_submit_articles', e.target.checked)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <span className="text-sm">可提交文章</span>
                  </label>
                  
                  <label className={`flex items-center ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_edit_own_articles}
                      onChange={(e) => updateField('permissions.can_edit_own_articles', e.target.checked)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <span className="text-sm">可编辑自己的文章</span>
                  </label>

                  <label className={`flex items-center ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_edit_others_articles}
                      onChange={(e) => updateField('permissions.can_edit_others_articles', e.target.checked)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <span className="text-sm">可编辑他人文章</span>
                  </label>
                </div>
              </div>

              {/* 审批发布权限 */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">✅ 审批发布权限</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <label className={`flex items-center ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_approve_articles}
                      onChange={(e) => updateField('permissions.can_approve_articles', e.target.checked)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <span className="text-sm">可审批文章</span>
                  </label>

                  <label className={`flex items-center ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_publish_articles}
                      onChange={(e) => updateField('permissions.can_publish_articles', e.target.checked)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <span className="text-sm">可发布文章</span>
                  </label>
                </div>
              </div>

              {/* 系统管理权限 */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">⚙️ 系统管理权限</h4>
                <div className="space-y-3">
                  <label className={`flex items-center ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                    <input
                      type="checkbox"
                      checked={formData.permissions.can_view_statistics}
                      onChange={(e) => updateField('permissions.can_view_statistics', e.target.checked)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <span className="text-sm">可查看统计信息</span>
                  </label>

                  <div className={formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      可审核的代理
                    </label>
                    
                    {availableAgents.length > 0 ? (
                      <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded-md p-2">
                        {availableAgents.map((agent) => (
                          <label key={agent.id} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={formData.permissions.can_review_agents?.includes(agent.id) || false}
                              onChange={(e) => {
                                const currentAgents = formData.permissions.can_review_agents || [];
                                if (e.target.checked) {
                                  updateField('permissions.can_review_agents', [...currentAgents, agent.id]);
                                } else {
                                  updateField('permissions.can_review_agents', currentAgents.filter(id => id !== agent.id));
                                }
                              }}
                              disabled={!!(formData.role_template_id && useTemplatePermissions)}
                              className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                            />
                            <span className="text-sm">{agent.name} ({agent.id})</span>
                          </label>
                        ))}
                      </div>
                    ) : (
                      <input
                        type="text"
                        value={formData.permissions.can_review_agents?.join(', ') || ''}
                        onChange={(e) => handleArrayField('permissions.can_review_agents', e.target.value)}
                        disabled={!!(formData.role_template_id && useTemplatePermissions)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
                        placeholder="agent-1, agent-2 (留空表示不可审核其他代理)"
                      />
                    )}
                    
                    <p className="mt-1 text-xs text-gray-500">
                      选择此代理可以审核哪些其他代理的文章，不选择表示不具有审核权限
                    </p>
                    
                    {(formData.permissions.can_review_agents?.length || 0) > 0 && (
                      <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                        <span className="font-medium">已选择: </span>
                        {formData.permissions.can_review_agents?.join(', ') || ''}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 内容限制设置 */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">🏷️ 内容限制设置</h4>
                <div className={`grid grid-cols-1 md:grid-cols-2 gap-4 ${formData.role_template_id && useTemplatePermissions ? 'opacity-60' : ''}`}>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      允许的分类（逗号分隔）
                    </label>
                    <input
                      type="text"
                      value={formData.permissions.allowed_categories?.join(', ') || ''}
                      onChange={(e) => handleArrayField('permissions.allowed_categories', e.target.value)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
                      placeholder="技术, AI, 编程"
                    />
                    <p className="mt-1 text-xs text-gray-500">留空表示允许所有分类</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      允许的标签（逗号分隔）
                    </label>
                    <input
                      type="text"
                      value={formData.permissions.allowed_tags?.join(', ') || ''}
                      onChange={(e) => handleArrayField('permissions.allowed_tags', e.target.value)}
                      disabled={!!(formData.role_template_id && useTemplatePermissions)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
                      placeholder="ai, tech, tutorial"
                    />
                    <p className="mt-1 text-xs text-gray-500">留空表示允许所有标签</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 权限预览面板 */}
            <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
              <h4 className="text-sm font-medium text-blue-900 mb-3">🔍 权限预览</h4>
              <div className="space-y-3">
                {/* 文章管理权限预览 */}
                <div>
                  <h5 className="text-xs font-medium text-blue-800 mb-2">📝 文章管理权限</h5>
                  <div className="flex flex-wrap gap-2">
                    {formData.permissions.can_submit_articles && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        提交文章
                      </span>
                    )}
                    {formData.permissions.can_edit_own_articles && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        编辑自己的文章
                      </span>
                    )}
                    {formData.permissions.can_edit_others_articles && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        编辑他人文章
                      </span>
                    )}
                  </div>
                </div>

                {/* 审批发布权限预览 */}
                <div>
                  <h5 className="text-xs font-medium text-blue-800 mb-2">✅ 审批发布权限</h5>
                  <div className="flex flex-wrap gap-2">
                    {formData.permissions.can_approve_articles && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        审批文章
                      </span>
                    )}
                    {formData.permissions.can_publish_articles && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        发布文章
                      </span>
                    )}
                  </div>
                </div>

                {/* 系统管理权限预览 */}
                <div>
                  <h5 className="text-xs font-medium text-blue-800 mb-2">⚙️ 系统管理权限</h5>
                  <div className="flex flex-wrap gap-2">
                    {formData.permissions.can_view_statistics && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        查看统计信息
                      </span>
                    )}
                    {(formData.permissions.can_review_agents?.length || 0) > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        审查代理 ({formData.permissions.can_review_agents?.length || 0}个)
                      </span>
                    )}
                  </div>
                </div>

                {/* 内容限制预览 */}
                <div>
                  <h5 className="text-xs font-medium text-blue-800 mb-2">🏷️ 内容限制设置</h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-blue-700 font-medium">允许分类：</span>
                      <span className="text-blue-600">
                        {(formData.permissions.allowed_categories?.length || 0) > 0 
                          ? `${formData.permissions.allowed_categories?.length || 0}个分类`
                          : '不限制'
                        }
                      </span>
                    </div>
                    <div>
                      <span className="text-blue-700 font-medium">允许标签：</span>
                      <span className="text-blue-600">
                        {(formData.permissions.allowed_tags?.length || 0) > 0 
                          ? `${formData.permissions.allowed_tags?.length || 0}个标签`
                          : '不限制'
                        }
                      </span>
                    </div>
                  </div>
                </div>

                {/* 角色模板状态 */}
                {formData.role_template_id && (
                  <div className="pt-2 border-t border-blue-300">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-blue-700">
                        🎭 应用角色模板: <span className="font-medium">{selectedTemplate?.name || formData.role_template_id}</span>
                      </span>
                      <span className="text-xs text-blue-600">
                        {useTemplatePermissions ? '使用模板权限' : '自定义权限'}
                      </span>
                    </div>
                  </div>
                )}
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
            <div className="flex justify-between items-center pt-6 border-t border-gray-200">
              {/* 左侧提示信息 */}
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                {isEditing ? (
                  <>
                    <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                    <span>编辑现有代理配置</span>
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    <span>创建新代理</span>
                  </>
                )}
              </div>
              
              {/* 右侧操作按钮 */}
              <div className="flex space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={isLoading}
                  className="px-6"
                >
                  取消
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="flex items-center px-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:ring-blue-500"
                >
                  {isLoading && <LoadingSpinner size="sm" className="mr-2" />}
                  {isLoading ? (
                    isEditing ? '保存中...' : '创建中...'
                  ) : (
                    <>
                      {isEditing ? (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          保存更改
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          创建代理
                        </>
                      )}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default AgentFormModal;