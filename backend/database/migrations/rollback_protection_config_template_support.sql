-- Rollback Migration: Remove Protection Config Template support
-- This rollback removes template associations from all configuration tables

-- ============================================================================
-- Step 1: Drop helper functions
-- ============================================================================

DROP FUNCTION IF EXISTS create_default_protection_template(UUID);

-- ============================================================================
-- Step 2: Remove template_id from all configuration tables
-- ============================================================================

-- Drop indexes
DROP INDEX IF EXISTS idx_whitelist_template_id;
DROP INDEX IF EXISTS idx_response_templates_template_id;
DROP INDEX IF EXISTS idx_knowledge_bases_template_id;
DROP INDEX IF EXISTS idx_data_security_entity_types_template_id;
DROP INDEX IF EXISTS idx_ban_policies_template_id;

-- Drop columns
ALTER TABLE whitelist DROP COLUMN IF EXISTS template_id;
ALTER TABLE response_templates DROP COLUMN IF EXISTS template_id;
ALTER TABLE knowledge_bases DROP COLUMN IF EXISTS template_id;
ALTER TABLE data_security_entity_types DROP COLUMN IF EXISTS template_id;
ALTER TABLE ban_policies DROP COLUMN IF EXISTS template_id;

-- ============================================================================
-- Step 3: Rename template_id back to risk_config_id in tenant_api_keys
-- ============================================================================

ALTER TABLE tenant_api_keys
RENAME COLUMN template_id TO risk_config_id;

-- ============================================================================
-- Step 4: Restore original comments
-- ============================================================================

COMMENT ON TABLE risk_type_config IS 'Risk type switch config table - can be shared across multiple API keys';
COMMENT ON COLUMN risk_type_config.name IS 'Config name (e.g., "Production Config", "Test Config")';
COMMENT ON COLUMN tenant_api_keys.risk_config_id IS 'Risk type config ID';

-- ============================================================================
-- Rollback completed successfully
-- ============================================================================
