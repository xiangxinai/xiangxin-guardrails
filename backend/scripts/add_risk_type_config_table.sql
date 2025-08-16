-- 添加风险类型配置表
-- 此脚本为现有数据库添加风险类型开关功能

-- 创建风险类型配置表
CREATE TABLE IF NOT EXISTS risk_type_config (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,
    
    -- S1-S12风险类型开关配置
    s1_enabled BOOLEAN DEFAULT TRUE,  -- 一般政治话题
    s2_enabled BOOLEAN DEFAULT TRUE,  -- 敏感政治话题
    s3_enabled BOOLEAN DEFAULT TRUE,  -- 损害国家形象
    s4_enabled BOOLEAN DEFAULT TRUE,  -- 伤害未成年人
    s5_enabled BOOLEAN DEFAULT TRUE,  -- 暴力犯罪
    s6_enabled BOOLEAN DEFAULT TRUE,  -- 违法犯罪
    s7_enabled BOOLEAN DEFAULT TRUE,  -- 色情
    s8_enabled BOOLEAN DEFAULT TRUE,  -- 歧视内容
    s9_enabled BOOLEAN DEFAULT TRUE,  -- 提示词攻击
    s10_enabled BOOLEAN DEFAULT TRUE, -- 辱骂
    s11_enabled BOOLEAN DEFAULT TRUE, -- 侵犯个人隐私
    s12_enabled BOOLEAN DEFAULT TRUE, -- 商业违法违规
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_risk_config_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_risk_type_config_user_id ON risk_type_config(user_id);

-- 添加更新时间触发器
CREATE OR REPLACE FUNCTION update_risk_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_risk_config_updated_at ON risk_type_config;
CREATE TRIGGER trigger_update_risk_config_updated_at
    BEFORE UPDATE ON risk_type_config
    FOR EACH ROW
    EXECUTE FUNCTION update_risk_config_updated_at();

-- 为现有用户创建默认配置（可选 - 用户首次使用时会自动创建）
-- INSERT INTO risk_type_config (user_id)
-- SELECT id FROM users
-- WHERE id NOT IN (SELECT user_id FROM risk_type_config);

COMMENT ON TABLE risk_type_config IS '用户风险类型开关配置表';
COMMENT ON COLUMN risk_type_config.user_id IS '用户ID，与users表关联';
COMMENT ON COLUMN risk_type_config.s1_enabled IS 'S1-一般政治话题是否启用检测';
COMMENT ON COLUMN risk_type_config.s2_enabled IS 'S2-敏感政治话题是否启用检测';
COMMENT ON COLUMN risk_type_config.s3_enabled IS 'S3-损害国家形象是否启用检测';
COMMENT ON COLUMN risk_type_config.s4_enabled IS 'S4-伤害未成年人是否启用检测';
COMMENT ON COLUMN risk_type_config.s5_enabled IS 'S5-暴力犯罪是否启用检测';
COMMENT ON COLUMN risk_type_config.s6_enabled IS 'S6-违法犯罪是否启用检测';
COMMENT ON COLUMN risk_type_config.s7_enabled IS 'S7-色情是否启用检测';
COMMENT ON COLUMN risk_type_config.s8_enabled IS 'S8-歧视内容是否启用检测';
COMMENT ON COLUMN risk_type_config.s9_enabled IS 'S9-提示词攻击是否启用检测';
COMMENT ON COLUMN risk_type_config.s10_enabled IS 'S10-辱骂是否启用检测';
COMMENT ON COLUMN risk_type_config.s11_enabled IS 'S11-侵犯个人隐私是否启用检测';
COMMENT ON COLUMN risk_type_config.s12_enabled IS 'S12-商业违法违规是否启用检测';