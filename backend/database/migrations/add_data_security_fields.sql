-- 添加数据安全检测字段到detection_results表
-- 创建时间: 2025-10-03

-- 添加数据安全检测结果字段
ALTER TABLE detection_results
ADD COLUMN IF NOT EXISTS data_risk_level VARCHAR(10) DEFAULT '无风险',
ADD COLUMN IF NOT EXISTS data_categories JSONB DEFAULT '[]'::jsonb;

-- 添加注释
COMMENT ON COLUMN detection_results.data_risk_level IS '数据泄漏风险等级';
COMMENT ON COLUMN detection_results.data_categories IS '数据泄漏类别';
