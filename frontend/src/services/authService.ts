import api from './api';
import type { AuthResponse, TokenResponse } from '@/types';

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export const authService = {
  register: (data: RegisterRequest) =>
    api.post<AuthResponse>('/api/auth/register', data).then((r) => r.data),

  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/api/auth/login', data).then((r) => r.data),

  logout: () => api.post('/api/auth/logout').then((r) => r.data),

  refresh: () =>
    api.post<TokenResponse>('/api/auth/refresh').then((r) => r.data),

  me: () => api.get('/api/auth/me').then((r) => r.data),
};
