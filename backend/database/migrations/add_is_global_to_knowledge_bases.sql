-- 添加is_global列到knowledge_bases表
-- 用于支持全局知识库功能（所有用户生效的知识库）

-- 添加is_global列
ALTER TABLE knowledge_bases 
ADD COLUMN is_global BOOLEAN DEFAULT false NOT NULL;

-- 添加索引以提高查询性能
CREATE INDEX idx_knowledge_bases_is_global ON knowledge_bases(is_global);

-- 更新现有记录，默认都不是全局知识库
UPDATE knowledge_bases SET is_global = false WHERE is_global IS NULL;

-- 添加注释
COMMENT ON COLUMN knowledge_bases.is_global IS '是否为全局知识库（所有用户生效），仅管理员可设置';
