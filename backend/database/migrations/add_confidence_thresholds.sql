-- 添加风险类型敏感度阈值字段到 risk_type_config 表

-- 添加 S1-S12 敏感度阈值字段，默认值为 0.90 (中档90%)
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s1_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s2_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s3_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s4_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s5_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s6_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s7_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s8_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s9_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s10_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s11_confidence_threshold FLOAT DEFAULT 0.90;
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS s12_confidence_threshold FLOAT DEFAULT 0.90;

-- 给现有记录设置默认值
UPDATE risk_type_config
SET s1_confidence_threshold = 0.90,
    s2_confidence_threshold = 0.90,
    s3_confidence_threshold = 0.90,
    s4_confidence_threshold = 0.90,
    s5_confidence_threshold = 0.90,
    s6_confidence_threshold = 0.90,
    s7_confidence_threshold = 0.90,
    s8_confidence_threshold = 0.90,
    s9_confidence_threshold = 0.90,
    s10_confidence_threshold = 0.90,
    s11_confidence_threshold = 0.90,
    s12_confidence_threshold = 0.90
WHERE s1_confidence_threshold IS NULL;