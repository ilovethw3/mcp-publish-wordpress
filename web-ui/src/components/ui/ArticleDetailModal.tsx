/**
 * Article Detail Modal Component
 * 
 * Displays complete article information including Markdown content,
 * metadata, and publishing status using direct database access.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Dialog } from '@headlessui/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import StatusBadge from '@/components/ui/StatusBadge';
import ArticleEditModal from '@/components/ui/ArticleEditModal';
import { X, ExternalLink, Calendar, User, Globe, Tag, FolderOpen, Edit3 } from 'lucide-react';
import { Article } from '@/types';

interface ArticleDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  articleId?: number;
  onArticleUpdate?: () => void; // Callback when article is updated
}

interface DetailedArticle extends Article {
  content_markdown: string;
  content_html?: string | null;
  agent_metadata?: any;
}

const ArticleDetailModal: React.FC<ArticleDetailModalProps> = ({
  isOpen,
  onClose,
  articleId,
  onArticleUpdate
}) => {
  const [article, setArticle] = useState<DetailedArticle | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);

  // Fetch article details when modal opens
  useEffect(() => {
    if (isOpen && articleId) {
      fetchArticleDetail();
    } else {
      // Reset state when modal closes
      setArticle(null);
      setError(null);
    }
  }, [isOpen, articleId]);

  const fetchArticleDetail = async () => {
    if (!articleId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/articles/${articleId}`);
      const result = await response.json();
      
      if (result.success) {
        setArticle(result.data);
      } else {
        setError(result.error || '获取文章详情失败');
      }
    } catch (err) {
      console.error('Failed to fetch article detail:', err);
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleClose = () => {
    onClose();
  };

  const handleEditSave = (updatedArticle: Article) => {
    setArticle(updatedArticle as DetailedArticle);
    setEditModalOpen(false);
    if (onArticleUpdate) {
      onArticleUpdate();
    }
  };

  const canEdit = article && article.status === 'pending_review';

  if (!isOpen) return null;

  return (
    <Dialog
      open={isOpen}
      onClose={handleClose}
      className="relative z-50"
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50" aria-hidden="true" />

      {/* Full-screen container */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-4xl max-h-[90vh] bg-white rounded-lg shadow-xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50 flex-shrink-0">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              文章详情
            </Dialog.Title>
            <div className="flex items-center space-x-2">
              {canEdit && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditModalOpen(true)}
                  className="flex items-center space-x-2"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>编辑</span>
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                className="p-2 hover:bg-gray-200"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" />
                <span className="ml-3 text-gray-600">加载中...</span>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="text-red-600 text-center mb-4">{error}</div>
                <Button onClick={fetchArticleDetail} variant="outline">
                  重新加载
                </Button>
              </div>
            ) : article ? (
              <div className="p-6">
                {/* Article Header */}
                <div className="mb-6">
                  <div className="flex items-start justify-between mb-4">
                    <h1 className="text-2xl font-bold text-gray-900 pr-4">
                      {article.title}
                    </h1>
                    <StatusBadge status={article.status} />
                  </div>

                  {/* Metadata Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4" />
                      <span>创建时间: {formatDateTime(article.created_at)}</span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4" />
                      <span>更新时间: {formatDateTime(article.updated_at)}</span>
                    </div>

                    {article.submitting_agent && (
                      <div className="flex items-center space-x-2">
                        <User className="w-4 h-4" />
                        <span>提交代理: {article.submitting_agent.name}</span>
                      </div>
                    )}

                    {article.target_site && (
                      <div className="flex items-center space-x-2">
                        <Globe className="w-4 h-4" />
                        <span>目标站点: {article.target_site.name}</span>
                      </div>
                    )}

                    {article.tags && (
                      <div className="flex items-center space-x-2">
                        <Tag className="w-4 h-4" />
                        <span>标签: {article.tags}</span>
                      </div>
                    )}

                    {article.category && (
                      <div className="flex items-center space-x-2">
                        <FolderOpen className="w-4 h-4" />
                        <span>分类: {article.category}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* WordPress Publishing Info */}
                {article.wordpress_post_id && (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-green-800">已发布到 WordPress</h3>
                        <p className="text-sm text-green-600">文章ID: {article.wordpress_post_id}</p>
                      </div>
                      {article.wordpress_permalink && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(article.wordpress_permalink!, '_blank')}
                          className="flex items-center space-x-2"
                        >
                          <ExternalLink className="w-4 h-4" />
                          <span>查看文章</span>
                        </Button>
                      )}
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {article.publish_error_message && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h3 className="font-medium text-red-800 mb-2">发布错误</h3>
                    <p className="text-sm text-red-700">{article.publish_error_message}</p>
                  </div>
                )}

                {/* Rejection Reason */}
                {article.rejection_reason && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h3 className="font-medium text-red-800 mb-2">拒绝原因</h3>
                    <p className="text-sm text-red-700">{article.rejection_reason}</p>
                  </div>
                )}

                {/* Reviewer Notes */}
                {article.reviewer_notes && (
                  <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h3 className="font-medium text-blue-800 mb-2">审核备注</h3>
                    <p className="text-sm text-blue-700">{article.reviewer_notes}</p>
                  </div>
                )}

                {/* Article Content */}
                <div className="border-t border-gray-200 pt-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">文章内容</h2>
                  <div className="prose prose-lg max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      className="markdown-content"
                    >
                      {article.content_markdown}
                    </ReactMarkdown>
                  </div>
                </div>

                {/* Agent Metadata */}
                {article.agent_metadata && (
                  <div className="mt-8 pt-6 border-t border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">代理元数据</h3>
                    <pre className="bg-gray-100 rounded-md p-4 overflow-x-auto text-sm">
                      {JSON.stringify(article.agent_metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex-shrink-0">
            <div className="flex justify-end">
              <Button onClick={handleClose} variant="outline">
                关闭
              </Button>
            </div>
          </div>
        </Dialog.Panel>
      </div>

      {/* Article Edit Modal */}
      <ArticleEditModal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        article={article}
        onSave={handleEditSave}
      />
    </Dialog>
  );
};

export default ArticleDetailModal;