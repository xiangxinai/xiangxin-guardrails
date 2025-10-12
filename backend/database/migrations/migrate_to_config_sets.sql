-- Migration Script: Migrate existing data to use Config Sets
-- Purpose: Ensure all tenants have a default config set and all existing configurations are associated with it
-- Date: 2025-10-10
-- Author: Claude Code

-- ============================================================================
-- STEP 1: Create default config sets for tenants that don't have one
-- ============================================================================

INSERT INTO risk_type_config (
    tenant_id,
    name,
    description,
    is_default,
    s1_enabled, s2_enabled, s3_enabled, s4_enabled,
    s5_enabled, s6_enabled, s7_enabled, s8_enabled,
    s9_enabled, s10_enabled, s11_enabled, s12_enabled,
    high_sensitivity_threshold,
    medium_sensitivity_threshold,
    low_sensitivity_threshold,
    sensitivity_trigger_level,
    created_at,
    updated_at
)
SELECT
    id as tenant_id,
    'Default Config' as name,
    'Default configuration set created during migration' as description,
    true as is_default,
    true, true, true, true,  -- All risk types enabled by default
    true, true, true, true,
    true, true, true, true,
    0.40 as high_sensitivity_threshold,
    0.60 as medium_sensitivity_threshold,
    0.95 as low_sensitivity_threshold,
    'medium' as sensitivity_trigger_level,
    NOW() as created_at,
    NOW() as updated_at
FROM tenants
WHERE id NOT IN (
    SELECT DISTINCT tenant_id
    FROM risk_type_config
    WHERE is_default = true
);

-- ============================================================================
-- STEP 2: Associate existing API keys with default config sets
-- ============================================================================

-- Update tenant_api_keys that don't have a template_id
UPDATE tenant_api_keys
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = tenant_api_keys.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = tenant_api_keys.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- STEP 3: Associate existing blacklists with default config sets
-- ============================================================================

UPDATE blacklist
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = blacklist.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = blacklist.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- STEP 4: Associate existing whitelists with default config sets
-- ============================================================================

UPDATE whitelist
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = whitelist.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = whitelist.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- STEP 5: Associate existing response templates with default config sets
-- ============================================================================

UPDATE response_templates
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = response_templates.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND tenant_id IS NOT NULL  -- Don't update global templates
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = response_templates.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- STEP 6: Associate existing knowledge bases with default config sets
-- ============================================================================

UPDATE knowledge_bases
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = knowledge_bases.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND is_global = false  -- Don't update global knowledge bases
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = knowledge_bases.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- STEP 7: Associate existing data security entity types with default config sets
-- ============================================================================

UPDATE data_security_entity_types
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = data_security_entity_types.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND is_global = false  -- Don't update global entity types
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = data_security_entity_types.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- STEP 8: Associate existing ban policies with default config sets
-- ============================================================================

UPDATE ban_policies
SET template_id = (
    SELECT id
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = ban_policies.tenant_id
    AND risk_type_config.is_default = true
    LIMIT 1
),
updated_at = NOW()
WHERE template_id IS NULL
AND EXISTS (
    SELECT 1
    FROM risk_type_config
    WHERE risk_type_config.tenant_id = ban_policies.tenant_id
    AND risk_type_config.is_default = true
);

-- ============================================================================
-- VERIFICATION QUERIES (Run after migration to verify)
-- ============================================================================

-- Check: All tenants should have at least one default config set
-- Expected: COUNT should equal total number of tenants
-- SELECT COUNT(*) as tenants_with_default_config
-- FROM risk_type_config
-- WHERE is_default = true;

-- Check: All active API keys should have a template_id
-- Expected: COUNT should be 0 (no API keys without template_id)
-- SELECT COUNT(*) as api_keys_without_template
-- FROM tenant_api_keys
-- WHERE template_id IS NULL
-- AND is_active = true;

-- Check: All tenant-owned blacklists should have a template_id
-- Expected: COUNT should be 0
-- SELECT COUNT(*) as blacklists_without_template
-- FROM blacklist
-- WHERE template_id IS NULL;

-- Check: All tenant-owned whitelists should have a template_id
-- Expected: COUNT should be 0
-- SELECT COUNT(*) as whitelists_without_template
-- FROM whitelist
-- WHERE template_id IS NULL;

-- Check: All tenant-owned response templates should have a template_id
-- Expected: COUNT should be close to 0 (only global templates should be NULL)
-- SELECT COUNT(*) as response_templates_without_template
-- FROM response_templates
-- WHERE template_id IS NULL
-- AND tenant_id IS NOT NULL;

-- Check: Summary of config sets per tenant
-- SELECT
--     t.email,
--     COUNT(rtc.id) as config_set_count,
--     SUM(CASE WHEN rtc.is_default THEN 1 ELSE 0 END) as default_count
-- FROM tenants t
-- LEFT JOIN risk_type_config rtc ON t.id = rtc.tenant_id
-- GROUP BY t.id, t.email
-- ORDER BY t.email;

-- ============================================================================
-- ROLLBACK SCRIPT (If needed)
-- ============================================================================

-- To rollback, set all template_ids to NULL (system will use default behavior)
--
-- UPDATE tenant_api_keys SET template_id = NULL WHERE template_id IS NOT NULL;
-- UPDATE blacklist SET template_id = NULL WHERE template_id IS NOT NULL;
-- UPDATE whitelist SET template_id = NULL WHERE template_id IS NOT NULL;
-- UPDATE response_templates SET template_id = NULL WHERE template_id IS NOT NULL;
-- UPDATE knowledge_bases SET template_id = NULL WHERE template_id IS NOT NULL;
-- UPDATE data_security_entity_types SET template_id = NULL WHERE template_id IS NOT NULL;
-- UPDATE ban_policies SET template_id = NULL WHERE template_id IS NOT NULL;
--
-- Optionally delete auto-created default config sets:
-- DELETE FROM risk_type_config
-- WHERE name = 'Default Config'
-- AND description = 'Default configuration set created during migration';

-- ============================================================================
-- NOTES
-- ============================================================================

-- 1. This migration is IDEMPOTENT - safe to run multiple times
-- 2. It will only update records where template_id IS NULL
-- 3. Global configurations (is_global=true) are NOT updated
-- 4. The migration maintains backward compatibility
-- 5. After running, verify using the verification queries above
-- 6. Rollback is available but should only be used in emergencies

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
