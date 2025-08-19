'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useToastContext } from '@/contexts/ToastContext';
import { useUsers, createUser, updateUser, deleteUser, changePassword } from '@/hooks/useUsers';
import { useForm } from 'react-hook-form';
import { UserPlus, Edit, Trash2, Key, Search } from 'lucide-react';

interface User {
  id: number;
  username: string;
  email: string;
  is_reviewer: boolean;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

interface UserFormData {
  username: string;
  email: string;
  password?: string;
  is_reviewer: boolean;
}

interface PasswordFormData {
  new_password: string;
  confirm_password: string;
}

export default function UsersPage() {
  const { showSuccess, showError } = useToastContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(true); // 默认只显示活跃用户
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { users, loading, refresh } = useUsers({
    search: searchTerm,
    is_active: filterActive,
  });

  const {
    register: registerCreate,
    handleSubmit: handleCreateSubmit,
    reset: resetCreate,
    formState: { errors: createErrors },
  } = useForm<UserFormData>();

  const {
    register: registerEdit,
    handleSubmit: handleEditSubmit,
    reset: resetEdit,
    setValue: setEditValue,
    formState: { errors: editErrors },
  } = useForm<UserFormData>();

  const {
    register: registerPassword,
    handleSubmit: handlePasswordSubmit,
    reset: resetPassword,
    watch: watchPassword,
    formState: { errors: passwordErrors },
  } = useForm<PasswordFormData>();

  const onCreateUser = async (data: UserFormData) => {
    setIsSubmitting(true);
    try {
      await createUser({
        username: data.username,
        email: data.email,
        password: data.password!,
        is_reviewer: data.is_reviewer,
      });
      showSuccess('用户创建成功！');
      setShowCreateModal(false);
      resetCreate();
      refresh();
    } catch (error: any) {
      showError(error.message || '创建用户失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const onEditUser = async (data: UserFormData) => {
    if (!selectedUser) return;
    
    setIsSubmitting(true);
    try {
      await updateUser(selectedUser.id, {
        username: data.username,
        email: data.email,
        is_reviewer: data.is_reviewer,
      });
      showSuccess('用户信息更新成功！');
      setShowEditModal(false);
      setSelectedUser(null);
      refresh();
    } catch (error: any) {
      showError(error.message || '更新用户失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const onChangePassword = async (data: PasswordFormData) => {
    if (!selectedUser) return;
    
    setIsSubmitting(true);
    try {
      await changePassword(selectedUser.id, data.new_password);
      showSuccess('密码修改成功！');
      setShowPasswordModal(false);
      setSelectedUser(null);
      resetPassword();
    } catch (error: any) {
      showError(error.message || '密码修改失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeleteModal = (user: User) => {
    setSelectedUser(user);
    setShowDeleteModal(true);
  };

  const onConfirmDelete = async () => {
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      await deleteUser(selectedUser.id);
      showSuccess('用户删除成功！');
      setShowDeleteModal(false);
      setSelectedUser(null);
      refresh();
    } catch (error: any) {
      showError(error.message || '删除用户失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditModal = (user: User) => {
    setSelectedUser(user);
    setEditValue('username', user.username);
    setEditValue('email', user.email);
    setEditValue('is_reviewer', user.is_reviewer);
    setShowEditModal(true);
  };

  const openPasswordModal = (user: User) => {
    setSelectedUser(user);
    setShowPasswordModal(true);
  };

  return (
    <ProtectedRoute requireReviewer={true}>
      <DashboardLayout>
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">用户管理</h2>
              <p className="mt-1 text-sm text-gray-600">
                管理系统用户账户和权限
              </p>
            </div>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2"
            >
              <UserPlus className="w-4 h-4" />
              <span>创建用户</span>
            </Button>
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="搜索用户名或邮箱..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={filterActive === undefined ? 'all' : filterActive.toString()}
                    onChange={(e) => {
                      const value = e.target.value;
                      setFilterActive(value === 'all' ? undefined : value === 'true');
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">所有状态</option>
                    <option value="true">活跃用户</option>
                    <option value="false">已停用</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Users Table */}
          <Card>
            <CardHeader>
              <CardTitle>用户列表</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : users.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          用户信息
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          权限
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          状态
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          最后登录
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {user.username}
                              </div>
                              <div className="text-sm text-gray-500">
                                {user.email}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.is_reviewer
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {user.is_reviewer ? '审核员' : '普通用户'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {user.is_active ? '活跃' : '已停用'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.last_login
                              ? new Date(user.last_login).toLocaleString('zh-CN')
                              : '从未登录'
                            }
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => openEditModal(user)}
                                className="text-blue-600 hover:text-blue-900"
                                title="编辑用户"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => openPasswordModal(user)}
                                className="text-green-600 hover:text-green-900"
                                title="修改密码"
                              >
                                <Key className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => openDeleteModal(user)}
                                className="text-red-600 hover:text-red-900"
                                title="删除用户"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  暂无用户数据
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Create User Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">创建新用户</h3>
              
              <form onSubmit={handleCreateSubmit(onCreateUser)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    用户名
                  </label>
                  <input
                    {...registerCreate('username', {
                      required: '用户名不能为空',
                      minLength: { value: 3, message: '用户名至少3个字符' }
                    })}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {createErrors.username && (
                    <p className="mt-1 text-sm text-red-600">{createErrors.username.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    邮箱
                  </label>
                  <input
                    {...registerCreate('email', {
                      required: '邮箱不能为空',
                      pattern: { value: /^\S+@\S+$/i, message: '请输入有效的邮箱地址' }
                    })}
                    type="email"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {createErrors.email && (
                    <p className="mt-1 text-sm text-red-600">{createErrors.email.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    密码
                  </label>
                  <input
                    {...registerCreate('password', {
                      required: '密码不能为空',
                      minLength: { value: 8, message: '密码至少8个字符' }
                    })}
                    type="password"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {createErrors.password && (
                    <p className="mt-1 text-sm text-red-600">{createErrors.password.message}</p>
                  )}
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      {...registerCreate('is_reviewer')}
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">审核员权限</span>
                  </label>
                </div>

                <div className="flex space-x-3 justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateModal(false);
                      resetCreate();
                    }}
                  >
                    取消
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? '创建中...' : '创建'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit User Modal */}
        {showEditModal && selectedUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">编辑用户</h3>
              
              <form onSubmit={handleEditSubmit(onEditUser)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    用户名
                  </label>
                  <input
                    {...registerEdit('username', {
                      required: '用户名不能为空',
                      minLength: { value: 3, message: '用户名至少3个字符' }
                    })}
                    type="text"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {editErrors.username && (
                    <p className="mt-1 text-sm text-red-600">{editErrors.username.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    邮箱
                  </label>
                  <input
                    {...registerEdit('email', {
                      required: '邮箱不能为空',
                      pattern: { value: /^\S+@\S+$/i, message: '请输入有效的邮箱地址' }
                    })}
                    type="email"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {editErrors.email && (
                    <p className="mt-1 text-sm text-red-600">{editErrors.email.message}</p>
                  )}
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      {...registerEdit('is_reviewer')}
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">审核员权限</span>
                  </label>
                </div>

                <div className="flex space-x-3 justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowEditModal(false);
                      setSelectedUser(null);
                      resetEdit();
                    }}
                  >
                    取消
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? '更新中...' : '更新'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Change Password Modal */}
        {showPasswordModal && selectedUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">修改密码</h3>
              <p className="text-sm text-gray-600 mb-4">
                为用户 "{selectedUser.username}" 设置新密码
              </p>
              
              <form onSubmit={handlePasswordSubmit(onChangePassword)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    新密码
                  </label>
                  <input
                    {...registerPassword('new_password', {
                      required: '新密码不能为空',
                      minLength: { value: 8, message: '密码至少8个字符' }
                    })}
                    type="password"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {passwordErrors.new_password && (
                    <p className="mt-1 text-sm text-red-600">{passwordErrors.new_password.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    确认密码
                  </label>
                  <input
                    {...registerPassword('confirm_password', {
                      required: '请确认密码',
                      validate: (value) => {
                        const newPassword = watchPassword('new_password');
                        return value === newPassword || '两次输入的密码不一致';
                      }
                    })}
                    type="password"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {passwordErrors.confirm_password && (
                    <p className="mt-1 text-sm text-red-600">{passwordErrors.confirm_password.message}</p>
                  )}
                </div>

                <div className="flex space-x-3 justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowPasswordModal(false);
                      setSelectedUser(null);
                      resetPassword();
                    }}
                  >
                    取消
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? '修改中...' : '修改密码'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && selectedUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4 text-red-600">确认删除用户</h3>
              <p className="text-sm text-gray-600 mb-6">
                您确定要删除用户 "<span className="font-semibold">{selectedUser.username}</span>" 吗？
              </p>
              <p className="text-sm text-red-500 mb-6">
                ⚠️ 此操作将使该用户无法登录系统，但历史数据将被保留。
              </p>
              
              <div className="flex space-x-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setSelectedUser(null);
                  }}
                  disabled={isSubmitting}
                >
                  取消
                </Button>
                <Button
                  onClick={onConfirmDelete}
                  disabled={isSubmitting}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  {isSubmitting ? '删除中...' : '确认删除'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedRoute>
  );
}