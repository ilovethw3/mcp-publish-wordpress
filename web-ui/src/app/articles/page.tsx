'use client';

import React, { useState, useCallback, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ArticleDetailModal from '@/components/ui/ArticleDetailModal';
import ArticleEditModal from '@/components/ui/ArticleEditModal';
import { useArticles, useArticle } from '@/hooks/useMCPData';
import { apiClient } from '@/lib/api';
import { Article } from '@/types';
import { useToastContext } from '@/contexts/ToastContext';

interface Site {
  id: string;
  name: string;
  status: string;
}

interface ArticleActionsProps {
  article: Article;
  onAction: (action: 'approve_only' | 'reject' | 'publish' | 'edit', id: number, data?: any) => Promise<void>;
  isLoading: boolean;
  showError: (message: string) => void;
  showWarning: (message: string) => void;
}

const ArticleActions: React.FC<ArticleActionsProps> = ({ article, onAction, isLoading, showError, showWarning }) => {
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [publishNotes, setPublishNotes] = useState('');
  const [approveNotes, setApproveNotes] = useState('');
  const [selectedSiteForPublish, setSelectedSiteForPublish] = useState('');
  const [sites, setSites] = useState<Site[]>([]);
  const [sitesLoading, setSitesLoading] = useState(false);

  // Fetch sites when publish dialog opens
  const fetchSites = async () => {
    if (sites.length > 0) return; // Already fetched
    
    setSitesLoading(true);
    try {
      const response = await fetch('/api/config/sites');
      const result = await response.json();
      
      if (result.success && result.data.sites) {
        const activeSites = result.data.sites.filter((site: Site) => site.status === 'active');
        setSites(activeSites);
      } else {
        console.error('Failed to fetch sites:', result.error);
        showError('获取站点列表失败，请稍后重试');
      }
    } catch (error) {
      console.error('Error fetching sites:', error);
      showError('网络错误，请检查连接');
    } finally {
      setSitesLoading(false);
    }
  };

  const handleApproveOnly = () => {
    onAction('approve_only', article.id, { 
      reviewer_notes: approveNotes 
    });
    setShowApproveDialog(false);
    setApproveNotes('');
  };

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      showWarning('请输入拒绝原因');
      return;
    }
    onAction('reject', article.id, rejectionReason);
    setShowRejectDialog(false);
    setRejectionReason('');
  };

  const handlePublish = () => {
    if (!selectedSiteForPublish) {
      showWarning('请选择发布站点');
      return;
    }
    onAction('publish', article.id, {
      target_site_id: selectedSiteForPublish,
      notes: publishNotes
    });
    setShowPublishDialog(false);
    setSelectedSiteForPublish('');
    setPublishNotes('');
  };

  // Render actions based on status
  if (article.status === 'pending_review') {
    return (
      <div className="flex space-x-2">
        <Button
          size="sm"
          variant="primary"
          onClick={() => setShowApproveDialog(true)}
          disabled={isLoading}
        >
          通过
        </Button>
        <Button
          size="sm"
          variant="danger"
          onClick={() => setShowRejectDialog(true)}
          disabled={isLoading}
        >
          拒绝
        </Button>

        {/* Approve Only Dialog (No Site Selection) */}
        {showApproveDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">审批文章</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  审批备注
                </label>
                <textarea
                  className="w-full border border-gray-300 rounded-md p-2"
                  rows={3}
                  value={approveNotes}
                  onChange={(e) => setApproveNotes(e.target.value)}
                  placeholder="审批备注..."
                />
              </div>

              <div className="flex space-x-3 justify-end">
                <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
                  取消
                </Button>
                <Button variant="primary" onClick={handleApproveOnly}>
                  通过审批
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Simple reject dialog */}
        {showRejectDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">拒绝文章</h3>
              <p className="text-gray-600 mb-4">请输入拒绝原因：</p>
              <textarea
                className="w-full border border-gray-300 rounded-md p-3 mb-4"
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="请输入拒绝原因..."
              />
              <div className="flex space-x-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowRejectDialog(false)}
                >
                  取消
                </Button>
                <Button
                  variant="danger"
                  onClick={handleReject}
                  disabled={!rejectionReason.trim()}
                >
                  确认拒绝
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (article.status === 'approved') {
    return (
      <div className="flex space-x-2">
        <Button
          size="sm"
          variant="primary"
          onClick={() => {
            setShowPublishDialog(true);
            fetchSites();
          }}
          disabled={isLoading}
        >
          发布
        </Button>

        {/* Publish Dialog with Site Selection */}
        {showPublishDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">发布文章</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择发布站点 <span className="text-red-500">*</span>
                </label>
                {sitesLoading ? (
                  <div className="flex items-center justify-center py-2">
                    <LoadingSpinner size="sm" />
                    <span className="ml-2 text-sm text-gray-600">加载站点列表...</span>
                  </div>
                ) : (
                  <select
                    className="w-full border border-gray-300 rounded-md p-2"
                    value={selectedSiteForPublish}
                    onChange={(e) => setSelectedSiteForPublish(e.target.value)}
                  >
                    <option value="">请选择站点</option>
                    {sites.map((site) => (
                      <option key={site.id} value={site.id}>
                        {site.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  发布备注 (可选)
                </label>
                <textarea
                  className="w-full border border-gray-300 rounded-md p-2"
                  rows={3}
                  value={publishNotes}
                  onChange={(e) => setPublishNotes(e.target.value)}
                  placeholder="发布备注..."
                />
              </div>
              
              <div className="flex space-x-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowPublishDialog(false);
                    setSelectedSiteForPublish('');
                    setPublishNotes('');
                  }}
                >
                  取消
                </Button>
                <Button
                  variant="primary"
                  onClick={handlePublish}
                  disabled={!selectedSiteForPublish || isLoading}
                >
                  确认发布
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (article.status === 'publish_failed') {
    return (
      <div className="flex space-x-2">
        <Button
          size="sm"
          variant="primary"
          onClick={() => {
            setShowPublishDialog(true);
            fetchSites();
          }}
          disabled={isLoading}
        >
          重试发布
        </Button>

        {/* Retry publish dialog with site selection */}
        {showPublishDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">重新发布文章</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择发布站点 <span className="text-red-500">*</span>
                </label>
                {sitesLoading ? (
                  <div className="flex items-center justify-center py-2">
                    <LoadingSpinner size="sm" />
                    <span className="ml-2 text-sm text-gray-600">加载站点列表...</span>
                  </div>
                ) : (
                  <select
                    className="w-full border border-gray-300 rounded-md p-2"
                    value={selectedSiteForPublish}
                    onChange={(e) => setSelectedSiteForPublish(e.target.value)}
                  >
                    <option value="">请选择站点</option>
                    {sites.map((site) => (
                      <option key={site.id} value={site.id}>
                        {site.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  重试备注 (可选)
                </label>
                <textarea
                  className="w-full border border-gray-300 rounded-md p-2"
                  rows={3}
                  value={publishNotes}
                  onChange={(e) => setPublishNotes(e.target.value)}
                  placeholder="重试备注..."
                />
              </div>
              
              <div className="flex space-x-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowPublishDialog(false);
                    setSelectedSiteForPublish('');
                    setPublishNotes('');
                  }}
                >
                  取消
                </Button>
                <Button
                  variant="primary"
                  onClick={handlePublish}
                  disabled={!selectedSiteForPublish || isLoading}
                >
                  确认重新发布
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
};

const ArticlesPage = () => {
  const [selectedStatus, setSelectedStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedArticleId, setSelectedArticleId] = useState<number | undefined>();
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingArticle, setEditingArticle] = useState<Article | null>(null);
  
  // Toast functionality
  const { showSuccess, showError, showWarning } = useToastContext();

  const { 
    articles, 
    total, 
    loading, 
    error, 
    refresh 
  } = useArticles({
    status: selectedStatus || undefined,
    search: searchTerm || undefined,
    agent_id: selectedAgent || undefined,
    limit: 50,
  });

  const handleArticleAction = useCallback(async (
    action: 'approve_only' | 'reject' | 'publish' | 'edit',
    articleId: number,
    data?: any
  ) => {
    setActionLoading(articleId);
    try {
      let result;
      
      // 使用新的分离工作流MCP工具
      if (action === 'approve_only') {
        console.log(`[ARTICLES-PAGE] 🔐 使用MCP工具审批文章 ${articleId}`);
        const response = await fetch('/api/mcp-proxy/approve-article', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            article_id: articleId,
            reviewer_notes: data?.reviewer_notes || ''
          }),
        });
        result = await response.json();
      } else if (action === 'reject') {
        console.log(`[ARTICLES-PAGE] 🔐 使用MCP工具拒绝文章 ${articleId}`);
        result = await apiClient.mcpRejectArticle(articleId, data);
      } else if (action === 'publish') {
        console.log(`[ARTICLES-PAGE] 🔐 使用MCP工具发布文章 ${articleId}，发布到站点: ${data?.target_site_id}`);
        const response = await fetch('/api/mcp-proxy/publish-article', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            article_id: articleId,
            target_site_id: data?.target_site_id,
            notes: data?.notes || ''
          }),
        });
        result = await response.json();
      }
      
      if (result && result.success) {
        // 显示更详细的成功信息
        const actionText = action === 'approve_only' ? '审批通过' : 
                          action === 'reject' ? '拒绝' : 
                          action === 'publish' ? '发布' : '操作';
        let message = `文章${actionText}成功！`;
        
        // 如果是发布成功，显示WordPress发布信息
        let toastAction;
        if (action === 'publish' && result.data) {
          const wpData = result.data;
          if (wpData.wordpress_post_id) {
            message += `\n📝 WordPress文章ID: ${wpData.wordpress_post_id}`;
          }
          if (wpData.wordpress_permalink) {
            message += `\n🔗 文章已成功发布到WordPress`;
            toastAction = {
              label: '查看文章',
              onClick: () => window.open(wpData.wordpress_permalink, '_blank')
            };
          }
        }
        
        // For successful publish actions, show longer duration
        const duration = action === 'publish' ? 8000 : 5000;
        showSuccess(message, { 
          duration,
          action: toastAction
        });
        
        // Refresh the articles list after action
        await refresh();
      } else {
        throw new Error(result?.error || '操作失败');
      }
    } catch (error) {
      console.error(`[ARTICLES-PAGE] ❌ ${action} article failed:`, error);
      
      // 显示更详细的错误信息
      let errorMessage = `操作失败: ${error instanceof Error ? error.message : error}`;
      if (error instanceof Error && error.message.includes('MCP')) {
        errorMessage += '\n请检查MCP服务器连接和API密钥配置';
      }
      
      showError(errorMessage);
    } finally {
      setActionLoading(null);
    }
  }, [refresh, showSuccess, showError]);

  // Handle opening article detail modal
  const handleViewArticleDetail = useCallback((articleId: number) => {
    setSelectedArticleId(articleId);
    setDetailModalOpen(true);
  }, []);

  // Handle closing article detail modal
  const handleCloseDetailModal = useCallback(() => {
    setDetailModalOpen(false);
    setSelectedArticleId(undefined);
  }, []);

  // Handle opening article edit modal
  const handleEditArticle = useCallback((article: Article) => {
    setEditingArticle(article);
    setEditModalOpen(true);
  }, []);

  // Handle closing article edit modal
  const handleCloseEditModal = useCallback(() => {
    setEditModalOpen(false);
    setEditingArticle(null);
  }, []);

  // Handle article save in edit modal
  const handleArticleSave = useCallback((updatedArticle: Article) => {
    setEditModalOpen(false);
    setEditingArticle(null);
    refresh(); // Refresh the article list
  }, [refresh]);

  const statusOptions = [
    { value: '', label: '全部状态' },
    { value: 'pending_review', label: '待审核' },
    { value: 'approved', label: '已通过' },
    { value: 'publishing', label: '发布中' },
    { value: 'published', label: '已发布' },
    { value: 'rejected', label: '已拒绝' },
    { value: 'publish_failed', label: '发布失败' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">文章管理</h2>
            <p className="mt-1 text-sm text-gray-600">
              管理所有AI代理提交的文章内容
            </p>
          </div>
          <div className="text-sm text-gray-500">
            共 {total} 篇文章
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  状态筛选
                </label>
                <select
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                >
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  搜索文章
                </label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="搜索标题或内容..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  代理筛选
                </label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="输入代理ID..."
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Articles List */}
        <Card>
          <CardHeader>
            <CardTitle>文章列表</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" />
                <span className="ml-2 text-gray-600">加载中...</span>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <div className="text-red-600 mb-4">加载失败: {error}</div>
                <Button onClick={() => refresh()}>重试</Button>
              </div>
            ) : articles.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                没有找到符合条件的文章
              </div>
            ) : (
              <div className="space-y-4">
                {articles.map((article) => (
                  <div 
                    key={article.id}
                    className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          <button
                            onClick={() => handleViewArticleDetail(article.id)}
                            className="text-left hover:text-blue-600 transition-colors cursor-pointer focus:outline-none focus:text-blue-600"
                            title="点击查看详情"
                          >
                            {article.title}
                          </button>
                        </h3>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                          <span>ID: {article.id}</span>
                          {article.submitting_agent && (
                            <span>代理: {article.submitting_agent.name}</span>
                          )}
                          {article.target_site && (
                            <span>目标站点: {article.target_site.name}</span>
                          )}
                          {article.tags && (
                            <span>标签: {article.tags}</span>
                          )}
                          {article.category && (
                            <span>分类: {article.category}</span>
                          )}
                        </div>
                      </div>
                      <StatusBadge status={article.status} />
                    </div>

                    {article.content_preview && (
                      <div className="mb-4">
                        <p className="text-gray-700 text-sm">
                          {article.content_preview}
                        </p>
                      </div>
                    )}

                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-500">
                        <div>创建: {new Date(article.created_at).toLocaleString('zh-CN')}</div>
                        <div>更新: {new Date(article.updated_at).toLocaleString('zh-CN')}</div>
                      </div>

                      <div className="flex items-center space-x-4">
                        {article.wordpress_post_id && (
                          <div className="text-sm text-green-600">
                            WordPress ID: {article.wordpress_post_id}
                          </div>
                        )}
                        
                        <div className="flex items-center space-x-2">
                          {article.status === 'pending_review' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleEditArticle(article)}
                              className="text-blue-600 border-blue-300 hover:bg-blue-50"
                            >
                              编辑
                            </Button>
                          )}
                          
                          <ArticleActions
                            article={article}
                            onAction={handleArticleAction}
                            isLoading={actionLoading === article.id}
                            showError={showError}
                            showWarning={showWarning}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Error messages */}
                    {article.publish_error_message && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                        <div className="text-sm font-medium text-red-800">发布错误:</div>
                        <div className="text-sm text-red-700">{article.publish_error_message}</div>
                      </div>
                    )}

                    {article.rejection_reason && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                        <div className="text-sm font-medium text-red-800">拒绝原因:</div>
                        <div className="text-sm text-red-700">{article.rejection_reason}</div>
                      </div>
                    )}

                    {article.reviewer_notes && (
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                        <div className="text-sm font-medium text-blue-800">审核备注:</div>
                        <div className="text-sm text-blue-700">{article.reviewer_notes}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Article Detail Modal */}
        <ArticleDetailModal
          isOpen={detailModalOpen}
          onClose={handleCloseDetailModal}
          articleId={selectedArticleId}
          onArticleUpdate={refresh}
        />

        {/* Article Edit Modal */}
        <ArticleEditModal
          isOpen={editModalOpen}
          onClose={handleCloseEditModal}
          article={editingArticle}
          onSave={handleArticleSave}
        />
      </div>
    </DashboardLayout>
  );
};

export default ArticlesPage;