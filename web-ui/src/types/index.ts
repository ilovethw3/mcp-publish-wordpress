// MCP WordPress Publisher v2.1 Web UI Types

// 基础Agent接口
interface BaseAgent {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'locked';
}

// MCP运行时Agent（来自MCP服务器的运行时数据）
interface MCPAgent extends BaseAgent {
  statistics: {
    total_articles: number;
    published_articles: number;
    success_rate: number;
    last_submission: string | null;
  };
}

// 配置Agent（配置管理中的完整数据）
interface ConfigAgent extends BaseAgent {
  description: string;
  api_key?: string;
  rate_limit: {
    requests_per_minute: number;
    requests_per_hour: number;
    requests_per_day: number;
  };
  permissions: {
    can_submit_articles: boolean;
    can_edit_own_articles: boolean;
    can_delete_own_articles: boolean;
    can_view_statistics: boolean;
    allowed_categories: string[];
    allowed_tags: string[];
  };
  notifications: {
    on_approval: boolean;
    on_rejection: boolean;
    on_publish_success: boolean;
    on_publish_failure: boolean;
  };
  // 数据库统计字段
  total_articles_submitted?: number;
  total_articles_published?: number;
  total_articles_rejected?: number;
  success_rate?: number;
  created_at?: string;
  updated_at?: string;
}

// 用于创建/编辑代理的表单接口
interface AgentFormData extends BaseAgent {
  description: string;
  api_key?: string; // 创建时生成，编辑时重新生成
  rate_limit: {
    requests_per_minute: number;
    requests_per_hour: number;
    requests_per_day: number;
  };
  permissions: {
    can_submit_articles: boolean;
    can_edit_own_articles: boolean;
    can_delete_own_articles: boolean;
    can_view_statistics: boolean;
    allowed_categories: string[];
    allowed_tags: string[];
  };
  notifications: {
    on_approval: boolean;
    on_rejection: boolean;
    on_publish_success: boolean;
    on_publish_failure: boolean;
  };
}

// 完整Agent（支持MCP数据 + 部分配置数据合并）
export type Agent = MCPAgent & Partial<ConfigAgent>;

// 完整配置Agent（用于表单和配置管理）
export type FullConfigAgent = BaseAgent & ConfigAgent;

// 导出代理表单数据类型
export type { AgentFormData };

// 基础Site接口
interface BaseSite {
  id: string;
  name: string;
  health_status: 'healthy' | 'warning' | 'error' | 'unknown';
}

// MCP运行时Site（来自MCP服务器的运行时数据）
interface MCPSite extends BaseSite {
  statistics: {
    total_articles: number;
    published_articles: number;
    failed_articles: number;
    success_rate: number;
    last_publish: string | null;
  };
}

// 配置Site（配置管理中的完整数据）
interface ConfigSite extends BaseSite {
  description: string;
  wordpress_config: {
    api_url: string;
    username: string;
    app_password: string;
    default_status: string;
    default_comment_status: string;
    default_ping_status: string;
    category_mapping: Record<string, number>;
    tag_auto_create: boolean;
  };
  publishing_rules: {
    allowed_agents: string[];
    allowed_categories: string[];
    min_word_count: number;
    max_word_count: number;
    require_featured_image: boolean;
    auto_approve: boolean;
    auto_publish_approved: boolean;
  };
  rate_limit: {
    max_posts_per_hour: number;
    max_posts_per_day: number;
    max_concurrent_publishes: number;
  };
  notifications: {
    on_publish_success: boolean;
    on_publish_failure: boolean;
    on_connection_error: boolean;
  };
  created_at?: string;
  status: 'active' | 'inactive';
}

// 完整Site（支持MCP数据 + 部分配置数据合并）
export type Site = MCPSite & Partial<ConfigSite>;

// 完整配置Site（用于表单和配置管理）
export type FullConfigSite = BaseSite & ConfigSite;

export interface Article {
  id: number;
  title: string;
  content_markdown?: string; // Article full content in Markdown format
  status: 'pending_review' | 'publishing' | 'published' | 'rejected' | 'publish_failed';
  tags?: string;
  category?: string;
  created_at: string;
  updated_at: string;
  submitting_agent?: {
    id: string;
    name: string;
  } | null;
  target_site?: {
    id: string;
    name: string;
  } | null;
  publishing_agent_id?: string;
  wordpress_post_id?: number;
  wordpress_permalink?: string;
  publish_error_message?: string;
  reviewer_notes?: string;
  rejection_reason?: string;
  content_preview?: string;
}

export interface SecurityStatus {
  active_sessions: number;
  session_details: SessionInfo[];
  audit_summary: AuditSummary;
  rate_limiting: {
    locked_agents: number;
    lockout_duration_minutes: number;
  };
}

export interface SessionInfo {
  agent_id: string;
  agent_name: string;
  created_at: string;
  last_activity: string;
  request_count: number;
  failed_attempts: number;
  is_locked: boolean;
  lockout_until?: string;
  session_duration_minutes: number;
  inactive_minutes: number;
}

export interface AuditSummary {
  period_hours: number;
  total_events: number;
  failed_events: number;
  success_rate: number;
  unique_agents: number;
  action_breakdown: Record<string, number>;
  last_updated: string;
}

export interface AuditEvent {
  timestamp: string;
  agent_id: string;
  action: string;
  resource: string;
  success: boolean;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, any>;
}

export interface RateLimitStatus {
  agent_id: string;
  minute_requests: number;
  minute_limit: number;
  hour_requests: number;
  hour_limit: number;
  is_locked: boolean;
  lockout_until?: string;
  remaining_minute: number;
  remaining_hour: number;
}

export interface SystemStats {
  total_articles: number;
  articles_by_status: Record<string, number>;
  recent_submissions_24h: number;
  last_updated: string;
}

export interface SystemHealth {
  system_status: 'healthy' | 'warning' | 'error';
  activity_metrics: {
    submissions_last_hour: number;
    submissions_last_24h: number;
    active_agents_24h: number;
    active_sites_24h: number;
  };
  publishing_metrics: {
    successful_publishes_24h: number;
    failed_publishes_24h: number;
    failure_rate_percent: number;
  };
  last_updated: string;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// Component prop types
export interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon?: React.ComponentType<any>;
  color?: 'primary' | 'success' | 'warning' | 'error';
}

export interface StatusBadgeProps {
  status: string;
  variant?: 'default' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}