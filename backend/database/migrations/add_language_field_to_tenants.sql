-- 添加language字段到tenants表
-- 创建时间: 2025-01-27

-- 添加language字段
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en' NOT NULL;

-- 添加注释
COMMENT ON COLUMN tenants.language IS 'User language preference';