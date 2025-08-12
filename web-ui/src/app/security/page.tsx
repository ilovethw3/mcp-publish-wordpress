'use client';

import React, { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatsCard from '@/components/ui/StatsCard';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useSecurityStatus, useActiveSessions, useAuditEvents } from '@/hooks/useMCPData';
import { AuditEvent, SecurityStatus, SessionInfo } from '@/types';
import SecurityMetricsChart from '@/components/security/SecurityMetricsChart';
import ThreatDetection from '@/components/security/ThreatDetection';

interface SecurityEventCardProps {
  event: AuditEvent;
}

const SecurityEventCard: React.FC<SecurityEventCardProps> = ({ event }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'primary';
      default: return 'secondary';
    }
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case 'login_success': return '✅';
      case 'login_failed': return '❌';
      case 'api_access': return '🔌';
      case 'rate_limit_exceeded': return '⚡';
      case 'permission_denied': return '🚫';
      case 'account_locked': return '🔒';
      case 'suspicious_activity': return '⚠️';
      default: return '📝';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getEventTypeIcon(event.action)}</span>
          <div>
            <div className="font-medium text-gray-900">{event.action}</div>
            <div className="text-sm text-gray-500">
              {event.agent_id && `代理: ${event.agent_id}`}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <StatusBadge 
            status={event.success ? 'success' : 'error'} 
            size="sm"
            variant="default"
          />
          <span className="text-xs text-gray-500">
            {new Date(event.timestamp).toLocaleString('zh-CN')}
          </span>
        </div>
      </div>
      
      {event.details && (
        <div className="text-sm text-gray-700 mb-2">{JSON.stringify(event.details)}</div>
      )}
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>IP: {event.ip_address || 'N/A'}</span>
        {event.user_agent && (
          <span className="truncate max-w-xs">UA: {event.user_agent}</span>
        )}
      </div>
    </div>
  );
};

interface ActiveSessionCardProps {
  session: SessionInfo;
  onEndSession: (agentId: string) => void;
  isEndingSession: boolean;
}

const ActiveSessionCard: React.FC<ActiveSessionCardProps> = ({ 
  session, 
  onEndSession, 
  isEndingSession 
}) => {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="font-medium text-gray-900">{session.agent_name}</div>
          <div className="text-sm text-gray-500">ID: {session.agent_id}</div>
        </div>
        <StatusBadge status="active" size="sm" />
      </div>
      
      <div className="space-y-2 text-sm text-gray-600 mb-3">
        <div className="flex justify-between">
          <span>开始时间:</span>
          <span>{new Date(session.created_at).toLocaleString('zh-CN')}</span>
        </div>
        <div className="flex justify-between">
          <span>最后活动:</span>
          <span>{new Date(session.last_activity).toLocaleString('zh-CN')}</span>
        </div>
        <div className="flex justify-between">
          <span>请求数:</span>
          <span>{session.request_count}</span>
        </div>
      </div>
      
      <Button
        size="sm"
        variant="danger"
        onClick={() => onEndSession(session.agent_id)}
        disabled={isEndingSession}
        className="w-full"
      >
        {isEndingSession ? <LoadingSpinner size="sm" /> : '结束会话'}
      </Button>
    </div>
  );
};

const SecurityPage = () => {
  const [auditFilters, setAuditFilters] = useState({
    hours: 24,
    agent_id: '',
    limit: 50
  });
  const [endingSessionId, setEndingSessionId] = useState<string | null>(null);

  const { status: securityStatus, loading: securityLoading, refresh: refreshSecurity } = useSecurityStatus();
  const { sessions, loading: sessionsLoading, endSession, refresh: refreshSessions } = useActiveSessions();
  const { events, summary, loading: eventsLoading, refresh: refreshEvents } = useAuditEvents(auditFilters);

  const handleEndSession = async (agentId: string) => {
    setEndingSessionId(agentId);
    try {
      const result = await endSession(agentId);
      if (result.success) {
        refreshSessions();
      } else {
        alert(`结束会话失败: ${result.error}`);
      }
    } catch (error) {
      alert(`结束会话失败: ${error}`);
    } finally {
      setEndingSessionId(null);
    }
  };

  const refreshAllData = () => {
    refreshSecurity();
    refreshSessions();
    refreshEvents();
  };

  // Calculate security metrics
  const criticalEvents = events.filter(e => !e.success).length;
  const failedLogins = events.filter(e => e.action === 'login' && !e.success).length;
  const rateLimitViolations = events.filter(e => e.action === 'rate_limit_exceeded').length;

  // Mock data for demo - in real app this would come from API
  const mockSecurityMetrics = [
    {
      timestamp: new Date(Date.now() - 11 * 60000).toISOString(),
      successful_authentications: 15,
      failed_authentications: 2,
      rate_limit_violations: 0,
      suspicious_activities: 0
    },
    {
      timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
      successful_authentications: 12,
      failed_authentications: 1,
      rate_limit_violations: 0,
      suspicious_activities: 0
    },
    {
      timestamp: new Date(Date.now() - 9 * 60000).toISOString(),
      successful_authentications: 18,
      failed_authentications: 3,
      rate_limit_violations: 1,
      suspicious_activities: 1
    },
    // Add more data points...
  ];

  const mockThreats = [
    {
      id: 'threat-001',
      type: 'brute_force' as const,
      severity: 'high' as const,
      title: '暴力破解攻击检测',
      description: '检测到来自IP 192.168.1.100的多次登录失败尝试',
      timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
      source_ip: '192.168.1.100',
      agent_id: 'unknown',
      resolved: false,
      actions_taken: ['临时限制IP访问', '增强监控']
    },
    {
      id: 'threat-002',
      type: 'rate_limit_abuse' as const,
      severity: 'medium' as const,
      title: '速率限制违规',
      description: '代理content-creator-001超出每分钟请求限制',
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      agent_id: 'content-creator-001',
      resolved: false
    }
  ];

  const handleResolveThreat = (threatId: string) => {
    console.log('Resolving threat:', threatId);
    // In real app, call API to resolve threat
  };

  const handleBlockIP = (ip: string) => {
    console.log('Blocking IP:', ip);
    // In real app, call API to block IP
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">安全监控</h2>
            <p className="mt-1 text-sm text-gray-600">
              监控系统安全状态、会话和审计事件
            </p>
          </div>
          <Button onClick={refreshAllData} disabled={securityLoading}>
            {securityLoading ? <LoadingSpinner size="sm" className="mr-2" /> : null}
            刷新数据
          </Button>
        </div>

        {/* Security Overview */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
          <StatsCard
            title="活跃会话"
            value={securityStatus?.active_sessions || 0}
            loading={securityLoading}
            description="当前活跃的代理会话"
            color="primary"
          />
          <StatsCard
            title="锁定代理"
            value={securityStatus?.rate_limiting?.locked_agents || 0}
            loading={securityLoading}
            description="因违反速率限制被锁定"
            color={(securityStatus?.rate_limiting?.locked_agents || 0) > 0 ? 'error' : 'success'}
          />
          <StatsCard
            title="严重事件"
            value={criticalEvents}
            loading={eventsLoading}
            description="24小时内严重安全事件"
            color={criticalEvents > 0 ? 'error' : 'success'}
          />
          <StatsCard
            title="失败登录"
            value={failedLogins}
            loading={eventsLoading}
            description="24小时内失败登录尝试"
            color={failedLogins > 5 ? 'warning' : 'success'}
          />
        </div>

        {/* Security Status Details */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Security Status Card */}
          <Card>
            <CardHeader>
              <CardTitle>安全状态详情</CardTitle>
            </CardHeader>
            <CardContent>
              {securityLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : securityStatus ? (
                <div className="space-y-4">
                  {/* Rate Limiting Status */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">速率限制状态</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">锁定代理:</span>
                        <span className="ml-2 font-semibold">{securityStatus.rate_limiting.locked_agents}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">总违规次数:</span>
                        <span className="ml-2 font-semibold">{rateLimitViolations}</span>
                      </div>
                    </div>
                  </div>

                  {/* Authentication Status */}
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2">认证状态</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">活跃会话:</span>
                        <span className="ml-2 font-semibold">{securityStatus.active_sessions}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">锁定时长:</span>
                        <span className="ml-2 font-semibold">{securityStatus.rate_limiting.lockout_duration_minutes}分钟</span>
                      </div>
                    </div>
                  </div>

                  {/* Audit Summary */}
                  {securityStatus.audit_summary && (
                    <div className="border-t pt-4">
                      <h4 className="font-medium text-gray-900 mb-2">审计摘要(24h)</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">总事件:</span>
                          <span className="ml-2 font-semibold">{securityStatus.audit_summary.total_events}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">成功率:</span>
                          <span className="ml-2 font-semibold">{securityStatus.audit_summary.success_rate.toFixed(1)}%</span>
                        </div>
                        <div>
                          <span className="text-gray-600">失败事件:</span>
                          <span className="ml-2 font-semibold">{securityStatus.audit_summary.failed_events}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">可疑活动:</span>
                          <span className="ml-2 font-semibold">{securityStatus.audit_summary.failed_events || 0}</span>
                        </div>
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

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>快速操作</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">速率限制违规:</span>
                    <span className="ml-2 font-semibold">{rateLimitViolations}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">可疑IP数量:</span>
                    <span className="ml-2 font-semibold">{new Set(events.filter(e => !e.success).map(e => e.ip_address).filter(Boolean)).size}</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Button size="sm" variant="outline" className="w-full">
                    导出审计报告
                  </Button>
                  <Button size="sm" variant="outline" className="w-full">
                    查看IP白名单
                  </Button>
                  <Button size="sm" variant="outline" className="w-full">
                    安全策略配置
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Security Metrics Chart */}
        <SecurityMetricsChart 
          metrics={mockSecurityMetrics} 
          timeRange="最近12小时" 
        />

        {/* Threat Detection */}
        <ThreatDetection
          threats={mockThreats}
          onResolveThreat={handleResolveThreat}
          onBlockIP={handleBlockIP}
          loading={false}
        />

        {/* Active Sessions */}
        <Card>
          <CardHeader>
            <CardTitle>活跃会话</CardTitle>
          </CardHeader>
          <CardContent>
            {sessionsLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : sessions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sessions.map((session) => (
                  <ActiveSessionCard
                    key={session.agent_id}
                    session={session}
                    onEndSession={handleEndSession}
                    isEndingSession={endingSessionId === session.agent_id}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                当前没有活跃会话
              </div>
            )}
          </CardContent>
        </Card>

        {/* Audit Events */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>审计事件</CardTitle>
              <div className="flex items-center space-x-4">
                <select 
                  className="text-sm border border-gray-300 rounded-md px-3 py-1"
                  value={auditFilters.hours}
                  onChange={(e) => setAuditFilters({...auditFilters, hours: parseInt(e.target.value)})}
                >
                  <option value={1}>最近1小时</option>
                  <option value={24}>最近24小时</option>
                  <option value={168}>最近7天</option>
                  <option value={720}>最近30天</option>
                </select>
                <input
                  type="text"
                  placeholder="筛选代理ID..."
                  className="text-sm border border-gray-300 rounded-md px-3 py-1"
                  value={auditFilters.agent_id}
                  onChange={(e) => setAuditFilters({...auditFilters, agent_id: e.target.value})}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {eventsLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : events.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {events.map((event, index) => (
                  <SecurityEventCard key={index} event={event} />
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                没有找到审计事件
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default SecurityPage;