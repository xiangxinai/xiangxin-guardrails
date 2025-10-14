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
  ResponseTemplate,
  KnowledgeBase,
  KnowledgeBaseFileInfo,
  SimilarQuestionResult
} from '../types';

// Create axios instance - Use API URL from environment variables
const getBaseURL = () => {
  // Use API URL from environment variables
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Production and Docker environments use relative path, through nginx proxy
  return '';
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 300000, // Increase to 5 minutes timeout
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Skip authentication routes, do not add Authorization header
    if (config.url && config.url.includes('/auth/')) {
      return config;
    }
    
    // Add authentication header - Use JWT token first, then use API key
    const authToken = localStorage.getItem('auth_token');
    const apiToken = localStorage.getItem('api_token');

    const token = authToken || apiToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add tenant switch session token
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

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const url: string | undefined = error.config?.url;
    
    // Silent handling of certain non-critical 401 (e.g. when checking switch status is not ready)
    if (status === 401 && url && url.includes('/admin/current-switch')) {
      return Promise.reject(error);
    }
    
    // For 429 rate limit errors, let business logic handle it, do not show a popup globally
    if (status === 429) {
      return Promise.reject(error);
    }
    
    const errorMessage = error.response?.data?.detail || error.message || 'Request failed';
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

// Guardrails API
export const guardrailsApi = {
  // Check content
  check: (data: GuardrailRequest): Promise<GuardrailResponse> =>
    api.post('/v1/guardrails', data).then(res => res.data),
  
  // Health check
  health: () => api.get('/v1/guardrails/health').then(res => res.data),
  
  // Get model list
  models: () => api.get('/v1/guardrails/models').then(res => res.data),
};

// Dashboard API
export const dashboardApi = {
  // Get stats data
  getStats: (): Promise<DashboardStats> =>
    api.get('/api/v1/dashboard/stats').then(res => res.data),
  
  // Get risk category distribution
  getCategoryDistribution: (params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<{ categories: { name: string; value: number }[] }> =>
    api.get('/api/v1/dashboard/category-distribution', { params }).then(res => res.data),
};

// Detection results API
export const resultsApi = {
  // Get detection results list
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
  
  // Get single detection result
  getResult: (id: number): Promise<DetectionResult> =>
    api.get(`/api/v1/results/${id}`).then(res => res.data),
};

// Config API
export const configApi = {
  // Blacklist management
  blacklist: {
    list: (applicationId?: string): Promise<Blacklist[]> => {
      const params = applicationId ? { application_id: applicationId } : {};
      return api.get('/api/v1/config/blacklist', { params }).then(res => res.data);
    },
    create: (data: Omit<Blacklist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.post('/api/v1/config/blacklist', data).then(res => res.data),
    update: (id: number, data: Omit<Blacklist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.put(`/api/v1/config/blacklist/${id}`, data).then(res => res.data),
    delete: (id: number): Promise<ApiResponse> =>
      api.delete(`/api/v1/config/blacklist/${id}`).then(res => res.data),
  },

  // Whitelist management
  whitelist: {
    list: (applicationId?: string): Promise<Whitelist[]> => {
      const params = applicationId ? { application_id: applicationId } : {};
      return api.get('/api/v1/config/whitelist', { params }).then(res => res.data);
    },
    create: (data: Omit<Whitelist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.post('/api/v1/config/whitelist', data).then(res => res.data),
    update: (id: number, data: Omit<Whitelist, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.put(`/api/v1/config/whitelist/${id}`, data).then(res => res.data),
    delete: (id: number): Promise<ApiResponse> =>
      api.delete(`/api/v1/config/whitelist/${id}`).then(res => res.data),
  },
  
  // Response template management
  responses: {
    list: (applicationId?: string): Promise<ResponseTemplate[]> => {
      const params = applicationId ? { application_id: applicationId } : {};
      return api.get('/api/v1/config/responses', { params }).then(res => res.data);
    },
    create: (data: Omit<ResponseTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.post('/api/v1/config/responses', data).then(res => res.data),
    update: (id: number, data: Omit<ResponseTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse> =>
      api.put(`/api/v1/config/responses/${id}`, data).then(res => res.data),
    delete: (id: number): Promise<ApiResponse> =>
      api.delete(`/api/v1/config/responses/${id}`).then(res => res.data),
  },
  
  // Get system info
  getSystemInfo: (): Promise<{ support_email: string | null; app_name: string; app_version: string }> =>
    api.get('/api/v1/config/system-info').then(res => res.data),

  // Ban policy management
  banPolicy: {
    // Get ban policy
    get: (): Promise<any> => api.get('/api/v1/ban-policy').then(res => res.data),

    // Update ban policy
    update: (data: {
      enabled: boolean;
      risk_level: string;
      trigger_count: number;
      time_window_minutes: number;
      ban_duration_minutes: number;
    }): Promise<any> => api.put('/api/v1/ban-policy', data).then(res => res.data),

    // Get banned users list
    getBannedUsers: (skip?: number, limit?: number): Promise<{ users: any[] }> =>
      api.get('/api/v1/ban-policy/banned-users', { params: { skip, limit } }).then(res => res.data),

    // Unban user
    unbanUser: (userId: string): Promise<any> =>
      api.post('/api/v1/ban-policy/unban', { user_id: userId }).then(res => res.data),

    // Get user risk history
    getUserHistory: (userId: string, days?: number): Promise<{ history: any[] }> =>
      api.get(`/api/v1/ban-policy/user-history/${userId}`, { params: { days } }).then(res => res.data),

    // Check user ban status
    checkUserStatus: (userId: string): Promise<any> =>
      api.get(`/api/v1/ban-policy/check-status/${userId}`).then(res => res.data),
  },
};

// Admin API
export const adminApi = {
  // Get admin stats info
  getAdminStats: (): Promise<{
    status: string;
    data: {
      total_users: number;
      total_detections: number;
      user_detection_counts: Array<{
        tenant_id: string;
        email: string;
        detection_count: number;
      }>
    }
  }> =>
    api.get('/api/v1/admin/stats').then(res => res.data),

  // Get all tenants list
  getUsers: (): Promise<{ status: string; users: any[]; total: number }> =>
    api.get('/api/v1/admin/users').then(res => res.data),

  // Switch to specified tenant perspective
  switchToUser: (tenantId: string): Promise<{
    status: string;
    message: string;
    switch_session_token: string;
    target_user: { id: string; email: string; api_key: string }
  }> =>
    api.post(`/api/v1/admin/switch-user/${tenantId}`).then(res => res.data),

  // Exit tenant switch
  exitSwitch: (): Promise<{ status: string; message: string }> =>
    api.post('/api/v1/admin/exit-switch').then(res => res.data),

  // Get current switch status
  getCurrentSwitch: (): Promise<{
    is_switched: boolean;
    admin_user?: { id: string; email: string };
    target_user?: { id: string; email: string; api_key: string };
  }> =>
    api.get('/api/v1/admin/current-switch').then(res => res.data),

  // Tenant management
  createUser: (data: {
    email: string;
    password: string;
    is_active?: boolean;
    is_verified?: boolean;
    is_super_admin?: boolean;
  }): Promise<ApiResponse> =>
    api.post('/api/v1/admin/create-user', data).then(res => res.data),

  updateUser: (tenantId: string, data: {
    email?: string;
    is_active?: boolean;
    is_verified?: boolean;
    is_super_admin?: boolean;
  }): Promise<ApiResponse> =>
    api.put(`/api/v1/admin/users/${tenantId}`, data).then(res => res.data),

  deleteUser: (tenantId: string): Promise<ApiResponse> =>
    api.delete(`/api/v1/admin/users/${tenantId}`).then(res => res.data),

  resetUserApiKey: (tenantId: string): Promise<ApiResponse> =>
    api.post(`/api/v1/admin/users/${tenantId}/reset-api-key`).then(res => res.data),

  // Tenant rate limit management
  getRateLimits: (params?: { skip?: number; limit?: number; search?: string }): Promise<{ status: string; data: any[]; total: number }> =>
    api.get('/api/v1/admin/rate-limits', { params }).then(res => res.data),

  setUserRateLimit: (data: {
    tenant_id: string;
    requests_per_second: number;
  }): Promise<{ status: string; message: string; data: any }> =>
    api.post('/api/v1/admin/rate-limits', data).then(res => res.data),

  removeUserRateLimit: (tenantId: string): Promise<{ status: string; message: string }> =>
    api.delete(`/api/v1/admin/rate-limits/${tenantId}`).then(res => res.data),
};

// Online test model API - Use proxy model configuration
export const testModelsApi = {
  // Get online test available proxy model list
  getModels: () => api.get('/api/v1/test/models').then(res => res.data),
  
  // Update online test model selection
  updateSelection: (model_selections: Array<{ id: string; selected: boolean }>) => 
    api.post('/api/v1/test/models/selection', { model_selections }).then(res => res.data),
};

// Risk type configuration API
export const riskConfigApi = {
  // Get risk configuration (application-scoped or tenant-scoped for backward compatibility)
  get: (applicationId?: string) => {
    const params = applicationId ? { application_id: applicationId } : {};
    return api.get('/api/v1/config/risk-types', { params }).then(res => res.data);
  },

  // Update risk configuration (application-scoped or tenant-scoped for backward compatibility)
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
  }, applicationId?: string) => {
    const params = applicationId ? { application_id: applicationId } : {};
    return api.put('/api/v1/config/risk-types', config, { params }).then(res => res.data);
  },

  // Get enabled risk types
  getEnabled: () => api.get('/api/v1/config/risk-types/enabled').then(res => res.data),

  // Reset to default configuration
  reset: () => api.post('/api/v1/config/risk-types/reset').then(res => res.data),
};

// Sensitivity threshold configuration API
export const sensitivityThresholdApi = {
  // Get sensitivity threshold configuration (application-scoped or tenant-scoped for backward compatibility)
  get: (applicationId?: string) => {
    const params = applicationId ? { application_id: applicationId } : {};
    return api.get('/api/v1/config/sensitivity-thresholds', { params }).then(res => res.data);
  },

  // Update sensitivity threshold configuration (application-scoped or tenant-scoped for backward compatibility)
  update: (config: {
    high_sensitivity_threshold: number;
    medium_sensitivity_threshold: number;
    low_sensitivity_threshold: number;
    sensitivity_trigger_level: string;
  }, applicationId?: string) => {
    const params = applicationId ? { application_id: applicationId } : {};
    return api.put('/api/v1/config/sensitivity-thresholds', config, { params }).then(res => res.data);
  },

  // Reset to default configuration
  reset: () => api.post('/api/v1/config/sensitivity-thresholds/reset').then(res => res.data),
};

// Proxy model configuration API
export const proxyModelsApi = {
  // Get proxy model list
  list: (): Promise<{ success: boolean; data: any[] }> =>
    api.get('/api/v1/proxy/models').then(res => res.data),
  
  // Get proxy model detail
  get: (id: string): Promise<{ success: boolean; data: any }> =>
    api.get(`/api/v1/proxy/models/${id}`).then(res => res.data),
  
  // Create proxy model configuration
  create: (data: {
    config_name: string;
    api_base_url: string;
    api_key: string;
    model_name: string;
    enabled?: boolean;
    block_on_input_risk?: boolean;
    block_on_output_risk?: boolean;
    enable_reasoning_detection?: boolean;
    stream_chunk_size?: number;
  }): Promise<{ success: boolean; message: string; data?: any }> =>
    api.post('/api/v1/proxy/models', data).then(res => res.data),
  
  // Update proxy model configuration
  update: (id: string, data: {
    config_name?: string;
    api_base_url?: string;
    api_key?: string;
    model_name?: string;
    enabled?: boolean;
    block_on_input_risk?: boolean;
    block_on_output_risk?: boolean;
    enable_reasoning_detection?: boolean;
    stream_chunk_size?: number;
  }): Promise<{ success: boolean; message: string }> =>
    api.put(`/api/v1/proxy/models/${id}`, data).then(res => res.data),
  
  // Delete proxy model configuration
  delete: (id: string): Promise<{ success: boolean; message: string }> =>
    api.delete(`/api/v1/proxy/models/${id}`).then(res => res.data),
  
  // Test proxy model configuration
  test: (id: string): Promise<{ success: boolean; message: string; data?: any }> =>
    api.post(`/api/v1/proxy/models/${id}/test`).then(res => res.data),
};

// Knowledge base management API
export const knowledgeBaseApi = {
  // Get knowledge base list
  list: (category?: string): Promise<KnowledgeBase[]> => {
    const url = category ? `/api/v1/config/knowledge-bases?category=${category}` : '/api/v1/config/knowledge-bases';
    return api.get(url).then(res => res.data);
  },

  // Create knowledge base
  create: (data: FormData): Promise<{ success: boolean; message: string }> =>
    api.post('/api/v1/config/knowledge-bases', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => res.data),

  // Update knowledge base
  update: (id: number, data: {
    category: string;
    name: string;
    description?: string;
    is_active: boolean;
  }): Promise<{ success: boolean; message: string }> =>
    api.put(`/api/v1/config/knowledge-bases/${id}`, data).then(res => res.data),

  // Delete knowledge base
  delete: (id: number): Promise<{ success: boolean; message: string }> =>
    api.delete(`/api/v1/config/knowledge-bases/${id}`).then(res => res.data),

  // Replace knowledge base file
  replaceFile: (id: number, file: File): Promise<{ success: boolean; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/config/knowledge-bases/${id}/replace-file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => res.data);
  },

  // Get knowledge base file info
  getInfo: (id: number): Promise<KnowledgeBaseFileInfo> =>
    api.get(`/api/v1/config/knowledge-bases/${id}/info`).then(res => res.data),

  // Search similar questions
  search: (id: number, query: string, topK?: number): Promise<SimilarQuestionResult[]> => {
    const params = new URLSearchParams({ query });
    if (topK) params.append('top_k', topK.toString());
    return api.post(`/api/v1/config/knowledge-bases/${id}/search?${params.toString()}`).then(res => res.data);
  },

  // Get knowledge base by category
  getByCategory: (category: string): Promise<KnowledgeBase[]> =>
    api.get(`/api/v1/config/categories/${category}/knowledge-bases`).then(res => res.data),
};

// Data security API
export const dataSecurityApi = {
  // Get all sensitive data types
  getEntityTypes: (): Promise<{ items: any[] }> =>
    api.get('/api/v1/config/data-security/entity-types').then(res => res.data),

  // Get single sensitive data type
  getEntityType: (id: string): Promise<any> =>
    api.get(`/api/v1/config/data-security/entity-types/${id}`).then(res => res.data),

  // Create sensitive data type
  createEntityType: (data: any): Promise<any> =>
    api.post('/api/v1/config/data-security/entity-types', data).then(res => res.data),

  // Update sensitive data type
  updateEntityType: (id: string, data: any): Promise<any> =>
    api.put(`/api/v1/config/data-security/entity-types/${id}`, data).then(res => res.data),

  // Delete sensitive data type
  deleteEntityType: (id: string): Promise<any> =>
    api.delete(`/api/v1/config/data-security/entity-types/${id}`).then(res => res.data),

  // Create global sensitive data type (only admin)
  createGlobalEntityType: (data: any): Promise<any> =>
    api.post('/api/v1/config/data-security/global-entity-types', data).then(res => res.data),

  // Get detection results list
  getDetectionResults: (limit: number, offset: number): Promise<{ items: any[]; total: number }> =>
    api.get(`/api/v1/results?per_page=${limit}&page=${Math.floor(offset / limit) + 1}`).then(res => res.data),

  // Get single detection result detail
  getDetectionResult: (requestId: string): Promise<any> =>
    api.get(`/api/v1/results/${requestId}`).then(res => res.data),
};

// Application management API
export const applicationApi = {
  // Get all applications
  list: (): Promise<Application[]> =>
    api.get('/api/v1/applications').then(res => res.data),

  // Get application detail
  get: (id: string): Promise<ApplicationDetail> =>
    api.get(`/api/v1/applications/${id}`).then(res => res.data),

  // Create application
  create: (data: CreateApplicationRequest): Promise<CreateApplicationResponse> =>
    api.post('/api/v1/applications', data).then(res => res.data),

  // Update application
  update: (id: string, data: UpdateApplicationRequest): Promise<Application> =>
    api.put(`/api/v1/applications/${id}`, data).then(res => res.data),

  // Delete application
  delete: (id: string): Promise<ApiResponse> =>
    api.delete(`/api/v1/applications/${id}`).then(res => res.data),
};

// API Key management API
export const apiKeyApi = {
  // Get all API keys for an application
  list: (applicationId: string): Promise<APIKey[]> =>
    api.get(`/api/v1/applications/${applicationId}/api-keys`).then(res => res.data),

  // Create API key
  create: (applicationId: string, data: CreateAPIKeyRequest): Promise<CreateAPIKeyResponse> =>
    api.post(`/api/v1/applications/${applicationId}/api-keys`, data).then(res => res.data),

  // Update API key
  update: (applicationId: string, keyId: string, data: UpdateAPIKeyRequest): Promise<APIKey> =>
    api.patch(`/api/v1/applications/${applicationId}/api-keys/${keyId}`, data).then(res => res.data),

  // Delete API key
  delete: (applicationId: string, keyId: string): Promise<ApiResponse> =>
    api.delete(`/api/v1/applications/${applicationId}/api-keys/${keyId}`).then(res => res.data),
};

// Convenient functions
export const getRiskConfig = (applicationId?: string) => riskConfigApi.get(applicationId);
export const updateRiskConfig = (config: any, applicationId?: string) => riskConfigApi.update(config, applicationId);

export default api;