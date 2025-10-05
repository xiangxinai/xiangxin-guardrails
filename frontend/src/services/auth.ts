import axios from 'axios';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface VerifyEmailRequest {
  email: string;
  verification_code: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  api_key?: string;
  tenant_id?: string;
  is_super_admin?: boolean;
}

export interface UserInfo {
  id: string;
  email: string;
  api_key: string;
  is_active: boolean;
  is_verified: boolean;
  is_super_admin: boolean;
  rate_limit: number;  // 租户速度限制（每秒请求数，0表示无限制，默认为1）
}

// 获取base URL的辅助函数，与api.ts保持一致
const getBaseURL = () => {
  // 优先使用环境变量中的API URL
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // 生产环境和Docker环境都使用相对路径，通过nginx代理
  return '';
};

class AuthService {
  private baseURL: string;

  constructor() {
    this.baseURL = getBaseURL();
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(`${this.baseURL}/api/v1/users/login`, credentials);
    return response.data;
  }

  async register(data: RegisterRequest): Promise<{ message: string }> {
    const response = await axios.post<{ message: string }>(`${this.baseURL}/api/v1/users/register`, data);
    return response.data;
  }

  async verifyEmail(data: VerifyEmailRequest): Promise<{ message: string }> {
    const response = await axios.post<{ message: string }>(`${this.baseURL}/api/v1/users/verify-email`, data);
    return response.data;
  }

  async getCurrentUser(): Promise<UserInfo> {
    const token = this.getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await axios.get<UserInfo>(`${this.baseURL}/api/v1/users/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  async regenerateApiKey(): Promise<{ api_key: string }> {
    const token = this.getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }
    const response = await axios.post<{ api_key: string }>(`${this.baseURL}/api/v1/users/regenerate-api-key`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  }

  async logout(): Promise<void> {
    const token = this.getToken();
    if (token) {
      try {
        await axios.post(`${this.baseURL}/api/v1/auth/logout`, {}, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout API call failed:', error);
      }
    }
    this.clearToken();
  }

  setToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  clearToken(): void {
    localStorage.removeItem('auth_token');
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) {
      return false;
    }

    try {
      // 简单检查token是否过期（这里可以解析JWT payload来检查exp字段）
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }
}

export const authService = new AuthService();