-- 添加敏感度触发等级配置字段到 risk_type_config 表

-- 添加敏感度触发等级字段，默认值为 'low' 表示低敏感度就会触发检测命中
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS confidence_trigger_level VARCHAR(10) DEFAULT 'low';

-- 给现有记录设置默认值
UPDATE risk_type_config
SET confidence_trigger_level = 'low'
WHERE confidence_trigger_level IS NULL;