-- 回滚脚本: 将租户概念恢复为用户概念
-- 执行时间: 2025-10-05
-- 说明: 将 tenants 表重命名回 users,所有 tenant_id 字段重命名回 user_id

-- ============================================================
-- 第一步: 重命名索引回原名
-- ============================================================

ALTER INDEX IF EXISTS idx_detection_results_tenant_id
    RENAME TO idx_detection_results_user_id;

ALTER INDEX IF EXISTS idx_blacklist_tenant_id
    RENAME TO idx_blacklist_user_id;

ALTER INDEX IF EXISTS idx_whitelist_tenant_id
    RENAME TO idx_whitelist_user_id;

ALTER INDEX IF EXISTS idx_response_templates_tenant_id
    RENAME TO idx_response_templates_user_id;

ALTER INDEX IF EXISTS idx_tenant_rate_limits_tenant_id
    RENAME TO idx_user_rate_limits_user_id;

ALTER INDEX IF EXISTS idx_tenant_rate_limits_is_active
    RENAME TO idx_user_rate_limits_is_active;

-- ============================================================
-- 第二步: 重命名相关表名回原名
-- ============================================================

ALTER TABLE tenant_switches RENAME TO user_switches;
ALTER TABLE tenant_rate_limits RENAME TO user_rate_limits;
ALTER TABLE tenant_rate_limit_counters RENAME TO user_rate_limit_counters;

-- ============================================================
-- 第三步: 重命名所有表中的 tenant_id 列回 user_id
-- ============================================================

ALTER TABLE detection_results
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE blacklist
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE whitelist
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE response_templates
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE user_switches
    RENAME COLUMN admin_tenant_id TO admin_user_id;
ALTER TABLE user_switches
    RENAME COLUMN target_tenant_id TO target_user_id;

ALTER TABLE risk_type_config
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE user_rate_limits
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE user_rate_limit_counters
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE test_model_configs
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE proxy_model_configs
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE proxy_request_logs
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE knowledge_bases
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE online_test_model_selections
    RENAME COLUMN tenant_id TO user_id;

ALTER TABLE data_security_entity_types
    RENAME COLUMN tenant_id TO user_id;

-- ============================================================
-- 第四步: 重命名主表 tenants -> users
-- ============================================================
ALTER TABLE tenants RENAME TO users;

-- ============================================================
-- 验证回滚结果
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE EXCEPTION '回滚失败: users 表不存在';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tenants') THEN
        RAISE EXCEPTION '回滚失败: tenants 表仍然存在';
    END IF;

    RAISE NOTICE '✓ 回滚成功';
END $$;
