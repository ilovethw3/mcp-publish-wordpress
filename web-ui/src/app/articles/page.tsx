'use client';

import React, { useState, useCallback } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useArticles, useArticle } from '@/hooks/useMCPData';
import { Article } from '@/types';

interface ArticleActionsProps {
  article: Article;
  onAction: (action: 'approve' | 'reject', id: number, data?: any) => Promise<void>;
  isLoading: boolean;
}

const ArticleActions: React.FC<ArticleActionsProps> = ({ article, onAction, isLoading }) => {
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  if (article.status !== 'pending_review') {
    return null;
  }

  const handleApprove = () => {
    onAction('approve', article.id);
  };

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      alert('请输入拒绝原因');
      return;
    }
    onAction('reject', article.id, rejectionReason);
    setShowRejectDialog(false);
    setRejectionReason('');
  };

  return (
    <div className="flex space-x-2">
      <Button
        size="sm"
        variant="primary"
        onClick={handleApprove}
        disabled={isLoading}
      >
        批准
      </Button>
      <Button
        size="sm"
        variant="danger"
        onClick={() => setShowRejectDialog(true)}
        disabled={isLoading}
      >
        拒绝
      </Button>

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
};

const ArticlesPage = () => {
  const [selectedStatus, setSelectedStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

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
    action: 'approve' | 'reject',
    articleId: number,
    data?: any
  ) => {
    setActionLoading(articleId);
    try {
      // This would be implemented with proper API calls
      // For now, just simulate the action
      console.log(`${action} article ${articleId}`, data);
      
      // Refresh the articles list after action
      await refresh();
    } catch (error) {
      console.error(`Failed to ${action} article:`, error);
      alert(`操作失败: ${error}`);
    } finally {
      setActionLoading(null);
    }
  }, [refresh]);

  const statusOptions = [
    { value: '', label: '全部状态' },
    { value: 'pending_review', label: '待审核' },
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
                          {article.title}
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
                        
                        <ArticleActions
                          article={article}
                          onAction={handleArticleAction}
                          isLoading={actionLoading === article.id}
                        />
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
      </div>
    </DashboardLayout>
  );
};

export default ArticlesPage;