'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import Cookies from 'js-cookie';

interface User {
  id: number;
  username: string;
  email: string;
  is_reviewer: boolean;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from cookies
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = Cookies.get('auth_token');
      
      if (storedToken) {
        setToken(storedToken);
        try {
          await fetchCurrentUser(storedToken);
        } catch (error) {
          // Token might be invalid, clear it
          console.error('Failed to fetch current user:', error);
          Cookies.remove('auth_token');
          setToken(null);
        }
      }
      
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const fetchCurrentUser = async (authToken: string) => {
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        setUser(data.data);
      } else {
        throw new Error(data.error || 'Failed to fetch user');
      }
    } else {
      throw new Error('Failed to fetch user');
    }
  };

  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success) {
        const { token: newToken, user: userData } = data.data;
        
        // Store token in cookie (7 days expiry)
        Cookies.set('auth_token', newToken, { 
          expires: 7,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'strict'
        });
        
        setToken(newToken);
        setUser(userData);
        
        return { success: true };
      } else {
        return { success: false, error: data.error || '登录失败' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: '网络错误，请稍后重试' };
    }
  };

  const logout = () => {
    Cookies.remove('auth_token');
    setToken(null);
    setUser(null);
    
    // Redirect to login page
    window.location.href = '/login';
  };

  const refreshUser = async () => {
    if (token) {
      try {
        await fetchCurrentUser(token);
      } catch (error) {
        console.error('Failed to refresh user:', error);
        logout();
      }
    }
  };

  const contextValue: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Hook for protecting routes
export const useRequireAuth = () => {
  const { user, isLoading } = useAuth();
  
  useEffect(() => {
    if (!isLoading && !user) {
      window.location.href = '/login';
    }
  }, [user, isLoading]);
  
  return { user, isLoading };
};

// Hook for requiring reviewer permissions
export const useRequireReviewer = () => {
  const { user, isLoading } = useAuth();
  
  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        window.location.href = '/login';
      } else if (!user.is_reviewer) {
        window.location.href = '/';
      }
    }
  }, [user, isLoading]);
  
  return { user, isLoading };
};