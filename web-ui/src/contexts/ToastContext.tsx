/**
 * Toast Context - Global Toast Management
 * 
 * Provides toast notification functionality throughout the application
 * using React Context API.
 */

'use client';

import React, { createContext, useContext } from 'react';
import { useToast, UseToastReturn } from '@/hooks/useToast';
import { ToastContainer } from '@/components/ui/Toast';

interface ToastContextType extends UseToastReturn {}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

interface ToastProviderProps {
  children: React.ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const toastState = useToast();

  return (
    <ToastContext.Provider value={toastState}>
      {children}
      <ToastContainer 
        toasts={toastState.toasts} 
        onRemove={toastState.removeToast} 
      />
    </ToastContext.Provider>
  );
};

export const useToastContext = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    // During SSR/build time, return a no-op implementation
    if (typeof window === 'undefined') {
      return {
        toasts: [],
        addToast: () => '',
        removeToast: () => {},
        clearToasts: () => {},
        showSuccess: () => '',
        showError: () => '',
        showWarning: () => '',
        showInfo: () => '',
      };
    }
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
};

export default ToastProvider;