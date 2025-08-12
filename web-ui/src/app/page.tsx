'use client';

import React from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import StatsCard from '@/components/ui/StatsCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { 
  useSystemStats, 
  useSystemHealth, 
  useAgents, 
  useSites, 
  useArticles,
  useSecurityStatus 
} from '@/hooks/useMCPData';

const Dashboard = () => {
  const { stats: systemStats, loading: statsLoading } = useSystemStats();
  const { health: systemHealth, loading: healthLoading } = useSystemHealth();
  const { agents, loading: agentsLoading } = useAgents();
  const { sites, loading: sitesLoading } = useSites();
  const { articles: recentArticles, loading: articlesLoading } = useArticles({ limit: 5 });
  const { status: securityStatus, loading: securityLoading } = useSecurityStatus();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">系统概览</h2>
          <p className="mt-1 text-sm text-gray-600">
            多代理多站点WordPress发布系统运行状态
          </p>
        </div>

        {/* System Status Cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="总文章数"
            value={systemStats?.total_articles || 0}
            loading={statsLoading}
            description="系统中的文章总数"
            color="primary"
          />
          <StatsCard
            title="待审核文章"
            value={systemStats?.articles_by_status?.pending_review || 0}
            loading={statsLoading}
            description="等待审核的文章"
            color="warning"
          />
          <StatsCard
            title="活跃代理"
            value={agents.length}
            loading={agentsLoading}
            description="当前活跃的AI代理"
            color="success"
          />
          <StatsCard
            title="配置站点"
            value={sites.length}
            loading={sitesLoading}
            description="已配置的WordPress站点"
            color="primary"
          />
        </div>

        {/* System Health and Recent Activity */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* System Health */}
          <Card>
            <CardHeader>
              <CardTitle>系统健康状态</CardTitle>
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : systemHealth ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">总体状态</span>
                    <StatusBadge status={systemHealth.system_status} />
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">最近1小时提交</div>
                      <div className="font-semibold">{systemHealth.activity_metrics.submissions_last_hour}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">最近24小时提交</div>
                      <div className="font-semibold">{systemHealth.activity_metrics.submissions_last_24h}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">活跃代理（24h）</div>
                      <div className="font-semibold">{systemHealth.activity_metrics.active_agents_24h}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">活跃站点（24h）</div>
                      <div className="font-semibold">{systemHealth.activity_metrics.active_sites_24h}</div>
                    </div>
                  </div>
                  <div className="border-t pt-4">
                    <div className="text-sm text-gray-600">发布成功率（24h）</div>
                    <div className="text-2xl font-bold text-green-600">
                      {(100 - systemHealth.publishing_metrics.failure_rate_percent).toFixed(1)}%
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  无法获取系统健康数据
                </div>
              )}
            </CardContent>
          </Card>

          {/* Security Status */}
          <Card>
            <CardHeader>
              <CardTitle>安全状态</CardTitle>
            </CardHeader>
            <CardContent>
              {securityLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : securityStatus ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">活跃会话</div>
                      <div className="font-semibold">{securityStatus.active_sessions}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">锁定代理</div>
                      <div className="font-semibold">{securityStatus.rate_limiting.locked_agents}</div>
                    </div>
                  </div>
                  {securityStatus.audit_summary && (
                    <div className="border-t pt-4">
                      <div className="text-sm text-gray-600">安全事件成功率（24h）</div>
                      <div className="text-2xl font-bold text-green-600">
                        {securityStatus.audit_summary.success_rate.toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        总事件: {securityStatus.audit_summary.total_events}，
                        失败: {securityStatus.audit_summary.failed_events}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  无法获取安全状态数据
                </div>
              )}
            </CardContent>
          </Card>
        </div>

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
            ) : recentArticles.length > 0 ? (
              <div className="space-y-4">
                {recentArticles.map((article) => (
                  <div 
                    key={article.id} 
                    className="flex items-center justify-between border-b border-gray-100 pb-4 last:border-b-0"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{article.title}</h3>
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        {article.submitting_agent && (
                          <span>代理: {article.submitting_agent.name}</span>
                        )}
                        {article.target_site && (
                          <span>站点: {article.target_site.name}</span>
                        )}
                        <span>创建: {new Date(article.created_at).toLocaleString('zh-CN')}</span>
                      </div>
                    </div>
                    <StatusBadge status={article.status} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                暂无文章数据
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;