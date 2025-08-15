/**
 * Custom React hooks for MCP data fetching and state management
 */

import useSWR from 'swr';
import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { 
  Agent,
  Site, 
  Article,
  SecurityStatus,
  SystemStats,
  SystemHealth,
  SessionInfo,
  AuditEvent,
  ApiResponse 
} from '@/types';

// SWR fetcher function
const fetcher = (url: string) => fetch(url).then(res => res.json());

// ========== Articles Hooks ==========

export function useArticles(filters?: {
  status?: string;
  search?: string;
  agent_id?: string;
  target_site?: string;
  limit?: number;
}) {
  const { data, error, mutate, isLoading } = useSWR(
    ['articles', JSON.stringify(filters)],
    () => apiClient.getArticles(filters),
    {
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: true,
    }
  );

  return {
    articles: data?.success ? data.data?.articles || [] : [],
    total: data?.success ? data.data?.total || 0 : 0,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

export function useArticle(id: number) {
  const { data, error, mutate, isLoading } = useSWR(
    id ? ['article', id] : null,
    () => apiClient.getArticleById(id),
    {
      refreshInterval: 15000,
    }
  );

  const approveArticle = useCallback(async (reviewerNotes?: string) => {
    const result = await apiClient.approveArticle(id, reviewerNotes);
    if (result.success) {
      mutate(); // Refresh the article data
    }
    return result;
  }, [id, mutate]);

  const rejectArticle = useCallback(async (rejectionReason: string) => {
    const result = await apiClient.rejectArticle(id, rejectionReason);
    if (result.success) {
      mutate(); // Refresh the article data
    }
    return result;
  }, [id, mutate]);

  return {
    article: data?.success ? data.data : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
    approveArticle,
    rejectArticle,
  };
}

// ========== Agents Hooks ==========

export function useAgents(includeInactive = false) {
  const { data, error, mutate, isLoading } = useSWR(
    ['agents', includeInactive],
    () => apiClient.getAgents(includeInactive),
    {
      refreshInterval: 60000, // Refresh every minute
      onError: (error) => {
        // 只在网络错误或真正的服务器错误时显示错误
        // 404 或空数据不算错误
        console.warn('Agent data fetch warning:', error);
      }
    }
  );

  // 更智能的错误处理：区分真正的错误和正常的空状态
  const hasRealError = error && !error.message?.includes('404') && !error.message?.includes('HTTP error! status: 404');
  const dataError = data?.success === false && !data.error?.includes('暂无代理');

  return {
    agents: data?.success ? data.data?.agents || [] : [],
    total: data?.success ? data.data?.total || 0 : 0,
    loading: isLoading,
    error: (hasRealError || dataError) ? (data?.error || error?.message) : null,
    refresh: mutate,
  };
}

export function useAgentStats(agentId: string) {
  const { data, error, mutate, isLoading } = useSWR(
    agentId ? ['agent-stats', agentId] : null,
    () => apiClient.getAgentStats(agentId),
    {
      refreshInterval: 30000,
    }
  );

  return {
    stats: data?.success ? data.data : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

export function useAgentArticles(agentId: string) {
  const { data, error, mutate, isLoading } = useSWR(
    agentId ? ['agent-articles', agentId] : null,
    () => apiClient.getAgentArticles(agentId),
    {
      refreshInterval: 60000,
    }
  );

  return {
    articles: data?.success ? data.data?.articles || [] : [],
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

// ========== Sites Hooks ==========

export function useSites(includeInactive = false) {
  const { data, error, mutate, isLoading } = useSWR(
    ['sites', includeInactive],
    () => apiClient.getSites(includeInactive),
    {
      refreshInterval: 60000,
    }
  );

  return {
    sites: data?.success ? data.data?.sites || [] : [],
    total: data?.success ? data.data?.total || 0 : 0,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

export function useSiteHealth(siteId: string) {
  const { data, error, mutate, isLoading } = useSWR(
    siteId ? ['site-health', siteId] : null,
    () => apiClient.getSiteHealth(siteId),
    {
      refreshInterval: 30000,
    }
  );

  return {
    health: data?.success ? data.data : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

export function useSiteArticles(siteId: string) {
  const { data, error, mutate, isLoading } = useSWR(
    siteId ? ['site-articles', siteId] : null,
    () => apiClient.getSiteArticles(siteId),
    {
      refreshInterval: 60000,
    }
  );

  return {
    articles: data?.success ? data.data?.articles || [] : [],
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

// ========== Security Hooks ==========

export function useSecurityStatus() {
  const { data, error, mutate, isLoading } = useSWR(
    'security-status',
    () => apiClient.getSecurityStatus(),
    {
      refreshInterval: 15000, // Refresh every 15 seconds for security data
    }
  );

  return {
    status: data?.success ? data.data : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

export function useActiveSessions() {
  const { data, error, mutate, isLoading } = useSWR(
    'active-sessions',
    () => apiClient.getActiveSessions(),
    {
      refreshInterval: 10000, // Refresh every 10 seconds
    }
  );

  const endSession = useCallback(async (agentId: string) => {
    const result = await apiClient.endAgentSession(agentId);
    if (result.success) {
      mutate(); // Refresh sessions list
    }
    return result;
  }, [mutate]);

  return {
    sessions: data?.success ? data.data?.active_sessions || [] : [],
    total: data?.success ? data.data?.total_sessions || 0 : 0,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
    endSession,
  };
}

export function useAuditEvents(options?: {
  limit?: number;
  agent_id?: string;
  hours?: number;
}) {
  const { data, error, mutate, isLoading } = useSWR(
    ['audit-events', JSON.stringify(options)],
    () => apiClient.getAuditEvents(options),
    {
      refreshInterval: 30000,
    }
  );

  return {
    events: data?.success ? data.data?.events || [] : [],
    summary: data?.success ? data.data?.summary : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

// ========== Statistics Hooks ==========

export function useSystemStats() {
  const { data, error, mutate, isLoading } = useSWR(
    'system-stats',
    () => apiClient.getSystemStats(),
    {
      refreshInterval: 30000,
    }
  );

  return {
    stats: data?.success ? data.data : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

export function useSystemHealth() {
  const { data, error, mutate, isLoading } = useSWR(
    'system-health',
    () => apiClient.getSystemHealth(),
    {
      refreshInterval: 15000,
    }
  );

  return {
    health: data?.success ? data.data : null,
    loading: isLoading,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
  };
}

// ========== Connection Status Hook ==========

export function useConnectionStatus() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkConnection = useCallback(async () => {
    try {
      const connected = await apiClient.testConnection();
      setIsConnected(connected);
      setLastChecked(new Date());
      return connected;
    } catch (error) {
      setIsConnected(false);
      setLastChecked(new Date());
      return false;
    }
  }, []);

  // Auto-check connection status periodically
  const { data: pingData } = useSWR(
    'connection-ping',
    () => apiClient.ping(),
    {
      refreshInterval: 60000, // Check every minute
      onSuccess: (data) => {
        setIsConnected(data.success && data.data?.status === 'ok');
        setLastChecked(new Date());
      },
      onError: () => {
        setIsConnected(false);
        setLastChecked(new Date());
      },
    }
  );

  return {
    isConnected,
    lastChecked,
    checkConnection,
  };
}

// ========== Real-time Updates Hook ==========

export function useRealTimeUpdates(eventType: string, onUpdate: (data: any) => void) {
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (eventSource) {
      eventSource.close();
    }

    const es = apiClient.createEventSource(`/events/${eventType}`);
    
    es.onopen = () => {
      setIsConnected(true);
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    es.onerror = () => {
      setIsConnected(false);
    };

    setEventSource(es);

    return () => {
      es.close();
      setIsConnected(false);
    };
  }, [eventType, onUpdate]);

  const disconnect = useCallback(() => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
      setIsConnected(false);
    }
  }, [eventSource]);

  return {
    isConnected,
    connect,
    disconnect,
  };
}