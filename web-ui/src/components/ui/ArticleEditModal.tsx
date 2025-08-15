/**
 * Article Edit Modal Component
 * 
 * Provides a full-screen modal for editing article content with Markdown editor,
 * live preview, and form validation.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { X, Eye, Edit3, Save } from 'lucide-react';
import { Article } from '@/types';
import { useToastContext } from '@/contexts/ToastContext';

interface ArticleEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  article: Article | null;
  onSave: (updatedArticle: Article) => void;
}

interface EditFormData {
  title: string;
  content_markdown: string;
  tags: string;
  category: string;
  reviewer_notes: string;
}

const ArticleEditModal: React.FC<ArticleEditModalProps> = ({
  isOpen,
  onClose,
  article,
  onSave
}) => {
  const [formData, setFormData] = useState<EditFormData>({
    title: '',
    content_markdown: '',
    tags: '',
    category: '',
    reviewer_notes: ''
  });
  const [showPreview, setShowPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  
  const { showSuccess, showError } = useToastContext();

  // Initialize form data when article changes
  useEffect(() => {
    if (article) {
      setFormData({
        title: article.title || '',
        content_markdown: article.content_markdown || '',
        tags: article.tags || '',
        category: article.category || '',
        reviewer_notes: article.reviewer_notes || ''
      });
      setHasChanges(false);
    }
  }, [article]);

  // Check if form has changes
  useEffect(() => {
    if (!article) return;
    
    const hasChanged = 
      formData.title !== (article.title || '') ||
      formData.content_markdown !== (article.content_markdown || '') ||
      formData.tags !== (article.tags || '') ||
      formData.category !== (article.category || '') ||
      formData.reviewer_notes !== (article.reviewer_notes || '');
    
    setHasChanges(hasChanged);
  }, [formData, article]);

  const handleInputChange = (field: keyof EditFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    if (!article) return;

    // Validate form
    if (!formData.title.trim()) {
      showError('标题不能为空');
      return;
    }

    if (!formData.content_markdown.trim()) {
      showError('内容不能为空');
      return;
    }

    if (formData.title.length > 200) {
      showError('标题不能超过200个字符');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`/api/articles/${article.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();
      
      if (result.success) {
        showSuccess('文章修改成功！');
        onSave(result.data);
        onClose();
      } else {
        throw new Error(result.error || '保存失败');
      }
    } catch (error) {
      console.error('Failed to save article:', error);
      showError(`保存失败: ${error instanceof Error ? error.message : '网络错误'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (hasChanges) {
      if (confirm('您有未保存的修改，确定要离开吗？')) {
        onClose();
      }
    } else {
      onClose();
    }
  };

  if (!isOpen || !article) return null;

  // Check if article can be edited
  const canEdit = article.status === 'pending_review';

  if (!canEdit) {
    return (
      <Dialog open={isOpen} onClose={onClose} className="relative z-50">
        <div className="fixed inset-0 bg-black bg-opacity-50" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">无法编辑文章</h3>
              <p className="text-gray-600 mb-6">
                只能编辑状态为"待审核"的文章。当前文章状态：{article.status}
              </p>
              <Button onClick={onClose} variant="outline">
                关闭
              </Button>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onClose={handleClose} className="relative z-50">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50" aria-hidden="true" />

      {/* Full-screen container */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full h-full max-w-6xl max-h-[95vh] bg-white rounded-lg shadow-xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50 flex-shrink-0">
            <div className="flex items-center space-x-4">
              <Dialog.Title className="text-lg font-semibold text-gray-900">
                编辑文章
              </Dialog.Title>
              {hasChanges && (
                <span className="text-sm text-orange-600 font-medium">未保存</span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center space-x-2"
              >
                {showPreview ? <Edit3 className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                <span>{showPreview ? '编辑' : '预览'}</span>
              </Button>
              
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                disabled={saving || !hasChanges}
                className="flex items-center space-x-2"
              >
                {saving ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>{saving ? '保存中...' : '保存'}</span>
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                className="p-2"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden flex">
            {/* Edit Form */}
            <div className={`${showPreview ? 'w-1/2' : 'w-full'} flex flex-col border-r border-gray-200`}>
              <div className="p-6 space-y-4 flex-1 overflow-y-auto">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    标题 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="请输入文章标题..."
                    maxLength={200}
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {formData.title.length}/200
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 flex flex-col">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    内容 <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    className="flex-1 min-h-[300px] border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm resize-none"
                    value={formData.content_markdown}
                    onChange={(e) => handleInputChange('content_markdown', e.target.value)}
                    placeholder="请输入Markdown格式的文章内容..."
                  />
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    标签
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.tags}
                    onChange={(e) => handleInputChange('tags', e.target.value)}
                    placeholder="请输入标签，用逗号分隔..."
                  />
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    分类
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    placeholder="请输入文章分类..."
                  />
                </div>

                {/* Reviewer Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    审核备注
                  </label>
                  <textarea
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    value={formData.reviewer_notes}
                    onChange={(e) => handleInputChange('reviewer_notes', e.target.value)}
                    placeholder="审核备注（可选）..."
                  />
                </div>
              </div>
            </div>

            {/* Preview */}
            {showPreview && (
              <div className="w-1/2 flex flex-col">
                <div className="p-6 bg-gray-50 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">预览</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="prose prose-lg max-w-none">
                    <h1 className="text-2xl font-bold text-gray-900 mb-4">
                      {formData.title || '标题预览'}
                    </h1>
                    
                    {formData.tags && (
                      <div className="mb-4">
                        <span className="text-sm text-gray-600">标签: {formData.tags}</span>
                      </div>
                    )}
                    
                    {formData.category && (
                      <div className="mb-4">
                        <span className="text-sm text-gray-600">分类: {formData.category}</span>
                      </div>
                    )}
                    
                    <div className="border-t border-gray-200 pt-4">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        className="markdown-content"
                      >
                        {formData.content_markdown || '*内容预览*'}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default ArticleEditModal;