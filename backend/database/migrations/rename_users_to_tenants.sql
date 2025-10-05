-- 将用户概念重命名为租户概念的数据库迁移脚本
-- 执行时间: 2025-10-05
-- 说明: 将 users 表重命名为 tenants,所有 user_id 字段重命名为 tenant_id

-- ============================================================
-- 第一步: 重命名主表 users -> tenants
-- ============================================================
ALTER TABLE users RENAME TO tenants;

-- ============================================================
-- 第二步: 重命名所有表中的 user_id 列为 tenant_id
-- ============================================================

-- detection_results 表
ALTER TABLE detection_results
    RENAME COLUMN user_id TO tenant_id;

-- blacklist 表
ALTER TABLE blacklist
    RENAME COLUMN user_id TO tenant_id;

-- whitelist 表
ALTER TABLE whitelist
    RENAME COLUMN user_id TO tenant_id;

-- response_templates 表
ALTER TABLE response_templates
    RENAME COLUMN user_id TO tenant_id;

-- user_switches 表 (需要重命名两个字段)
ALTER TABLE user_switches
    RENAME COLUMN admin_user_id TO admin_tenant_id;
ALTER TABLE user_switches
    RENAME COLUMN target_user_id TO target_tenant_id;

-- risk_type_config 表
ALTER TABLE risk_type_config
    RENAME COLUMN user_id TO tenant_id;

-- user_rate_limits 表
ALTER TABLE user_rate_limits
    RENAME COLUMN user_id TO tenant_id;

-- user_rate_limit_counters 表
ALTER TABLE user_rate_limit_counters
    RENAME COLUMN user_id TO tenant_id;

-- test_model_configs 表
ALTER TABLE test_model_configs
    RENAME COLUMN user_id TO tenant_id;

-- proxy_model_configs 表
ALTER TABLE proxy_model_configs
    RENAME COLUMN user_id TO tenant_id;

-- proxy_request_logs 表
ALTER TABLE proxy_request_logs
    RENAME COLUMN user_id TO tenant_id;

-- knowledge_bases 表
ALTER TABLE knowledge_bases
    RENAME COLUMN user_id TO tenant_id;

-- online_test_model_selections 表
ALTER TABLE online_test_model_selections
    RENAME COLUMN user_id TO tenant_id;

-- data_security_entity_types 表
ALTER TABLE data_security_entity_types
    RENAME COLUMN user_id TO tenant_id;

-- ============================================================
-- 第三步: 重命名相关表名
-- ============================================================

-- user_switches -> tenant_switches
ALTER TABLE user_switches RENAME TO tenant_switches;

-- user_rate_limits -> tenant_rate_limits
ALTER TABLE user_rate_limits RENAME TO tenant_rate_limits;

-- user_rate_limit_counters -> tenant_rate_limit_counters
ALTER TABLE user_rate_limit_counters RENAME TO tenant_rate_limit_counters;

-- ============================================================
-- 第四步: 更新外键约束名称 (如果数据库自动生成了约束名称)
-- 注意: PostgreSQL 的外键约束名称会自动更新引用的表名,但为了清晰性,
--       我们可以手动检查并重命名
-- ============================================================

-- 查询当前所有外键约束 (仅供参考,不执行)
-- SELECT conname, conrelid::regclass, confrelid::regclass
-- FROM pg_constraint
-- WHERE confrelid = 'tenants'::regclass;

-- ============================================================
-- 第五步: 重命名索引 (按照新的命名规范)
-- ============================================================

-- detection_results 表的索引
ALTER INDEX IF EXISTS idx_detection_results_user_id
    RENAME TO idx_detection_results_tenant_id;

-- blacklist 表的索引
ALTER INDEX IF EXISTS idx_blacklist_user_id
    RENAME TO idx_blacklist_tenant_id;

-- whitelist 表的索引
ALTER INDEX IF EXISTS idx_whitelist_user_id
    RENAME TO idx_whitelist_tenant_id;

-- response_templates 表的索引
ALTER INDEX IF EXISTS idx_response_templates_user_id
    RENAME TO idx_response_templates_tenant_id;

-- tenant_rate_limits 表的索引
ALTER INDEX IF EXISTS idx_user_rate_limits_user_id
    RENAME TO idx_tenant_rate_limits_tenant_id;

ALTER INDEX IF EXISTS idx_user_rate_limits_is_active
    RENAME TO idx_tenant_rate_limits_is_active;

-- ============================================================
-- 验证迁移结果
-- ============================================================

-- 验证表是否存在
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tenants') THEN
        RAISE EXCEPTION '迁移失败: tenants 表不存在';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE EXCEPTION '迁移失败: users 表仍然存在';
    END IF;

    RAISE NOTICE '✓ 表重命名成功';
END $$;

-- 验证列是否重命名
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'detection_results' AND column_name = 'tenant_id'
    ) THEN
        RAISE EXCEPTION '迁移失败: detection_results.tenant_id 列不存在';
    END IF;

    RAISE NOTICE '✓ 列重命名成功';
END $$;

-- ============================================================
-- 完成
-- ============================================================
