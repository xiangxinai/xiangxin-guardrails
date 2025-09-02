import axios from 'axios';
import { message } from 'antd';
import type {
  ApiResponse,
  GuardrailRequest,
  GuardrailResponse,
  DetectionResult,
  PaginatedResponse,
  DashboardStats,
  Blacklist,
  Whitelist,
  ResponseTemplate
} from '../types';

// 创建axios实例 - 使用环境变量中的API URL
const getBaseURL = () => {
  // 优先使用环境变量中的API URL
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // 生产环境和Docker环境都使用相对路径，通过nginx代理
  return '';
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 跳过认证路由，不添加Authorization头部
    if (config.url && config.url.includes('/auth/')) {
      return config;
    }
    
    // 添加认证头 - 优先使用JWT token，其次使用API key
    const authToken = localStorage.getItem('auth_token');
    const apiToken = localStorage.getItem('api_token');

    const token = authToken || apiToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // 添加用户切换会话token
    const switchToken = localStorage.getItem('switch_session_token');
    if (switchToken) {
      config.headers['X-Switch-Session'] = switchToken;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const url: string | undefined = error.config?.url;
    
    // 静默处理某些非关键性401（例如检查切换状态时未就绪）
    if (status === 401 && url && url.includes('/admin/current-switch')) {
      return Promise.reject(error);
    }
    
    // 对于429限速错误，让业务逻辑自行处理，不在全局显示弹窗
    if (status === 429) {
      return Promise.reject(error);
    }
    
    const errorMessage = error.response?.data?.detail || error.message || '请求失败';
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

// 护栏API
export const guardrailsApi = {
  // 检测内容
  check: (data: GuardrailRequest): Promise<GuardrailResponse> =>
    api.post('/v1/guardrails', data).then(res => res.data),
  
  // 健康检查
  health: () => api.get('/v1/guardrails/health').then(res => res.data),
  
  // 获取模型列表
  models: () => api.get('/v1/guardrails/models').then(res => res.data),
};

// 仪表板API
export const dashboardApi = {
  // 获取统计数据
  getStats: (): Promise<DashboardStats> =>
    api.get('/api/v1/dashboard/stats').then(res => res.data),
  
  // 获取风险类别分布
  getCategoryDistribution: (params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<{ categories: { name: string; value: number }[] }> =>
    api.get('/api/v1/dashboard/category-distribution', { params }).then(res => res.data),
};

// 检测结果API
export const resultsApi = {
  // 获取检测结果列表
  getResults: (params?: {
    page?: number;
    per_page?: number;
    risk_level?: string;
    result_type?: string;
    category?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<PaginatedResponse<DetectionResult>> =>
    api.get('/api/v1/results', { params }).then(res => res.data),
  
  // 获取单个检测结果
  getResult: (id: number): Promise<DetectionResult> =>
    api.get(`/api/v1/results/${id}`).then(res => res.data),
};

// 配置API
export const configApi = {
  // 黑名单管理
  blacklist: {
    list: (): Promise<Blacklist[]> => api.get('/api/v1/config/blacklist').then(res => res.data),
    create: (data: Omit<Blacklist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.post('/api/v1/config/blacklist', data).then(res => res.data),
    update: (id: number, data: Omit<Blacklist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.put(`/api/v1/config/blacklist/${id}`, data).then(res => res.data),
    delete: (id: number): Promise<ApiResponse> =>
      api.delete(`/api/v1/config/blacklist/${id}`).then(res => res.data),
  },
  
  // 白名单管理
  whitelist: {
    list: (): Promise<Whitelist[]> => api.get('/api/v1/config/whitelist').then(res => res.data),
    create: (data: Omit<Whitelist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.post('/api/v1/config/whitelist', data).then(res => res.data),
    update: (id: number, data: Omit<Whitelist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.put(`/api/v1/config/whitelist/${id}`, data).then(res => res.data),
    delete: (id: number): Promise<ApiResponse> =>
      api.delete(`/api/v1/config/whitelist/${id}`).then(res => res.data),
  },
  
  // 代答模板管理
  responses: {
    list: (): Promise<ResponseTemplate[]> => api.get('/api/v1/config/responses').then(res => res.data),
    create: (data: Omit<ResponseTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.post('/api/v1/config/responses', data).then(res => res.data),
    update: (id: number, data: Omit<ResponseTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.put(`/api/v1/config/responses/${id}`, data).then(res => res.data),
    delete: (id: number): Promise<ApiResponse> =>
      api.delete(`/api/v1/config/responses/${id}`).then(res => res.data),
  },
  
  // 获取系统信息
  getSystemInfo: (): Promise<{ support_email: string | null; app_name: string; app_version: string }> =>
    api.get('/api/v1/config/system-info').then(res => res.data),
};

// 管理员API
export const adminApi = {
  // 获取管理员统计信息
  getAdminStats: (): Promise<{ 
    status: string; 
    data: { 
      total_users: number; 
      total_detections: number; 
      user_detection_counts: Array<{
        user_id: string;
        email: string;
        detection_count: number;
      }>
    } 
  }> =>
    api.get('/api/v1/admin/stats').then(res => res.data),
  
  // 获取所有用户列表
  getUsers: (): Promise<{ status: string; users: any[]; total: number }> =>
    api.get('/api/v1/admin/users').then(res => res.data),
  
  // 切换到指定用户视角
  switchToUser: (userId: string): Promise<{ 
    status: string; 
    message: string; 
    switch_session_token: string; 
    target_user: { id: string; email: string; api_key: string } 
  }> =>
    api.post(`/api/v1/admin/switch-user/${userId}`).then(res => res.data),
  
  // 退出用户切换
  exitSwitch: (): Promise<{ status: string; message: string }> =>
    api.post('/api/v1/admin/exit-switch').then(res => res.data),
  
  // 获取当前切换状态
  getCurrentSwitch: (): Promise<{
    is_switched: boolean;
    admin_user?: { id: string; email: string };
    target_user?: { id: string; email: string; api_key: string };
  }> =>
    api.get('/api/v1/admin/current-switch').then(res => res.data),
  
  // 用户管理
  createUser: (data: {
    email: string;
    password: string;
    is_active?: boolean;
    is_verified?: boolean;
    is_super_admin?: boolean;
  }): Promise<ApiResponse> =>
    api.post('/api/v1/admin/create-user', data).then(res => res.data),
  
  updateUser: (userId: string, data: {
    email?: string;
    is_active?: boolean;
    is_verified?: boolean;
    is_super_admin?: boolean;
  }): Promise<ApiResponse> =>
    api.put(`/api/v1/admin/users/${userId}`, data).then(res => res.data),
  
  deleteUser: (userId: string): Promise<ApiResponse> =>
    api.delete(`/api/v1/admin/users/${userId}`).then(res => res.data),
  
  resetUserApiKey: (userId: string): Promise<ApiResponse> =>
    api.post(`/api/v1/admin/users/${userId}/reset-api-key`).then(res => res.data),
  
  // 限速管理
  getRateLimits: (): Promise<{ status: string; data: any[]; total: number }> =>
    api.get('/api/v1/admin/rate-limits').then(res => res.data),
  
  setUserRateLimit: (data: {
    user_id: string;
    requests_per_second: number;
  }): Promise<{ status: string; message: string; data: any }> =>
    api.post('/api/v1/admin/rate-limits', data).then(res => res.data),
  
  removeUserRateLimit: (userId: string): Promise<{ status: string; message: string }> =>
    api.delete(`/api/v1/admin/rate-limits/${userId}`).then(res => res.data),
};

// 在线测试模型API - 使用代理模型配置
export const testModelsApi = {
  // 获取在线测试可用的代理模型列表
  getModels: () => api.get('/api/v1/test/models').then(res => res.data),
  
  // 更新在线测试模型选择
  updateSelection: (model_selections: Array<{ id: string; selected: boolean }>) => 
    api.post('/api/v1/test/models/selection', { model_selections }).then(res => res.data),
};

// 风险类型配置API
export const riskConfigApi = {
  // 获取风险配置
  get: () => api.get('/api/v1/config/risk-types').then(res => res.data),
  
  // 更新风险配置
  update: (config: {
    s1_enabled: boolean;
    s2_enabled: boolean;
    s3_enabled: boolean;
    s4_enabled: boolean;
    s5_enabled: boolean;
    s6_enabled: boolean;
    s7_enabled: boolean;
    s8_enabled: boolean;
    s9_enabled: boolean;
    s10_enabled: boolean;
    s11_enabled: boolean;
    s12_enabled: boolean;
  }) => api.put('/api/v1/config/risk-types', config).then(res => res.data),
  
  // 获取启用的风险类型
  getEnabled: () => api.get('/api/v1/config/risk-types/enabled').then(res => res.data),
  
  // 重置为默认配置
  reset: () => api.post('/api/v1/config/risk-types/reset').then(res => res.data),
};

// 便捷函数
export const getRiskConfig = () => riskConfigApi.get();
export const updateRiskConfig = (config: any) => riskConfigApi.update(config);

export default api;