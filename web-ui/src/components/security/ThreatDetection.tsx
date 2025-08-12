'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';

interface ThreatAlert {
  id: string;
  type: 'brute_force' | 'suspicious_ip' | 'rate_limit_abuse' | 'anomalous_behavior';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  timestamp: string;
  source_ip?: string;
  agent_id?: string;
  resolved: boolean;
  actions_taken?: string[];
}

interface ThreatDetectionProps {
  threats: ThreatAlert[];
  onResolveThreat: (threatId: string) => void;
  onBlockIP: (ip: string) => void;
  loading?: boolean;
}

const ThreatDetection: React.FC<ThreatDetectionProps> = ({
  threats,
  onResolveThreat,
  onBlockIP,
  loading = false
}) => {
  const [selectedThreat, setSelectedThreat] = useState<ThreatAlert | null>(null);

  const getThreatIcon = (type: string) => {
    switch (type) {
      case 'brute_force': return '🔨';
      case 'suspicious_ip': return '🌐';
      case 'rate_limit_abuse': return '⚡';
      case 'anomalous_behavior': return '🚨';
      default: return '⚠️';
    }
  };

  const getThreatColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'warning';
      case 'low': return 'secondary';
      default: return 'primary';
    }
  };

  const getSeverityText = (severity: string) => {
    switch (severity) {
      case 'critical': return '严重';
      case 'high': return '高';
      case 'medium': return '中';
      case 'low': return '低';
      default: return '未知';
    }
  };

  const getTypeText = (type: string) => {
    switch (type) {
      case 'brute_force': return '暴力破解';
      case 'suspicious_ip': return '可疑IP';
      case 'rate_limit_abuse': return '速率滥用';
      case 'anomalous_behavior': return '异常行为';
      default: return '未知威胁';
    }
  };

  const unresolvedThreats = threats.filter(t => !t.resolved);
  const criticalThreats = unresolvedThreats.filter(t => t.severity === 'critical');
  const highThreats = unresolvedThreats.filter(t => t.severity === 'high');

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>威胁检测</CardTitle>
          <div className="flex items-center space-x-2">
            {criticalThreats.length > 0 && (
              <StatusBadge 
                status={`${criticalThreats.length} 严重`} 
                variant="default" 
                size="sm" 
              />
            )}
            {highThreats.length > 0 && (
              <StatusBadge 
                status={`${highThreats.length} 高危`} 
                variant="default" 
                size="sm" 
              />
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500">正在检测威胁...</div>
          </div>
        ) : unresolvedThreats.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">🛡️</div>
            <div>当前无威胁检测</div>
            <div className="text-sm">系统运行正常</div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Threat Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-b pb-4">
              <div className="text-center">
                <div className="font-semibold text-red-600">{criticalThreats.length}</div>
                <div className="text-gray-600">严重威胁</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-orange-600">{highThreats.length}</div>
                <div className="text-gray-600">高危威胁</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-yellow-600">
                  {unresolvedThreats.filter(t => t.severity === 'medium').length}
                </div>
                <div className="text-gray-600">中危威胁</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-blue-600">
                  {unresolvedThreats.filter(t => t.severity === 'low').length}
                </div>
                <div className="text-gray-600">低危威胁</div>
              </div>
            </div>

            {/* Threat List */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {unresolvedThreats
                .sort((a, b) => {
                  // Sort by severity and timestamp
                  const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
                  const severityDiff = (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);
                  if (severityDiff !== 0) return severityDiff;
                  return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
                })
                .map((threat) => (
                  <div 
                    key={threat.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getThreatIcon(threat.type)}</span>
                        <div>
                          <div className="font-medium text-gray-900">{threat.title}</div>
                          <div className="text-sm text-gray-500">
                            {getTypeText(threat.type)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <StatusBadge 
                          status={getSeverityText(threat.severity)} 
                          variant="default"
                          size="sm"
                        />
                      </div>
                    </div>

                    <div className="text-sm text-gray-700 mb-3">
                      {threat.description}
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <div className="space-x-4">
                        <span>时间: {new Date(threat.timestamp).toLocaleString('zh-CN')}</span>
                        {threat.source_ip && <span>IP: {threat.source_ip}</span>}
                        {threat.agent_id && <span>代理: {threat.agent_id}</span>}
                      </div>
                    </div>

                    {threat.actions_taken && threat.actions_taken.length > 0 && (
                      <div className="mb-3">
                        <div className="text-xs font-medium text-gray-600 mb-1">已采取措施:</div>
                        <div className="flex flex-wrap gap-1">
                          {threat.actions_taken.map((action, index) => (
                            <span 
                              key={index}
                              className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                            >
                              {action}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => onResolveThreat(threat.id)}
                      >
                        标记已解决
                      </Button>
                      {threat.source_ip && (
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => onBlockIP(threat.source_ip!)}
                        >
                          阻止IP
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedThreat(threat)}
                      >
                        查看详情
                      </Button>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Threat Detail Modal */}
        {selectedThreat && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto mx-4">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      威胁详情: {selectedThreat.title}
                    </h3>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                      <span>类型: {getTypeText(selectedThreat.type)}</span>
                      <span>严重级别: {getSeverityText(selectedThreat.severity)}</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedThreat(null)}
                  >
                    关闭
                  </Button>
                </div>
              </div>

              <div className="p-6 space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">威胁描述</h4>
                  <p className="text-gray-700">{selectedThreat.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">基本信息</h4>
                    <div className="space-y-1">
                      <div>时间: {new Date(selectedThreat.timestamp).toLocaleString('zh-CN')}</div>
                      {selectedThreat.source_ip && <div>源IP: {selectedThreat.source_ip}</div>}
                      {selectedThreat.agent_id && <div>涉及代理: {selectedThreat.agent_id}</div>}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">状态信息</h4>
                    <div className="space-y-1">
                      <div>状态: {selectedThreat.resolved ? '已解决' : '未解决'}</div>
                      <div>威胁ID: {selectedThreat.id}</div>
                    </div>
                  </div>
                </div>

                {selectedThreat.actions_taken && selectedThreat.actions_taken.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">已采取措施</h4>
                    <ul className="list-disc list-inside text-gray-700 space-y-1">
                      {selectedThreat.actions_taken.map((action, index) => (
                        <li key={index}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="border-t pt-4 flex space-x-4">
                  {!selectedThreat.resolved && (
                    <Button
                      variant="primary"
                      onClick={() => {
                        onResolveThreat(selectedThreat.id);
                        setSelectedThreat(null);
                      }}
                    >
                      标记已解决
                    </Button>
                  )}
                  {selectedThreat.source_ip && (
                    <Button
                      variant="danger"
                      onClick={() => {
                        onBlockIP(selectedThreat.source_ip!);
                        setSelectedThreat(null);
                      }}
                    >
                      阻止该IP
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ThreatDetection;