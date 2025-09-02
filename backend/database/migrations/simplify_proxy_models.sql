-- 极简化代理模型配置 - 只保留核心功能
-- 删除所有高级参数配置字段
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS max_tokens;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS temperature;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS top_p;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS frequency_penalty;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS presence_penalty;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS timeout;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS stream_chunk_size;

-- 删除旧的检测配置字段
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS enable_input_detection;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS enable_output_detection;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS enable_thinking_detection;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS thinking_content_field;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS extra_body;
ALTER TABLE proxy_model_configs DROP COLUMN IF EXISTS extra_parameters;

-- 保留的核心字段（极简设计）：
-- - config_name: 配置名称
-- - api_base_url: 上游API地址  
-- - api_key_encrypted: 加密的API密钥
-- - model_name: 实际模型名称
-- - enabled: 是否启用

-- 安全配置（极简设计）
ALTER TABLE proxy_model_configs ADD COLUMN IF NOT EXISTS block_on_input_risk BOOLEAN DEFAULT FALSE;
ALTER TABLE proxy_model_configs ADD COLUMN IF NOT EXISTS block_on_output_risk BOOLEAN DEFAULT FALSE;
ALTER TABLE proxy_model_configs ADD COLUMN IF NOT EXISTS enable_reasoning_detection BOOLEAN DEFAULT TRUE;

-- 添加注释
COMMENT ON COLUMN proxy_model_configs.block_on_input_risk IS '输入风险时是否阻断，默认不阻断（只记录）';
COMMENT ON COLUMN proxy_model_configs.block_on_output_risk IS '输出风险时是否阻断，默认不阻断（只记录）';
COMMENT ON COLUMN proxy_model_configs.enable_reasoning_detection IS '是否检测reasoning_content字段内容，默认开启且不可关闭';

-- 新的极简设计理念：
-- 1. 核心配置：只需要api_base_url, api_key, model_name三个字段  
-- 2. 完全透传：所有请求参数由用户动态传递
-- 3. 默认安全：始终检测输入输出和推理内容，但默认不阻断（用户可选择开启阻断）
-- 4. 原生体验：用户可以完全按照OpenAI API方式使用
-- 5. 推理检测：默认开启且不可关闭，确保推理过程的安全性