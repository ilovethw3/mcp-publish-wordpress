'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

interface SecurityMetric {
  timestamp: string;
  successful_authentications: number;
  failed_authentications: number;
  rate_limit_violations: number;
  suspicious_activities: number;
}

interface SecurityMetricsChartProps {
  metrics: SecurityMetric[];
  timeRange: string;
}

const SecurityMetricsChart: React.FC<SecurityMetricsChartProps> = ({ 
  metrics, 
  timeRange 
}) => {
  // Simple text-based chart implementation
  // In a real application, you might use a charting library like Chart.js or recharts
  
  const maxValue = Math.max(
    ...metrics.flatMap(m => [
      m.successful_authentications,
      m.failed_authentications,
      m.rate_limit_violations,
      m.suspicious_activities
    ])
  );

  const getBarWidth = (value: number) => {
    return maxValue > 0 ? (value / maxValue) * 100 : 0;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>安全指标趋势 ({timeRange})</CardTitle>
      </CardHeader>
      <CardContent>
        {metrics.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无数据
          </div>
        ) : (
          <div className="space-y-6">
            {/* Legend */}
            <div className="flex flex-wrap gap-4 text-sm">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
                <span>成功认证</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
                <span>认证失败</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-orange-500 rounded mr-2"></div>
                <span>速率限制违规</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-purple-500 rounded mr-2"></div>
                <span>可疑活动</span>
              </div>
            </div>

            {/* Chart */}
            <div className="space-y-4">
              {metrics.slice(-12).map((metric, index) => (
                <div key={index} className="space-y-2">
                  <div className="text-xs text-gray-500">
                    {formatTime(metric.timestamp)}
                  </div>
                  
                  {/* Successful authentications */}
                  <div className="flex items-center space-x-2">
                    <div className="w-12 text-xs text-gray-600">成功</div>
                    <div className="flex-1 bg-gray-100 rounded h-2 relative">
                      <div 
                        className="absolute left-0 top-0 h-full bg-green-500 rounded"
                        style={{ width: `${getBarWidth(metric.successful_authentications)}%` }}
                      />
                    </div>
                    <div className="w-8 text-xs text-gray-600">
                      {metric.successful_authentications}
                    </div>
                  </div>

                  {/* Failed authentications */}
                  <div className="flex items-center space-x-2">
                    <div className="w-12 text-xs text-gray-600">失败</div>
                    <div className="flex-1 bg-gray-100 rounded h-2 relative">
                      <div 
                        className="absolute left-0 top-0 h-full bg-red-500 rounded"
                        style={{ width: `${getBarWidth(metric.failed_authentications)}%` }}
                      />
                    </div>
                    <div className="w-8 text-xs text-gray-600">
                      {metric.failed_authentications}
                    </div>
                  </div>

                  {/* Rate limit violations */}
                  {metric.rate_limit_violations > 0 && (
                    <div className="flex items-center space-x-2">
                      <div className="w-12 text-xs text-gray-600">限制</div>
                      <div className="flex-1 bg-gray-100 rounded h-2 relative">
                        <div 
                          className="absolute left-0 top-0 h-full bg-orange-500 rounded"
                          style={{ width: `${getBarWidth(metric.rate_limit_violations)}%` }}
                        />
                      </div>
                      <div className="w-8 text-xs text-gray-600">
                        {metric.rate_limit_violations}
                      </div>
                    </div>
                  )}

                  {/* Suspicious activities */}
                  {metric.suspicious_activities > 0 && (
                    <div className="flex items-center space-x-2">
                      <div className="w-12 text-xs text-gray-600">可疑</div>
                      <div className="flex-1 bg-gray-100 rounded h-2 relative">
                        <div 
                          className="absolute left-0 top-0 h-full bg-purple-500 rounded"
                          style={{ width: `${getBarWidth(metric.suspicious_activities)}%` }}
                        />
                      </div>
                      <div className="w-8 text-xs text-gray-600">
                        {metric.suspicious_activities}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="border-t pt-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="font-semibold text-green-600">
                    {metrics.reduce((sum, m) => sum + m.successful_authentications, 0)}
                  </div>
                  <div className="text-gray-600">总成功</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-red-600">
                    {metrics.reduce((sum, m) => sum + m.failed_authentications, 0)}
                  </div>
                  <div className="text-gray-600">总失败</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-orange-600">
                    {metrics.reduce((sum, m) => sum + m.rate_limit_violations, 0)}
                  </div>
                  <div className="text-gray-600">限制违规</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-purple-600">
                    {metrics.reduce((sum, m) => sum + m.suspicious_activities, 0)}
                  </div>
                  <div className="text-gray-600">可疑活动</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SecurityMetricsChart;