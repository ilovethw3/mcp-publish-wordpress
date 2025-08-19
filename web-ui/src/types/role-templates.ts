/**
 * TypeScript interfaces for role template management
 */

export interface RoleTemplate {
  id: string;
  name: string;
  description: string;
  permissions: {
    can_submit_articles: boolean;
    can_edit_own_articles: boolean;
    can_edit_others_articles: boolean;
    can_approve_articles: boolean;
    can_publish_articles: boolean;
    can_view_statistics: boolean;
    can_review_agents: string[];
    allowed_categories: string[];
    allowed_tags: string[];
  };
  quota_limits: {
    daily_articles?: number;
    monthly_articles?: number;
    working_hours?: {
      enabled: boolean;
      start?: string;
      end?: string;
      timezone?: string;
      working_days?: number[];
    };
  };
  is_system_role: boolean;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface RoleTemplateHistory {
  id: number;
  role_template_id: string;
  action: string;
  old_config?: any;
  new_config?: any;
  changed_by?: string;
  created_at: string;
}

export interface RoleTemplateFormData {
  role_id?: string;
  name: string;
  description: string;
  permissions: {
    can_submit_articles: boolean;
    can_edit_own_articles: boolean;
    can_edit_others_articles: boolean;
    can_approve_articles: boolean;
    can_publish_articles: boolean;
    can_view_statistics: boolean;
    can_review_agents: string[];
    allowed_categories: string[];
    allowed_tags: string[];
  };
  quota_limits: {
    daily_articles?: number;
    monthly_articles?: number;
    working_hours?: {
      enabled: boolean;
      start?: string;
      end?: string;
      timezone?: string;
      working_days?: number[];
    };
  };
  created_by?: string;
  updated_by?: string;
}

export interface RoleApplyData {
  agent_ids: string[];
  permissions_override?: Record<string, any>;
}

export interface RoleApplyResult {
  agent_id: string;
  success: boolean;
  error?: string;
}

// Permission labels for UI display
export const PERMISSION_LABELS = {
  can_submit_articles: '提交文章',
  can_edit_own_articles: '编辑自己的文章',
  can_edit_others_articles: '编辑他人文章',
  can_approve_articles: '审批文章',
  can_publish_articles: '发布文章',
  can_view_statistics: '查看统计信息',
};

// Working days labels
export const WORKING_DAYS_LABELS = {
  1: '周一',
  2: '周二', 
  3: '周三',
  4: '周四',
  5: '周五',
  6: '周六',
  7: '周日',
};

// Common timezones
export const COMMON_TIMEZONES = [
  { value: 'Asia/Shanghai', label: '北京时间 (UTC+8)' },
  { value: 'UTC', label: '协调世界时 (UTC)' },
  { value: 'America/New_York', label: '纽约时间 (EST/EDT)' },
  { value: 'Europe/London', label: '伦敦时间 (GMT/BST)' },
  { value: 'Asia/Tokyo', label: '东京时间 (JST)' },
];