import apiClient from './client';

export interface User {
  id: number;
  email: string;
  name: string;
  profile_picture: string | null;
  oauth_provider: string;
  default_region: string | null;
  default_job_source: string | null;
  email_notifications: boolean;
  created_at: string;
  last_login: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface OAuthProvider {
  name: string;
  display_name: string;
}

// Get list of available OAuth providers
export const getOAuthProviders = async (): Promise<OAuthProvider[]> => {
  const response = await apiClient.get<{ providers: OAuthProvider[] }>('/auth/providers');
  return response.data.providers;
};

// Initiate OAuth login (redirects to provider)
export const initiateOAuthLogin = (provider: string): void => {
  window.location.href = `/api/auth/login/${provider}`;
};

// Get current user
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<{ user: User }>('/auth/me');
  return response.data.user;
};

// Refresh access token
export const refreshToken = async (refreshToken: string): Promise<{ access_token: string }> => {
  const response = await apiClient.post<{ access_token: string }>(
    '/auth/refresh',
    {},
    {
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    }
  );
  return response.data;
};

// Logout user
export const logout = async (): Promise<void> => {
  await apiClient.post('/auth/logout');
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// Update user preferences
export interface UpdatePreferencesRequest {
  default_region?: string;
  default_job_source?: string;
  email_notifications?: boolean;
}

export const updateUserPreferences = async (
  preferences: UpdatePreferencesRequest
): Promise<User> => {
  const response = await apiClient.put<User>('/auth/user/preferences', preferences);
  return response.data;
};
