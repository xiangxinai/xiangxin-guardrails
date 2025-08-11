// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

// 护栏检测相关类型
export interface GuardrailRequest {
  model: string;
  messages: Message[];
  max_tokens?: number;
  temperature?: number;
}

export interface Message {
  role: 'user' | 'system' | 'assistant';
  content: string;
}

export interface GuardrailResponse {
  id: string;
  result: {
    compliance: {
      risk_level: string;
      categories: string[];
    };
    security: {
      risk_level: string;
      categories: string[];
    };
  };
  overall_risk_level: string;
  suggest_action: string;
  suggest_answer?: string;
}

// 检测结果类型
export interface DetectionResult {
  id: number;
  request_id: string;
  content: string;
  suggest_action?: string;
  suggest_answer?: string;
  hit_keywords?: string;
  created_at: string;
  ip_address?: string;
  // 分离的安全和合规检测结果
  security_risk_level: string;
  security_categories: string[];
  compliance_risk_level: string;
  compliance_categories: string[];
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// 配置相关类型
export interface Blacklist {
  id: number;
  name: string;
  keywords: string[];
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Whitelist {
  id: number;
  name: string;
  keywords: string[];
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResponseTemplate {
  id: number;
  category: string;
  risk_level: string;
  template_content: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 仪表板统计类型
export interface DashboardStats {
  total_requests: number;
  security_risks: number;
  compliance_risks: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  safe_count: number;
  risk_distribution: {
    '高风险': number;
    '中风险': number;
    '低风险': number;
    '无风险': number;
  };
  daily_trends: DailyTrend[];
}

export interface DailyTrend {
  date: string;
  total: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  safe: number;
}