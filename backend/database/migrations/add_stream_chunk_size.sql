-- 添加流式检测配置字段
-- 为代理模型配置表添加stream_chunk_size字段

ALTER TABLE proxy_model_configs ADD COLUMN IF NOT EXISTS stream_chunk_size INTEGER DEFAULT 5;

-- 添加注释
COMMENT ON COLUMN proxy_model_configs.stream_chunk_size IS '流式检测间隔，每N个chunk检测一次，默认5。不同上游模型可配置不同值。';

-- 为现有记录设置合理的默认值
UPDATE proxy_model_configs SET stream_chunk_size = 5 WHERE stream_chunk_size IS NULL;

-- 设置约束：stream_chunk_size应该在1-50之间
ALTER TABLE proxy_model_configs ADD CONSTRAINT check_stream_chunk_size_range 
    CHECK (stream_chunk_size >= 1 AND stream_chunk_size <= 50);