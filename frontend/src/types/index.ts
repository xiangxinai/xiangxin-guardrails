// API response type
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

// Guardrail detection related types
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
    data: {
      risk_level: string;
      categories: string[];
    };
  };
  overall_risk_level: string;
  suggest_action: string;
  suggest_answer?: string;
  score?: number;  // Detection probability score (0.0-1.0)
}

// Detection result type
export interface DetectionResult {
  id: number;
  request_id: string;
  content: string;
  suggest_action?: string;
  suggest_answer?: string;
  hit_keywords?: string;
  created_at: string;
  ip_address?: string;
  // Separated security and compliance detection results
  security_risk_level: string;
  security_categories: string[];
  compliance_risk_level: string;
  compliance_categories: string[];
  // Data security detection results
  data_risk_level: string;
  data_categories: string[];
  // Detection result related fields
  score?: number;  // Detection probability score (0.0-1.0)
  // 多模态相关字段
  has_image?: boolean;
  image_count?: number;
  image_paths?: string[];
  image_urls?: string[];  // Signed image access URLs
}

// Paginated response type
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Configuration related types
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

// Dashboard statistics type
export interface DashboardStats {
  total_requests: number;
  security_risks: number;
  compliance_risks: number;
  data_leaks: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  safe_count: number;
  risk_distribution: {
    'high_risk': number;
    'medium_risk': number;
    'low_risk': number;
    'no_risk': number;
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

// Knowledge base related types
export interface KnowledgeBase {
  id: number;
  category: string;
  name: string;
  description?: string;
  file_path: string;
  vector_file_path?: string;
  total_qa_pairs: number;
  is_active: boolean;
  is_global: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseFileInfo {
  original_file_exists: boolean;
  vector_file_exists: boolean;
  original_file_size: number;
  vector_file_size: number;
  total_qa_pairs: number;
}

export interface SimilarQuestionResult {
  questionid: string;
  question: string;
  answer: string;
  similarity_score: number;
  rank: number;
}

// Data security related types
export interface DataSecurityEntityType {
  id: string;
  entity_type: string;
  display_name: string;
  risk_level: string;  // Low, medium, high
  pattern: string;
  anonymization_method: string;
  anonymization_config: Record<string, any>;
  check_input: boolean;
  check_output: boolean;
  is_active: boolean;
  is_global: boolean;
  created_at: string;
  updated_at: string;
}

// Application management related types
export interface Application {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApplicationDetail extends Application {
  api_key_count: number;
}

export interface CreateApplicationRequest {
  name: string;
  description?: string;
  copy_from_application_id?: string;
}

export interface UpdateApplicationRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface CreateApplicationResponse {
  application: Application;
  first_api_key: string;
  message: string;
}

// API Key management related types
export interface APIKey {
  id: string;
  application_id: string;
  name?: string;
  key_prefix: string;  // Only show prefix like "sk-xxai-abc..."
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAPIKeyRequest {
  name?: string;
  expires_at?: string;  // ISO format
}

export interface UpdateAPIKeyRequest {
  name?: string;
  is_active?: boolean;
}

export interface CreateAPIKeyResponse {
  id: string;
  application_id: string;
  name?: string;
  api_key: string;  // Full API key, only shown once during creation
  key_prefix: string;
  is_active: boolean;
  expires_at?: string;
  created_at: string;
}