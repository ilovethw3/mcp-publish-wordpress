'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatsCard from '@/components/ui/StatsCard';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useAgents, useAgentStats, useAgentArticles } from '@/hooks/useMCPData';
import { useAgentConfig, useToast } from '@/hooks/useConfigManagement';
import AgentFormModal from '@/components/config/AgentFormModal';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { ToastContainer } from '@/components/ui/Toast';
import { Agent, FullConfigAgent } from '@/types';
import { Plus, Edit, Trash2 } from 'lucide-react';

// 类型转换辅助函数
const agentToFullConfigAgent = (agent: Agent): FullConfigAgent | null => {
  // 检查是否有必需的配置字段（来自数据库的代理应该有完整配置）
  if (!agent.rate_limit || !agent.permissions || !agent.notifications) {
    return null;
  }
  
  return {
    id: agent.id,
    name: agent.name,
    status: agent.status,
    description: agent.description || '',
    api_key: agent.api_key_display, // 使用掩码显示
    api_key_display: agent.api_key_display, // 添加掩码字段
    rate_limit: agent.rate_limit,
    permissions: agent.permissions,
    notifications: agent.notifications,
    role_template_id: agent.role_template_id, // 添加角色模板支持
    permissions_override: agent.permissions_override,
    total_articles_submitted: agent.total_articles_submitted,
    total_articles_published: agent.total_articles_published,
    total_articles_rejected: agent.total_articles_rejected,
    success_rate: agent.success_rate,
    created_at: agent.created_at,
    updated_at: agent.updated_at,
  };
};

interface AgentDetailModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ agent, isOpen, onClose }) => {
  const { stats, loading: statsLoading } = useAgentStats(agent.id);
  const { articles, loading: articlesLoading } = useAgentArticles(agent.id);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{agent.name}</h2>
              <p className="text-gray-600">代理ID: {agent.id}</p>
            </div>
            <Button variant="outline" onClick={onClose}>
              关闭
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Agent Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard
              title="总提交数"
              value={agent.total_articles_submitted || 0}
              color="primary"
              loading={false}
            />
            <StatsCard
              title="发布成功"
              value={agent.total_articles_published || 0}
              color="success"
              loading={false}
            />
            <StatsCard
              title="成功率"
              value={`${agent.success_rate || 0}%`}
              color={(agent.success_rate || 0) >= 80 ? 'success' : 'warning'}
              loading={false}
            />
          </div>

          {/* Detailed Stats */}
          {statsLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : stats ? (
            <Card>
              <CardHeader>
                <CardTitle>详细统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">待审核</div>
                    <div className="font-semibold">{stats?.statistics?.pending_review || 0}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">已拒绝</div>
                    <div className="font-semibold">{stats?.statistics?.total_rejected || agent.total_articles_rejected || 0}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">首次提交</div>
                    <div className="font-semibold">
                      {stats?.statistics?.first_submission 
                        ? new Date(stats.statistics.first_submission).toLocaleDateString('zh-CN')
                        : agent.created_at
                        ? new Date(agent.created_at).toLocaleDateString('zh-CN')
                        : '-'
                      }
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">最近提交</div>
                    <div className="font-semibold">
                      {stats?.statistics?.last_submission
                        ? new Date(stats.statistics.last_submission).toLocaleDateString('zh-CN')
                        : agent.updated_at
                        ? new Date(agent.updated_at).toLocaleDateString('zh-CN')
                        : '-'
                      }
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {/* Recent Articles */}
          <Card>
            <CardHeader>
              <CardTitle>最近文章</CardTitle>
            </CardHeader>
            <CardContent>
              {articlesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : articles.length > 0 ? (
                <div className="space-y-4 max-h-64 overflow-y-auto">
                  {articles.slice(0, 10).map((article) => (
                    <div key={article.id} className="flex justify-between items-center border-b border-gray-100 pb-2">
                      <div>
                        <div className="font-medium text-gray-900">{article.title}</div>
                        <div className="text-sm text-gray-500">
                          {new Date(article.created_at).toLocaleDateString('zh-CN')}
                        </div>
                      </div>
                      <StatusBadge status={article.status} size="sm" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  该代理暂无文章记录
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const AgentsPage = () => {
  // Original state
  const [includeInactive, setIncludeInactive] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  
  // New configuration management state
  const [showAgentForm, setShowAgentForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState<FullConfigAgent | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);

  // Hooks
  const { 
    agents, 
    total, 
    loading, 
    error, 
    refresh 
  } = useAgents(includeInactive);

  const {
    agents: configAgents,
    loading: configLoading,
    isOperating,
    createAgent,
    updateAgent,
    deleteAgent,
    refresh: refreshConfig,
  } = useAgentConfig();

  const { toasts, showToast, removeToast } = useToast();

  // Merge data from both sources (MCP runtime data + configuration data)
  // Use MCP data for statistics, config data for permissions/settings
  const mergedAgents = agents.map(agent => {
    const configAgent = configAgents.find((ca: any) => ca.id === agent.id);
    if (configAgent) {
      // Keep MCP statistics, use config for settings
      return {
        ...configAgent, // Start with config data (permissions, etc.)
        // Override with MCP statistics
        total_articles_submitted: agent.total_articles_submitted,
        total_articles_published: agent.total_articles_published,
        total_articles_rejected: agent.total_articles_rejected,
        success_rate: agent.success_rate,
        // Keep config data for critical settings
        permissions: configAgent.permissions,
        rate_limit: configAgent.rate_limit,
        notifications: configAgent.notifications,
        api_key_display: configAgent.api_key_display,
        role_template_id: configAgent.role_template_id,
        permissions_override: configAgent.permissions_override,
      };
    }
    return agent;
  });

  // Add config-only agents (that may not have runtime data yet)
  const configOnlyAgents = configAgents.filter(
    (ca: any) => !agents.find(a => a.id === ca.id)
  ).map((ca: any) => ({
    ...ca,
    total_articles_submitted: 0,
    total_articles_published: 0,
    total_articles_rejected: 0,
    success_rate: 0,
  }));

  const allAgents = [...mergedAgents, ...configOnlyAgents];
  
  const activeAgents = allAgents.filter(agent => agent.status === 'active');
  const totalArticles = allAgents.reduce((sum, agent) => sum + (agent.total_articles_submitted || 0), 0);
  const totalPublished = allAgents.reduce((sum, agent) => sum + (agent.total_articles_published || 0), 0);
  const averageSuccessRate = allAgents.length > 0 
    ? allAgents.reduce((sum, agent) => sum + (Number(agent.success_rate) || 0), 0) / allAgents.length 
    : 0;

  // Handlers
  const handleCreateAgent = () => {
    setEditingAgent(null);
    setShowAgentForm(true);
  };

  const handleEditAgent = (agent: Agent) => {
    const configAgent = agentToFullConfigAgent(agent);
    if (!configAgent) {
      showToast('error', '无法编辑：代理缺少配置信息');
      return;
    }
    
    setEditingAgent(configAgent);
    setShowAgentForm(true);
  };

  const handleDeleteAgent = (agent: Agent) => {
    setAgentToDelete(agent);
    setShowDeleteConfirm(true);
  };

  const handleSaveAgent = async (agentData: any) => {
    try {
      if (editingAgent) {
        await updateAgent(editingAgent.id, agentData);
        showToast('success', '代理更新成功');
      } else {
        await createAgent(agentData);
        showToast('success', '代理创建成功');
      }
      
      // Force refresh both data sources
      await Promise.all([
        refresh(), // Refresh MCP data
        refreshConfig() // Refresh config data
      ]);
    } catch (error) {
      showToast('error', `操作失败: ${error instanceof Error ? error.message : '未知错误'}`);
      throw error;
    }
  };

  const handleConfirmDelete = async () => {
    if (!agentToDelete) return;

    try {
      await deleteAgent(agentToDelete.id);
      showToast('success', '代理删除成功');
      refresh();
      refreshConfig();
      setShowDeleteConfirm(false);
      setAgentToDelete(null);
    } catch (error) {
      showToast('error', `删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">代理管理</h2>
            <p className="mt-1 text-sm text-gray-600">
              管理所有AI代理的状态和性能
            </p>
          </div>
          <div className="flex space-x-3">
            <Button variant="outline" onClick={() => refresh()} disabled={loading || configLoading}>
              {(loading || configLoading) ? <LoadingSpinner size="sm" className="mr-2" /> : null}
              刷新数据
            </Button>
            <Button onClick={handleCreateAgent} className="flex items-center">
              <Plus className="w-4 h-4 mr-2" />
              添加代理
            </Button>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          <StatsCard
            title="总代理数"
            value={allAgents.length}
            loading={loading || configLoading}
            description="系统中的代理总数"
            color="primary"
          />
          <StatsCard
            title="活跃代理"
            value={activeAgents.length}
            loading={loading || configLoading}
            description="当前活跃的代理"
            color="success"
          />
          <StatsCard
            title="总文章数"
            value={totalArticles}
            loading={loading || configLoading}
            description="所有代理提交的文章"
            color="primary"
          />
          <StatsCard
            title="平均成功率"
            value={`${averageSuccessRate.toFixed(1)}%`}
            loading={loading || configLoading}
            description="所有代理的平均发布成功率"
            color={averageSuccessRate >= 80 ? 'success' : 'warning'}
          />
        </div>

        {/* Filter Controls */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeInactive}
                  onChange={(e) => setIncludeInactive(e.target.checked)}
                  className="mr-2"
                />
                包含不活跃代理
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Agents List */}
        <Card>
          <CardHeader>
            <CardTitle>代理列表</CardTitle>
          </CardHeader>
          <CardContent>
            {(loading || configLoading) ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" />
                <span className="ml-2 text-gray-600">加载中...</span>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <div className="text-red-600 mb-4">加载失败: {error}</div>
                <Button onClick={() => refresh()}>重试</Button>
              </div>
            ) : allAgents.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="mb-4">暂无代理数据</div>
                <Button onClick={handleCreateAgent} className="flex items-center mx-auto">
                  <Plus className="w-4 h-4 mr-2" />
                  添加第一个代理
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        代理信息
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        API密钥
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        文章统计
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        成功率
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        最近提交
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {allAgents.map((agent) => (
                      <tr key={agent.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {agent.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {agent.id}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-mono text-gray-700">
                            {agent.api_key_display || '未设置'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={agent.status} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            总计: {agent.total_articles_submitted || 0}
                          </div>
                          <div className="text-sm text-gray-500">
                            已发布: {agent.total_articles_published || 0}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {(Number(agent.success_rate) || 0).toFixed(1)}%
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {agent.updated_at
                            ? new Date(agent.updated_at).toLocaleDateString('zh-CN')
                            : '-'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setSelectedAgent(agent)}
                            >
                              详情
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEditAgent(agent)}
                              className="flex items-center"
                            >
                              <Edit className="w-3 h-3 mr-1" />
                              编辑
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteAgent(agent)}
                              className="flex items-center text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              删除
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Agent Detail Modal */}
        {selectedAgent && (
          <AgentDetailModal
            agent={selectedAgent}
            isOpen={true}
            onClose={() => setSelectedAgent(null)}
          />
        )}

        {/* Agent Form Modal */}
        <AgentFormModal
          isOpen={showAgentForm}
          onClose={() => setShowAgentForm(false)}
          agent={editingAgent || undefined}
          onSave={handleSaveAgent}
          isLoading={isOperating}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          onClose={() => setShowDeleteConfirm(false)}
          onConfirm={handleConfirmDelete}
          title="删除代理"
          message={`确定要删除代理 "${agentToDelete?.name}" 吗？此操作无法撤销。`}
          confirmText="删除"
          type="danger"
          isLoading={isOperating}
        />

        {/* Toast Notifications */}
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </DashboardLayout>
  );
};

export default AgentsPage;