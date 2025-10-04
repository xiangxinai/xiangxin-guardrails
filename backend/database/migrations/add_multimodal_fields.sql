-- 添加多模态相关字段到detection_results表
-- 创建时间: 2025-10-03

-- 添加多模态字段
ALTER TABLE detection_results
ADD COLUMN IF NOT EXISTS has_image BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS image_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS image_paths JSONB DEFAULT '[]'::jsonb;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_detection_results_has_image ON detection_results(has_image);

-- 添加注释
COMMENT ON COLUMN detection_results.has_image IS '是否包含图片';
COMMENT ON COLUMN detection_results.image_count IS '图片数量';
COMMENT ON COLUMN detection_results.image_paths IS '保存的图片文件路径列表';
