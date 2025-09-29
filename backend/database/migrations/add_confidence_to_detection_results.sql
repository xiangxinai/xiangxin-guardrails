-- 添加敏感度相关字段到 detection_results 表

-- 添加敏感度等级字段
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(10);

-- 添加敏感度分数字段
ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS confidence_score FLOAT;

-- 为现有记录设置默认值（可选，因为字段允许为NULL）
-- UPDATE detection_results SET confidence_level = NULL, confidence_score = NULL WHERE confidence_level IS NULL;