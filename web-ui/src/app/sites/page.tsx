'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatsCard from '@/components/ui/StatsCard';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useSites, useSiteHealth, useSiteArticles } from '@/hooks/useMCPData';
import { useSiteConfig, useToast } from '@/hooks/useConfigManagement';
import SiteFormModal from '@/components/config/SiteFormModal';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { ToastContainer } from '@/components/ui/Toast';
import { Site } from '@/types';
import { Plus, Edit, Trash2, TestTube } from 'lucide-react';

interface SiteDetailModalProps {
  site: Site;
  isOpen: boolean;
  onClose: () => void;
}

const SiteDetailModal: React.FC<SiteDetailModalProps> = ({ site, isOpen, onClose }) => {
  const { health, loading: healthLoading } = useSiteHealth(site.id);
  const { articles, loading: articlesLoading } = useSiteArticles(site.id);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto mx-4">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{site.name}</h2>
              <p className="text-gray-600">站点ID: {site.id}</p>
              <div className="mt-2">
                <StatusBadge status={site.health_status} />
              </div>
            </div>
            <Button variant="outline" onClick={onClose}>
              关闭
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Site Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard
              title="总文章数"
              value={site.statistics?.total_articles || 0}
              color="primary"
              loading={false}
            />
            <StatsCard
              title="发布成功"
              value={site.statistics?.published_articles || 0}
              color="success"
              loading={false}
            />
            <StatsCard
              title="发布失败"
              value={site.statistics?.failed_articles || 0}
              color="error"
              loading={false}
            />
          </div>

          {/* Health Details */}
          {healthLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : health ? (
            <Card>
              <CardHeader>
                <CardTitle>健康状态详情</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">健康状态</div>
                    <div className="font-semibold">
                      <StatusBadge status={health.health_status} size="sm" />
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">成功率</div>
                    <div className="font-semibold">{health.metrics?.success_rate || 0}%</div>
                  </div>
                  <div>
                    <div className="text-gray-600">最近成功发布</div>
                    <div className="font-semibold">
                      {health.metrics?.last_successful_publish
                        ? new Date(health.metrics.last_successful_publish).toLocaleDateString('zh-CN')
                        : '-'
                      }
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">最近失败发布</div>
                    <div className="font-semibold">
                      {health.metrics?.last_failed_publish
                        ? new Date(health.metrics.last_failed_publish).toLocaleDateString('zh-CN')
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
                          {article.submitting_agent?.name || 'Unknown Agent'} • 
                          {new Date(article.updated_at).toLocaleDateString('zh-CN')}
                        </div>
                      </div>
                      <StatusBadge status={article.status} size="sm" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  该站点暂无文章记录
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const SitesPage = () => {
  // Original state
  const [includeInactive, setIncludeInactive] = useState(false);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  
  // New configuration management state
  const [showSiteForm, setShowSiteForm] = useState(false);
  const [editingSite, setEditingSite] = useState<any | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [siteToDelete, setSiteToDelete] = useState<Site | null>(null);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [siteToTest, setSiteToTest] = useState<Site | null>(null);

  // Hooks
  const { 
    sites, 
    total, 
    loading, 
    error, 
    refresh 
  } = useSites(includeInactive);

  const {
    sites: configSites,
    loading: configLoading,
    isOperating,
    createSite,
    updateSite,
    deleteSite,
    testSiteConnection,
    refresh: refreshConfig,
  } = useSiteConfig();

  const { toasts, showToast, removeToast } = useToast();

  // Merge data from both sources (MCP runtime data + configuration data)
  const mergedSites = sites.map(site => {
    const configSite = configSites.find((cs: any) => cs.id === site.id);
    return configSite ? { ...site, ...configSite } : site;
  });

  // Add config-only sites (that may not have runtime data yet)
  const configOnlySites = configSites.filter(
    (cs: any) => !sites.find(s => s.id === cs.id)
  ).map((cs: any) => ({
    ...cs,
    health_status: 'unknown' as const,
    statistics: {
      total_articles: 0,
      published_articles: 0,
      failed_articles: 0,
      success_rate: 0,
      last_publish: null,
    }
  }));

  const allSites = [...mergedSites, ...configOnlySites];

  const healthySites = allSites.filter(site => site.health_status === 'healthy');
  const warningSites = allSites.filter(site => site.health_status === 'warning');
  const errorSites = allSites.filter(site => site.health_status === 'error');
  const totalArticles = allSites.reduce((sum, site) => sum + (site.statistics?.total_articles || 0), 0);
  const totalPublished = allSites.reduce((sum, site) => sum + (site.statistics?.published_articles || 0), 0);
  const averageSuccessRate = allSites.length > 0 
    ? allSites.reduce((sum, site) => sum + (site.statistics?.success_rate || 0), 0) / allSites.length 
    : 0;

  // Handlers
  const handleCreateSite = () => {
    setEditingSite(null);
    setShowSiteForm(true);
  };

  const handleEditSite = (site: Site) => {
    setEditingSite(site);
    setShowSiteForm(true);
  };

  const handleDeleteSite = (site: Site) => {
    setSiteToDelete(site);
    setShowDeleteConfirm(true);
  };

  const handleTestConnection = (site: Site) => {
    setSiteToTest(site);
    setShowTestDialog(true);
  };

  const handleSaveSite = async (siteData: any) => {
    try {
      if (editingSite) {
        await updateSite(editingSite.id, siteData, true); // Test connection on update
        showToast('success', '站点更新成功');
      } else {
        await createSite(siteData, true); // Test connection on create
        showToast('success', '站点创建成功');
      }
      refresh(); // Refresh MCP data
      refreshConfig(); // Refresh config data
    } catch (error) {
      showToast('error', `操作失败: ${error instanceof Error ? error.message : '未知错误'}`);
      throw error;
    }
  };

  const handleConfirmDelete = async () => {
    if (!siteToDelete) return;

    try {
      await deleteSite(siteToDelete.id);
      showToast('success', '站点删除成功');
      refresh();
      refreshConfig();
      setShowDeleteConfirm(false);
      setSiteToDelete(null);
    } catch (error) {
      showToast('error', `删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const handleConfirmTest = async () => {
    if (!siteToTest) return;

    try {
      const result = await testSiteConnection(siteToTest.id);
      if (result.success) {
        showToast('success', '连接测试成功');
      } else {
        showToast('warning', `连接测试警告: ${result.message || '未知问题'}`);
      }
      setShowTestDialog(false);
      setSiteToTest(null);
    } catch (error) {
      showToast('error', `连接测试失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'primary';
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">站点管理</h2>
            <p className="mt-1 text-sm text-gray-600">
              管理所有WordPress站点的状态和健康度
            </p>
          </div>
          <div className="flex space-x-3">
            <Button variant="outline" onClick={() => refresh()} disabled={loading || configLoading}>
              {(loading || configLoading) ? <LoadingSpinner size="sm" className="mr-2" /> : null}
              刷新数据
            </Button>
            <Button onClick={handleCreateSite} className="flex items-center">
              <Plus className="w-4 h-4 mr-2" />
              添加站点
            </Button>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          <StatsCard
            title="总站点数"
            value={allSites.length}
            loading={loading || configLoading}
            description="系统中的站点总数"
            color="primary"
          />
          <StatsCard
            title="健康站点"
            value={healthySites.length}
            loading={loading || configLoading}
            description="运行状态良好的站点"
            color="success"
          />
          <StatsCard
            title="总发布数"
            value={totalPublished}
            loading={loading || configLoading}
            description="所有站点发布的文章"
            color="primary"
          />
          <StatsCard
            title="平均成功率"
            value={`${averageSuccessRate.toFixed(1)}%`}
            loading={loading || configLoading}
            description="所有站点的平均发布成功率"
            color={averageSuccessRate >= 90 ? 'success' : 'warning'}
          />
        </div>

        {/* Health Summary */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <StatsCard
            title="健康站点"
            value={healthySites.length}
            loading={loading || configLoading}
            color="success"
            description="运行正常"
          />
          <StatsCard
            title="警告站点"
            value={warningSites.length}
            loading={loading || configLoading}
            color="warning"
            description="需要关注"
          />
          <StatsCard
            title="错误站点"
            value={errorSites.length}
            loading={loading || configLoading}
            color="error"
            description="需要修复"
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
                包含不活跃站点
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Sites List */}
        <Card>
          <CardHeader>
            <CardTitle>站点列表</CardTitle>
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
            ) : allSites.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="mb-4">暂无站点数据</div>
                <Button onClick={handleCreateSite} className="flex items-center mx-auto">
                  <Plus className="w-4 h-4 mr-2" />
                  添加第一个站点
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        站点信息
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        健康状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        文章统计
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        成功率
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        最近发布
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {allSites.map((site) => (
                      <tr key={site.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {site.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {site.id}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={site.health_status} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            总计: {site.statistics?.total_articles || 0}
                          </div>
                          <div className="text-sm text-gray-500">
                            成功: {site.statistics?.published_articles || 0} / 
                            失败: {site.statistics?.failed_articles || 0}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {(site.statistics?.success_rate || 0).toFixed(1)}%
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {site.statistics?.last_publish
                            ? new Date(site.statistics.last_publish).toLocaleDateString('zh-CN')
                            : '-'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setSelectedSite(site)}
                            >
                              详情
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEditSite(site)}
                              className="flex items-center"
                            >
                              <Edit className="w-3 h-3 mr-1" />
                              编辑
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleTestConnection(site)}
                              className="flex items-center text-blue-600 hover:text-blue-700"
                            >
                              <TestTube className="w-3 h-3 mr-1" />
                              测试
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteSite(site)}
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

        {/* Site Detail Modal */}
        {selectedSite && (
          <SiteDetailModal
            site={selectedSite}
            isOpen={true}
            onClose={() => setSelectedSite(null)}
          />
        )}

        {/* Site Form Modal */}
        <SiteFormModal
          isOpen={showSiteForm}
          onClose={() => setShowSiteForm(false)}
          site={editingSite || undefined}
          onSave={handleSaveSite}
          isLoading={isOperating}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          onClose={() => setShowDeleteConfirm(false)}
          onConfirm={handleConfirmDelete}
          title="删除站点"
          message={`确定要删除站点 "${siteToDelete?.name}" 吗？此操作无法撤销。`}
          confirmText="删除"
          type="danger"
          isLoading={isOperating}
        />

        {/* Test Connection Dialog */}
        <ConfirmDialog
          isOpen={showTestDialog}
          onClose={() => setShowTestDialog(false)}
          onConfirm={handleConfirmTest}
          title="测试连接"
          message={`确定要测试站点 "${siteToTest?.name}" 的WordPress连接吗？`}
          confirmText="测试连接"
          type="info"
          isLoading={isOperating}
        />

        {/* Toast Notifications */}
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </DashboardLayout>
  );
};

export default SitesPage;