import useSWR from 'swr';

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

interface UsersResponse {
  users: User[];
  total: number;
  skip: number;
  limit: number;
}

interface UseUsersOptions {
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
}

const fetcher = async (url: string) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch');
  }
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error || 'Failed to fetch data');
  }
  return data.data;
};

export function useUsers(options: UseUsersOptions = {}) {
  const { skip = 0, limit = 100, search = '', is_active } = options;
  
  // Build query string
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  });
  
  if (search) {
    params.append('search', search);
  }
  
  if (is_active !== undefined) {
    params.append('is_active', is_active.toString());
  }
  
  const { data, error, mutate } = useSWR<UsersResponse>(
    `/api/users?${params.toString()}`,
    fetcher,
    {
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: false,
    }
  );

  return {
    users: data?.users || [],
    total: data?.total || 0,
    skip: data?.skip || 0,
    limit: data?.limit || 0,
    loading: !error && !data,
    error,
    refresh: mutate,
  };
}

export function useUser(userId: number) {
  const { data, error, mutate } = useSWR<User>(
    userId ? `/api/users/${userId}` : null,
    fetcher
  );

  return {
    user: data,
    loading: !error && !data,
    error,
    refresh: mutate,
  };
}

// User management functions
export async function createUser(userData: {
  username: string;
  email: string;
  password: string;
  is_reviewer?: boolean;
}): Promise<User> {
  const response = await fetch('/api/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || '创建用户失败');
  }
  
  return data.data;
}

export async function updateUser(
  userId: number,
  updateData: {
    username?: string;
    email?: string;
    is_reviewer?: boolean;
    is_active?: boolean;
  }
): Promise<User> {
  const response = await fetch(`/api/users/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updateData),
  });

  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || '更新用户失败');
  }
  
  return data.data;
}

export async function deleteUser(userId: number): Promise<void> {
  const response = await fetch(`/api/users/${userId}`, {
    method: 'DELETE',
  });

  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || '删除用户失败');
  }
}

export async function changePassword(
  userId: number,
  newPassword: string
): Promise<void> {
  const response = await fetch(`/api/users/${userId}/change-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ new_password: newPassword }),
  });

  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || '密码修改失败');
  }
}