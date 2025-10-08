-- 添加租户级别的实体类型禁用功能
-- 创建时间: 2025-01-27

-- 租户实体类型禁用表
CREATE TABLE IF NOT EXISTS tenant_entity_type_disables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,  -- 实体类型代码，如 ID_CARD_NUMBER_SYS
    disabled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 确保每个租户对每个实体类型只能有一条禁用记录
    UNIQUE(tenant_id, entity_type)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tenant_entity_type_disables_tenant_id ON tenant_entity_type_disables(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_entity_type_disables_entity_type ON tenant_entity_type_disables(entity_type);

-- 添加注释
COMMENT ON TABLE tenant_entity_type_disables IS '租户实体类型禁用表';
COMMENT ON COLUMN tenant_entity_type_disables.tenant_id IS '租户ID';
COMMENT ON COLUMN tenant_entity_type_disables.entity_type IS '被禁用的实体类型代码';
COMMENT ON COLUMN tenant_entity_type_disables.disabled_at IS '禁用时间';
