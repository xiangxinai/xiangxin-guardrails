-- 添加数据安全功能相关表
-- 创建时间: 2025-10-02

-- 数据安全实体类型配置表
CREATE TABLE IF NOT EXISTS data_security_entity_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    recognition_method VARCHAR(20) NOT NULL,
    recognition_config JSONB NOT NULL,
    anonymization_method VARCHAR(20) DEFAULT 'replace',
    anonymization_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    is_global BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_data_security_entity_types_user_id ON data_security_entity_types(user_id);
CREATE INDEX IF NOT EXISTS idx_data_security_entity_types_entity_type ON data_security_entity_types(entity_type);
CREATE INDEX IF NOT EXISTS idx_data_security_entity_types_category ON data_security_entity_types(category);
CREATE INDEX IF NOT EXISTS idx_data_security_entity_types_is_active ON data_security_entity_types(is_active);
CREATE INDEX IF NOT EXISTS idx_data_security_entity_types_is_global ON data_security_entity_types(is_global);

-- 数据安全检测结果表
CREATE TABLE IF NOT EXISTS data_security_detection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id VARCHAR(64) UNIQUE NOT NULL,
    original_text TEXT NOT NULL,
    anonymized_text TEXT NOT NULL,
    detected_entities JSONB NOT NULL,
    entity_count INTEGER DEFAULT 0,
    categories_detected JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_data_security_detection_results_user_id ON data_security_detection_results(user_id);
CREATE INDEX IF NOT EXISTS idx_data_security_detection_results_request_id ON data_security_detection_results(request_id);
CREATE INDEX IF NOT EXISTS idx_data_security_detection_results_created_at ON data_security_detection_results(created_at);

-- 添加注释
COMMENT ON TABLE data_security_entity_types IS '数据安全实体类型配置表';
COMMENT ON TABLE data_security_detection_results IS '数据安全检测结果表';
