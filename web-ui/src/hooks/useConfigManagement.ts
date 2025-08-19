/**
 * Configuration Management Hooks
 * Handles CRUD operations for agents and sites configuration
 */

import { useState, useCallback } from 'react';
import useSWR from 'swr';
import { FullConfigAgent } from '@/types';

interface Site {
  id: string;
  name: string;
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
    on_connection_failure: boolean;
    email_notifications: string[];
  };
  created_at: string;
  status: 'active' | 'inactive';
  priority: number;
}

// Agent Configuration Management
export function useAgentConfig() {
  const { data, error, mutate, isLoading } = useSWR(
    '/api/config/agents',
    (url) => fetch(url).then(res => res.json()),
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
    }
  );

  const [isOperating, setIsOperating] = useState(false);

  const createAgent = useCallback(async (agentData: Omit<FullConfigAgent, 'created_at'>) => {
    setIsOperating(true);
    try {
      const response = await fetch('/api/config/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentData),
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to create agent');
      }

      mutate(); // Refresh data
      return result;
    } catch (error) {
      console.error('Failed to create agent:', error);
      throw error;
    } finally {
      setIsOperating(false);
    }
  }, [mutate]);

  const updateAgent = useCallback(async (agentId: string, agentData: Partial<Omit<FullConfigAgent, 'created_at'>>) => {
    setIsOperating(true);
    try {
      const response = await fetch(`/api/config/agents/${agentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentData),
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to update agent');
      }

      // Force refresh with revalidate option
      await mutate(undefined, { revalidate: true });
      
      return result;
    } catch (error) {
      console.error('Failed to update agent:', error);
      throw error;
    } finally {
      setIsOperating(false);
    }
  }, [mutate]);

  const deleteAgent = useCallback(async (agentId: string) => {
    setIsOperating(true);
    try {
      const response = await fetch(`/api/config/agents/${agentId}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to delete agent');
      }

      mutate(); // Refresh data
      return result;
    } catch (error) {
      console.error('Failed to delete agent:', error);
      throw error;
    } finally {
      setIsOperating(false);
    }
  }, [mutate]);

  return {
    agents: data?.success ? data.data.agents || [] : [],
    total: data?.success ? data.data.total || 0 : 0,
    loading: isLoading,
    isOperating,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
    createAgent,
    updateAgent,
    deleteAgent,
  };
}

// Site Configuration Management
export function useSiteConfig() {
  const { data, error, mutate, isLoading } = useSWR(
    '/api/config/sites',
    (url) => fetch(url).then(res => res.json()),
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
    }
  );

  const [isOperating, setIsOperating] = useState(false);

  const createSite = useCallback(async (siteData: Omit<Site, 'created_at'>, testConnection = false) => {
    setIsOperating(true);
    try {
      const response = await fetch('/api/config/sites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...siteData, test_connection: testConnection }),
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to create site');
      }

      mutate(); // Refresh data
      return result;
    } catch (error) {
      console.error('Failed to create site:', error);
      throw error;
    } finally {
      setIsOperating(false);
    }
  }, [mutate]);

  const updateSite = useCallback(async (siteId: string, siteData: Partial<Omit<Site, 'created_at'>>, testConnection = false) => {
    setIsOperating(true);
    try {
      const response = await fetch(`/api/config/sites/${siteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...siteData, test_connection: testConnection }),
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to update site');
      }

      mutate(); // Refresh data
      return result;
    } catch (error) {
      console.error('Failed to update site:', error);
      throw error;
    } finally {
      setIsOperating(false);
    }
  }, [mutate]);

  const deleteSite = useCallback(async (siteId: string) => {
    setIsOperating(true);
    try {
      const response = await fetch(`/api/config/sites/${siteId}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to delete site');
      }

      mutate(); // Refresh data
      return result;
    } catch (error) {
      console.error('Failed to delete site:', error);
      throw error;
    } finally {
      setIsOperating(false);
    }
  }, [mutate]);

  const testSiteConnection = useCallback(async (siteId: string) => {
    try {
      // First get the site data
      const siteResponse = await fetch(`/api/config/sites/${siteId}`);
      if (!siteResponse.ok) {
        throw new Error('Failed to fetch site data');
      }
      
      const siteResult = await siteResponse.json();
      if (!siteResult.success) {
        throw new Error(siteResult.error || 'Failed to fetch site data');
      }
      
      const site = siteResult.data;
      
      // Then test the connection using the site's WordPress config
      const response = await fetch('/api/config/sites/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wordpress_config: site.wordpress_config
        }),
      });

      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to test connection');
      }

      return result;
    } catch (error) {
      console.error('Failed to test site connection:', error);
      throw error;
    }
  }, []);

  return {
    sites: data?.success ? data.data.sites || [] : [],
    total: data?.success ? data.data.total || 0 : 0,
    loading: isLoading,
    isOperating,
    error: data?.success === false ? data.error : error?.message,
    refresh: mutate,
    createSite,
    updateSite,
    deleteSite,
    testSiteConnection,
  };
}

// Toast notification hook
export function useToast() {
  const [toasts, setToasts] = useState<Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  }>>([]);

  const showToast = useCallback((type: 'success' | 'error' | 'warning' | 'info', message: string, duration = 3000) => {
    const id = Math.random().toString(36).substr(2, 9);
    const toast = { id, type, message, duration };
    
    setToasts(prev => [...prev, toast]);
    
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return {
    toasts,
    showToast,
    removeToast,
  };
}