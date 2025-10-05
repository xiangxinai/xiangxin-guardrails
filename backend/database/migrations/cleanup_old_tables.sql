-- 清理旧的用户相关表
-- 执行时间: 2025-10-05
-- 说明: 删除迁移后遗留的旧表(users, user_switches, user_rate_limits, user_rate_limit_counters)

-- 由于新表(tenants)已经存在,我们需要处理数据迁移和外键

-- 第一步: 检查并迁移数据从 users 到 tenants (如果tenants为空)
DO $$
DECLARE
    users_count INTEGER;
    tenants_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO users_count FROM users;
    SELECT COUNT(*) INTO tenants_count FROM tenants;

    IF users_count > 0 AND tenants_count = 0 THEN
        RAISE NOTICE '正在将 % 条记录从 users 迁移到 tenants', users_count;
        INSERT INTO tenants SELECT * FROM users;
        RAISE NOTICE '✓ 数据迁移完成';
    ELSIF tenants_count > 0 THEN
        RAISE NOTICE '✓ tenants 表已有 % 条记录，跳过迁移', tenants_count;
    END IF;
END $$;

-- 第二步: 更新所有外键约束,将 users 改为 tenants
-- 注意: 这些外键约束可能有系统生成的名称,我们需要先找到它们

-- 删除指向 users 的外键约束
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT conname, conrelid::regclass AS table_name
        FROM pg_constraint
        WHERE confrelid = 'users'::regclass
        AND contype = 'f'
    LOOP
        RAISE NOTICE '删除外键: %.%', r.table_name, r.conname;
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %I', r.table_name, r.conname);
    END LOOP;
END $$;

-- 重新创建指向 tenants 的外键约束
ALTER TABLE detection_results
    ADD CONSTRAINT detection_results_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE blacklist
    ADD CONSTRAINT blacklist_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE whitelist
    ADD CONSTRAINT whitelist_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE response_templates
    ADD CONSTRAINT response_templates_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE tenant_switches
    ADD CONSTRAINT tenant_switches_admin_tenant_id_fkey
    FOREIGN KEY (admin_tenant_id) REFERENCES tenants(id);

ALTER TABLE tenant_switches
    ADD CONSTRAINT tenant_switches_target_tenant_id_fkey
    FOREIGN KEY (target_tenant_id) REFERENCES tenants(id);

ALTER TABLE risk_type_config
    ADD CONSTRAINT risk_type_config_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE tenant_rate_limits
    ADD CONSTRAINT tenant_rate_limits_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE tenant_rate_limit_counters
    ADD CONSTRAINT tenant_rate_limit_counters_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE test_model_configs
    ADD CONSTRAINT test_model_configs_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE proxy_model_configs
    ADD CONSTRAINT proxy_model_configs_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE proxy_request_logs
    ADD CONSTRAINT proxy_request_logs_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE knowledge_bases
    ADD CONSTRAINT knowledge_bases_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE online_test_model_selections
    ADD CONSTRAINT online_test_model_selections_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE data_security_entity_types
    ADD CONSTRAINT data_security_entity_types_tenant_id_fkey
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);

-- 第三步: 删除旧表
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS user_switches CASCADE;
DROP TABLE IF EXISTS user_rate_limits CASCADE;
DROP TABLE IF EXISTS user_rate_limit_counters CASCADE;

-- 验证清理结果
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE EXCEPTION '清理失败: users 表仍然存在';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tenants') THEN
        RAISE EXCEPTION '清理失败: tenants 表不存在';
    END IF;

    RAISE NOTICE '✓ 旧表清理成功';
END $$;
