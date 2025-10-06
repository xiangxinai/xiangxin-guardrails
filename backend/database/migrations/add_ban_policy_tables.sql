-- 封禁策略表
CREATE TABLE IF NOT EXISTS ban_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    risk_level VARCHAR(20) NOT NULL DEFAULT '高风险',  -- 高风险/中风险/低风险
    trigger_count INTEGER NOT NULL DEFAULT 3,  -- 触发次数阈值
    time_window_minutes INTEGER NOT NULL DEFAULT 10,  -- 时间窗口（分钟）
    ban_duration_minutes INTEGER NOT NULL DEFAULT 60,  -- 封禁时长（分钟）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_risk_level CHECK (risk_level IN ('高风险', '中风险', '低风险')),
    CONSTRAINT check_trigger_count CHECK (trigger_count >= 1 AND trigger_count <= 100),
    CONSTRAINT check_time_window CHECK (time_window_minutes >= 1 AND time_window_minutes <= 1440),
    CONSTRAINT check_ban_duration CHECK (ban_duration_minutes >= 1 AND ban_duration_minutes <= 10080)
);

-- 用户封禁记录表
CREATE TABLE IF NOT EXISTS user_ban_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,  -- xxai_app_user_id
    banned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ban_until TIMESTAMP WITH TIME ZONE NOT NULL,  -- 封禁到什么时候
    trigger_count INTEGER NOT NULL,  -- 触发了多少次
    risk_level VARCHAR(20) NOT NULL,  -- 触发的风险等级
    reason TEXT,  -- 封禁原因描述
    is_active BOOLEAN NOT NULL DEFAULT TRUE,  -- 是否仍在封禁期
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户风险触发历史表（用于统计时间窗口内的触发次数）
CREATE TABLE IF NOT EXISTS user_risk_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,  -- xxai_app_user_id
    detection_result_id VARCHAR(64),  -- 关联 detection_results.request_id（可选）
    risk_level VARCHAR(20) NOT NULL,  -- 触发的风险等级
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ban_policies_tenant ON ban_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_ban_records_tenant_user ON user_ban_records(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_user_ban_records_active ON user_ban_records(tenant_id, user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_risk_triggers_tenant_user_time ON user_risk_triggers(tenant_id, user_id, triggered_at);

-- 为每个租户创建默认封禁策略（禁用状态）
INSERT INTO ban_policies (tenant_id, enabled, risk_level, trigger_count, time_window_minutes, ban_duration_minutes)
SELECT id, FALSE, '高风险', 3, 10, 60
FROM tenants
WHERE NOT EXISTS (
    SELECT 1 FROM ban_policies WHERE ban_policies.tenant_id = tenants.id
);

-- 更新 updated_at 触发器
CREATE OR REPLACE FUNCTION update_ban_policies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ban_policies_updated_at
    BEFORE UPDATE ON ban_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_ban_policies_updated_at();

CREATE OR REPLACE FUNCTION update_user_ban_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_ban_records_updated_at
    BEFORE UPDATE ON user_ban_records
    FOR EACH ROW
    EXECUTE FUNCTION update_user_ban_records_updated_at();

-- 自动清理过期的封禁记录（将 is_active 设为 false）
CREATE OR REPLACE FUNCTION deactivate_expired_bans()
RETURNS void AS $$
BEGIN
    UPDATE user_ban_records
    SET is_active = FALSE
    WHERE is_active = TRUE
    AND ban_until < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- 自动清理旧的风险触发记录（保留最近7天）
CREATE OR REPLACE FUNCTION cleanup_old_risk_triggers()
RETURNS void AS $$
BEGIN
    DELETE FROM user_risk_triggers
    WHERE triggered_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE ban_policies IS '封禁策略配置表';
COMMENT ON TABLE user_ban_records IS '用户封禁记录表';
COMMENT ON TABLE user_risk_triggers IS '用户风险触发历史表';
