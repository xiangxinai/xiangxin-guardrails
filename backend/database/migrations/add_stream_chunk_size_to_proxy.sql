-- 为代理模型配置表添加stream_chunk_size字段
ALTER TABLE proxy_model_configs
ADD COLUMN stream_chunk_size INTEGER DEFAULT 50;

-- 更新注释
COMMENT ON COLUMN proxy_model_configs.stream_chunk_size IS '流式检测间隔，每N个chunk检测一次，默认50';