-- Rollback: Remove multi-API key support
-- WARNING: This will delete all non-default API keys

-- Step 1: Drop triggers and functions
DROP TRIGGER IF EXISTS trigger_update_tenant_api_keys_updated_at ON tenant_api_keys;
DROP FUNCTION IF EXISTS update_tenant_api_keys_updated_at();

-- Step 2: Drop association table
DROP TABLE IF EXISTS api_key_blacklist_associations CASCADE;

-- Step 3: Drop tenant_api_keys table
DROP TABLE IF EXISTS tenant_api_keys CASCADE;

-- Step 4: Revert risk_type_config changes
ALTER TABLE risk_type_config DROP CONSTRAINT IF EXISTS _tenant_risk_config_name_uc;
ALTER TABLE risk_type_config DROP COLUMN IF EXISTS name;
ALTER TABLE risk_type_config DROP COLUMN IF EXISTS is_default;

-- Re-add unique constraint on tenant_id
ALTER TABLE risk_type_config ADD CONSTRAINT risk_type_config_tenant_id_key UNIQUE (tenant_id);

-- Rollback completed
