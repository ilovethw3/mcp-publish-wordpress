'use client';

import React, { useState, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { RoleTemplate, RoleTemplateFormData, PERMISSION_LABELS } from '@/types/role-templates';
import { useToastContext } from '@/contexts/ToastContext';
import RoleTemplateFormModal from '@/components/roles/RoleTemplateFormModal';

const RoleTemplatesPage = () => {
  const [roles, setRoles] = useState<RoleTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleTemplate | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingRole, setDeletingRole] = useState<RoleTemplate | null>(null);
  const { showSuccess, showError } = useToastContext();

  useEffect(() => {
    loadRoles();
  }, []);

  const loadRoles = async () => {
    try {
      const response = await fetch('/api/role-templates?includeInactive=true');
      const result = await response.json();
      if (result.success) {
        setRoles(result.data.roles);
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Failed to load roles:', error);
      showError('加载角色模板失败');
    } finally {
      setLoading(false);
    }
  };

  const createRole = async (roleData: RoleTemplateFormData) => {
    try {
      const response = await fetch('/api/role-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(roleData)
      });

      const result = await response.json();
      if (result.success) {
        await loadRoles();
        setShowCreateModal(false);
        showSuccess('角色模板创建成功');
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Failed to create role:', error);
      showError(`创建角色模板失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const updateRole = async (roleId: string, roleData: RoleTemplateFormData) => {
    try {
      const response = await fetch(`/api/role-templates/${roleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(roleData)
      });

      const result = await response.json();
      if (result.success) {
        await loadRoles();
        setEditingRole(null);
        showSuccess('角色模板更新成功');
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Failed to update role:', error);
      showError(`更新角色模板失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const toggleRoleStatus = async (roleId: string, isActive: boolean) => {
    try {
      const response = await fetch('/api/role-templates/toggle-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role_id: roleId, is_active: isActive })
      });

      const result = await response.json();
      if (result.success) {
        await loadRoles();
        showSuccess(`角色模板${isActive ? '启用' : '停用'}成功`);
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Failed to toggle role status:', error);
      showError(`切换角色模板状态失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const openDeleteModal = (role: RoleTemplate) => {
    setDeletingRole(role);
    setShowDeleteModal(true);
  };

  const closeDeleteModal = () => {
    setShowDeleteModal(false);
    setDeletingRole(null);
  };

  const confirmDeleteRole = async () => {
    if (!deletingRole) return;

    try {
      const response = await fetch(`/api/role-templates/${deletingRole.id}`, {
        method: 'DELETE'
      });

      const result = await response.json();
      if (result.success) {
        await loadRoles();
        showSuccess('角色模板删除成功');
        closeDeleteModal();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Failed to delete role:', error);
      showError(`删除角色模板失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">加载中...</div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">角色模板管理</h1>
          <p className="text-gray-600">管理系统角色模板和权限配置</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          创建角色模板
        </button>
      </div>

      {/* Role List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {roles.map((role) => (
          <div key={role.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900">{role.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{role.description}</p>
              </div>
              <div className="flex items-center space-x-2">
                {role.is_system_role && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                    系统
                  </span>
                )}
                {!role.is_active && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                    已停用
                  </span>
                )}
              </div>
            </div>

            {/* Permission Summary */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">权限概览</h4>
              <div className="space-y-1">
                {Object.entries(role.permissions)
                  .filter(([key, value]) => typeof value === 'boolean' && value)
                  .map(([key]) => (
                    <div key={key} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-xs text-gray-600">
                        {PERMISSION_LABELS[key as keyof typeof PERMISSION_LABELS] || key}
                      </span>
                    </div>
                  ))
                }
              </div>
            </div>

            {/* Quota Information */}
            {role.quota_limits && (
              role.quota_limits.daily_articles !== undefined || 
              role.quota_limits.monthly_articles !== undefined
            ) && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">配额限制</h4>
                <div className="space-y-1">
                  {role.quota_limits.daily_articles !== undefined && (
                    <div className="text-xs text-gray-600">
                      日配额: {role.quota_limits.daily_articles === 0 ? '无限制' : `${role.quota_limits.daily_articles}篇`}
                    </div>
                  )}
                  {role.quota_limits.monthly_articles !== undefined && (
                    <div className="text-xs text-gray-600">
                      月配额: {role.quota_limits.monthly_articles === 0 ? '无限制' : `${role.quota_limits.monthly_articles}篇`}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-2">
              <button
                onClick={() => setEditingRole(role)}
                className="flex-1 px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 transition-colors"
              >
                编辑
              </button>
              {!role.is_system_role && (
                <>
                  <button
                    onClick={() => toggleRoleStatus(role.id, !role.is_active)}
                    className={`flex-1 px-3 py-1 rounded text-sm transition-colors ${
                      role.is_active 
                        ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {role.is_active ? '停用' : '启用'}
                  </button>
                  <button
                    onClick={() => openDeleteModal(role)}
                    className="flex-1 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200 transition-colors"
                  >
                    删除
                  </button>
                </>
              )}
            </div>

            {/* Metadata */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="text-xs text-gray-500">
                创建时间: {new Date(role.created_at).toLocaleString('zh-CN')}
              </div>
              {role.created_by && (
                <div className="text-xs text-gray-500">
                  创建者: {role.created_by}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {roles.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">暂无角色模板</div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            创建第一个角色模板
          </button>
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateModal || editingRole) && (
        <RoleTemplateFormModal
          role={editingRole}
          isOpen={true}
          onClose={() => {
            setShowCreateModal(false);
            setEditingRole(null);
          }}
          onSubmit={editingRole ? 
            (data) => updateRole(editingRole.id, data) : 
            createRole
          }
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingRole && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.866-.833-2.536 0L3.278 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-gray-900">确认删除</h3>
                </div>
              </div>
              <div className="mb-6">
                <p className="text-gray-600">
                  确定要删除角色模板 <span className="font-semibold text-gray-900">"{deletingRole.name}"</span> 吗？
                </p>
                <p className="text-sm text-red-600 mt-2">
                  删除后的角色模板将被标记为已删除，但数据不会完全丢失。
                </p>
              </div>
              <div className="flex space-x-3 justify-end">
                <button
                  onClick={closeDeleteModal}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  取消
                </button>
                <button
                  onClick={confirmDeleteRole}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  确认删除
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </DashboardLayout>
  );
};

export default RoleTemplatesPage;