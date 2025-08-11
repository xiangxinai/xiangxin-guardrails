-- 象信AI安全护栏数据库初始化脚本
-- 创建必要的扩展和基础表结构

-- 创建UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- 检测结果表
CREATE TABLE IF NOT EXISTS detection_results (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    request_id VARCHAR(255),
    content TEXT NOT NULL,
    security_risk_level VARCHAR(10) DEFAULT '无风险',
    compliance_risk_level VARCHAR(10) DEFAULT '无风险',
    overall_risk_level VARCHAR(10) DEFAULT '无风险',
    security_categories JSONB DEFAULT '[]',
    compliance_categories JSONB DEFAULT '[]',
    suggest_action VARCHAR(10) DEFAULT '通过',
    suggest_answer TEXT,
    response_time INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 黑名单表
CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    keywords TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 白名单表
CREATE TABLE IF NOT EXISTS whitelist (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    keywords TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 代答模板表
CREATE TABLE IF NOT EXISTS response_templates (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    risk_level VARCHAR(10) NOT NULL,
    category VARCHAR(255),
    template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户限速配置表
CREATE TABLE IF NOT EXISTS user_rate_limits (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) UNIQUE NOT NULL,
    requests_per_second INTEGER DEFAULT 1 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_detection_results_user_id ON detection_results(user_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_created_at ON detection_results(created_at);
CREATE INDEX IF NOT EXISTS idx_detection_results_risk_level ON detection_results(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_blacklist_user_id ON blacklist(user_id);
CREATE INDEX IF NOT EXISTS idx_whitelist_user_id ON whitelist(user_id);
CREATE INDEX IF NOT EXISTS idx_response_templates_user_id ON response_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rate_limits_user_id ON user_rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_rate_limits_is_active ON user_rate_limits(is_active);

-- 插入默认管理员用户（密码: admin123456）
INSERT INTO users (email, hashed_password, is_admin, is_verified) 
VALUES ('admin@xiangxinai.cn', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlDBqUJwgN3k6Nm', true, true)
ON CONFLICT (email) DO NOTHING;

-- 插入默认代答模板
INSERT INTO response_templates (user_id, name, risk_level, template, is_active)
VALUES 
    (null, '高风险默认回复', '高风险', '很抱歉，我无法回答您的问题。如果您有其他问题，我很乐意为您提供帮助。', true),
    (null, '中风险默认回复', '中风险', '抱歉，我无法提供相关信息。让我们换个话题吧，我可以为您介绍其他有趣的内容。', true),
    (null, '低风险默认回复', '低风险', '让我们保持友好的交流环境，我可以为您提供其他有用的信息。', true)
ON CONFLICT DO NOTHING;

-- 更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blacklist_updated_at BEFORE UPDATE ON blacklist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_whitelist_updated_at BEFORE UPDATE ON whitelist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_response_templates_updated_at BEFORE UPDATE ON response_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_rate_limits_updated_at BEFORE UPDATE ON user_rate_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();