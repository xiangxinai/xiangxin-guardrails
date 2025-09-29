-- 为代理模型配置表添加敏感度触发等级字段
-- 用于配置代理模式下各个模型的敏感度阻断阈值

ALTER TABLE proxy_model_configs ADD COLUMN IF NOT EXISTS confidence_trigger_level VARCHAR(10) DEFAULT 'medium';

-- 添加注释
COMMENT ON COLUMN proxy_model_configs.confidence_trigger_level IS '敏感度触发等级：high、medium、low，决定什么敏感度等级会触发安全网关的阻断';

-- 为现有记录设置默认值
UPDATE proxy_model_configs SET confidence_trigger_level = 'medium' WHERE confidence_trigger_level IS NULL;

-- 添加检查约束，确保只能是有效的敏感度等级
ALTER TABLE proxy_model_configs ADD CONSTRAINT check_confidence_trigger_level_values
    CHECK (confidence_trigger_level IN ('high', 'medium', 'low'));