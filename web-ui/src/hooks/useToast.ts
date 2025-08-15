/**
 * useToast Hook - Toast Notification Management
 * 
 * Provides Toast notification functionality with automatic management,
 * different types (success, error, warning, info), and customizable duration.
 */

'use client';

import { useState, useCallback } from 'react';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastOptions {
  duration?: number;
  id?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Generate unique ID for toasts
  const generateId = useCallback(() => {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add a new toast
  const addToast = useCallback((toast: Omit<Toast, 'id'> & { id?: string }) => {
    const newToast: Toast = {
      ...toast,
      id: toast.id || generateId(),
    };

    setToasts(prev => [...prev, newToast]);
    return newToast.id;
  }, [generateId]);

  // Remove a toast by ID
  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  // Clear all toasts
  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Convenience methods for different toast types
  const showSuccess = useCallback((message: string, options?: ToastOptions) => {
    return addToast({
      type: 'success',
      message,
      duration: options?.duration ?? 5000, // Auto-dismiss after 5 seconds
      id: options?.id,
      action: options?.action,
    });
  }, [addToast]);

  const showError = useCallback((message: string, options?: ToastOptions) => {
    return addToast({
      type: 'error',
      message,
      duration: options?.duration ?? 0, // Don't auto-dismiss errors
      id: options?.id,
    });
  }, [addToast]);

  const showWarning = useCallback((message: string, options?: ToastOptions) => {
    return addToast({
      type: 'warning',
      message,
      duration: options?.duration ?? 7000, // Auto-dismiss after 7 seconds
      id: options?.id,
    });
  }, [addToast]);

  const showInfo = useCallback((message: string, options?: ToastOptions) => {
    return addToast({
      type: 'info',
      message,
      duration: options?.duration ?? 5000, // Auto-dismiss after 5 seconds
      id: options?.id,
    });
  }, [addToast]);

  return {
    toasts,
    addToast,
    removeToast,
    clearToasts,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
}

export type UseToastReturn = ReturnType<typeof useToast>;