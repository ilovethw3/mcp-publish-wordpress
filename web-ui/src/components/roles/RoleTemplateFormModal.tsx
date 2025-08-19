'use client';

import React, { useState, useEffect } from 'react';
import { RoleTemplate, RoleTemplateFormData, PERMISSION_LABELS, WORKING_DAYS_LABELS, COMMON_TIMEZONES } from '@/types/role-templates';

interface RoleTemplateFormModalProps {
  role?: RoleTemplate | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: RoleTemplateFormData) => void;
}

const RoleTemplateFormModal: React.FC<RoleTemplateFormModalProps> = ({
  role,
  isOpen,
  onClose,
  onSubmit
}) => {
  const [formData, setFormData] = useState<RoleTemplateFormData>({
    role_id: '',
    name: '',
    description: '',
    permissions: {
      can_submit_articles: true,
      can_edit_own_articles: true,
      can_edit_others_articles: false,
      can_approve_articles: false,
      can_publish_articles: false,
      can_view_statistics: true,
      can_review_agents: [],
      allowed_categories: [],
      allowed_tags: []
    },
    quota_limits: {
      daily_articles: 0,
      monthly_articles: 0,
      working_hours: {
        enabled: false,
        start: '09:00',
        end: '18:00',
        timezone: 'Asia/Shanghai',
        working_days: [1, 2, 3, 4, 5]
      }
    }
  });

  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (role) {
      setFormData({
        role_id: role.id,
        name: role.name,
        description: role.description,
        permissions: { ...role.permissions },
        quota_limits: { ...role.quota_limits }
      });
    } else {
      // Reset form for new role
      setFormData({
        role_id: '',
        name: '',
        description: '',
        permissions: {
          can_submit_articles: true,
          can_edit_own_articles: true,
          can_edit_others_articles: false,
          can_approve_articles: false,
          can_publish_articles: false,
          can_view_statistics: true,
          can_review_agents: [],
          allowed_categories: [],
          allowed_tags: []
        },
        quota_limits: {
          daily_articles: 0,
          monthly_articles: 0,
          working_hours: {
            enabled: false,
            start: '09:00',
            end: '18:00',
            timezone: 'Asia/Shanghai',
            working_days: [1, 2, 3, 4, 5]
          }
        }
      });
    }
    setErrors([]);
  }, [role]);

  const validateForm = (): boolean => {
    const newErrors: string[] = [];

    if (!formData.name.trim()) {
      newErrors.push('角色名称不能为空');
    }

    if (!formData.description.trim()) {
      newErrors.push('角色描述不能为空');
    }

    if (!role && !formData.role_id?.trim()) {
      newErrors.push('角色ID不能为空');
    }

    if (!role && formData.role_id && !/^[a-zA-Z0-9-_]+$/.test(formData.role_id)) {
      newErrors.push('角色ID只能包含字母、数字、连字符和下划线');
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Clean up the data before submitting
    const submitData: RoleTemplateFormData = {
      ...formData,
      name: formData.name.trim(),
      description: formData.description.trim(),
    };

    // Don't send role_id for existing roles
    if (role) {
      delete submitData.role_id;
    }

    onSubmit(submitData);
  };

  const updatePermission = (permission: string, value: boolean) => {
    setFormData(prev => ({
      ...prev,
      permissions: {
        ...prev.permissions,
        [permission]: value
      }
    }));
  };

  const updateQuotaLimit = (field: string, value: number) => {
    setFormData(prev => ({
      ...prev,
      quota_limits: {
        ...prev.quota_limits,
        [field]: value
      }
    }));
  };

  const updateWorkingHours = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      quota_limits: {
        ...prev.quota_limits,
        working_hours: {
          ...prev.quota_limits.working_hours!,
          [field]: value
        }
      }
    }));
  };

  const toggleWorkingDay = (day: number) => {
    const currentDays = formData.quota_limits.working_hours?.working_days || [];
    const newDays = currentDays.includes(day)
      ? currentDays.filter(d => d !== day)
      : [...currentDays, day].sort();
    
    updateWorkingHours('working_days', newDays);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            {role ? '编辑角色模板' : '创建角色模板'}
          </h3>

          {errors.length > 0 && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded-md">
              <ul className="text-red-700 text-sm">
                {errors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {!role && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    角色ID *
                  </label>
                  <input
                    type="text"
                    value={formData.role_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, role_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="例如: content_creator"
                  />
                </div>
              )}
              
              <div className={!role ? '' : 'md:col-span-2'}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  角色名称 *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 内容创建者"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                角色描述 *
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="描述这个角色的用途和职责"
              />
            </div>

            {/* Permissions */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">权限设置</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(PERMISSION_LABELS).map(([key, label]) => (
                  <label key={key} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.permissions[key]}
                      onChange={(e) => updatePermission(key, e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">{label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Quota Limits */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">配额限制</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    每日文章限制 (0 = 无限制)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.quota_limits.daily_articles || 0}
                    onChange={(e) => updateQuotaLimit('daily_articles', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    每月文章限制 (0 = 无限制)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.quota_limits.monthly_articles || 0}
                    onChange={(e) => updateQuotaLimit('monthly_articles', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Working Hours */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">工作时间限制</h4>
              
              <label className="flex items-center space-x-2 mb-4">
                <input
                  type="checkbox"
                  checked={formData.quota_limits.working_hours?.enabled || false}
                  onChange={(e) => updateWorkingHours('enabled', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">启用工作时间限制</span>
              </label>

              {formData.quota_limits.working_hours?.enabled && (
                <div className="space-y-4 ml-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        开始时间
                      </label>
                      <input
                        type="time"
                        value={formData.quota_limits.working_hours?.start || '09:00'}
                        onChange={(e) => updateWorkingHours('start', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        结束时间
                      </label>
                      <input
                        type="time"
                        value={formData.quota_limits.working_hours?.end || '18:00'}
                        onChange={(e) => updateWorkingHours('end', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        时区
                      </label>
                      <select
                        value={formData.quota_limits.working_hours?.timezone || 'Asia/Shanghai'}
                        onChange={(e) => updateWorkingHours('timezone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {COMMON_TIMEZONES.map(tz => (
                          <option key={tz.value} value={tz.value}>{tz.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      工作日
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(WORKING_DAYS_LABELS).map(([day, label]) => (
                        <label key={day} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={formData.quota_limits.working_hours?.working_days?.includes(parseInt(day)) || false}
                            onChange={() => toggleWorkingDay(parseInt(day))}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="text-sm text-gray-700">{label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex space-x-3 justify-end pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
              >
                取消
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                {role ? '更新' : '创建'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RoleTemplateFormModal;