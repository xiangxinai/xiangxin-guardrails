-- Migration: Add multi-API key support for tenants
-- This migration enables tenants to have multiple API keys with different configurations
-- Each API key can be associated with different risk configs, blacklists, and ban policies

-- Step 1: Create tenant_api_keys table
CREATE TABLE IF NOT EXISTS tenant_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    risk_config_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _tenant_api_key_name_uc UNIQUE (tenant_id, name)
);

CREATE INDEX idx_tenant_api_keys_tenant_id ON tenant_api_keys(tenant_id);
CREATE INDEX idx_tenant_api_keys_api_key ON tenant_api_keys(api_key);
CREATE INDEX idx_tenant_api_keys_is_active ON tenant_api_keys(is_active);

-- Step 2: Create association table for API keys and blacklists
CREATE TABLE IF NOT EXISTS api_key_blacklist_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID NOT NULL REFERENCES tenant_api_keys(id) ON DELETE CASCADE,
    blacklist_id INTEGER NOT NULL REFERENCES blacklist(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _api_key_blacklist_uc UNIQUE (api_key_id, blacklist_id)
);

CREATE INDEX idx_api_key_blacklist_api_key_id ON api_key_blacklist_associations(api_key_id);
CREATE INDEX idx_api_key_blacklist_blacklist_id ON api_key_blacklist_associations(blacklist_id);

-- Step 3: Update risk_type_config table to support multiple configs per tenant
-- Add name field and is_default flag
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS name VARCHAR(100);
ALTER TABLE risk_type_config ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;

-- Set default name for existing configs
UPDATE risk_type_config SET name = 'Default Config' WHERE name IS NULL;

-- Make name NOT NULL after setting defaults
ALTER TABLE risk_type_config ALTER COLUMN name SET NOT NULL;

-- Set the first config for each tenant as default
UPDATE risk_type_config rc1
SET is_default = TRUE
WHERE id IN (
    SELECT MIN(id) FROM risk_type_config GROUP BY tenant_id
);

-- Drop old unique constraint on tenant_id (if exists)
ALTER TABLE risk_type_config DROP CONSTRAINT IF EXISTS risk_type_config_tenant_id_key;

-- Add new unique constraint on tenant_id + name
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = '_tenant_risk_config_name_uc'
    ) THEN
        ALTER TABLE risk_type_config ADD CONSTRAINT _tenant_risk_config_name_uc UNIQUE (tenant_id, name);
    END IF;
END $$;

-- Step 4: Migrate existing tenant API keys to new table
-- Create a default API key for each tenant using their existing api_key
INSERT INTO tenant_api_keys (id, tenant_id, api_key, name, is_active, is_default, risk_config_id)
SELECT
    gen_random_uuid(),
    t.id,
    t.api_key,
    'Default Key',
    TRUE,
    TRUE,
    rc.id
FROM tenants t
LEFT JOIN risk_type_config rc ON rc.tenant_id = t.id AND rc.is_default = TRUE
ON CONFLICT (api_key) DO NOTHING;

-- Step 5: Update existing risk configs to be linked to default API keys
UPDATE tenant_api_keys
SET risk_config_id = rc.id
FROM risk_type_config rc
WHERE tenant_api_keys.tenant_id = rc.tenant_id
  AND tenant_api_keys.is_default = TRUE
  AND tenant_api_keys.risk_config_id IS NULL;

-- Step 6: Add comments for documentation
COMMENT ON TABLE tenant_api_keys IS 'Stores multiple API keys per tenant with individual configurations';
COMMENT ON TABLE api_key_blacklist_associations IS 'Associates API keys with specific blacklists';
COMMENT ON COLUMN tenants.api_key IS 'Deprecated: Kept for backward compatibility. Use tenant_api_keys table instead';
COMMENT ON COLUMN risk_type_config.name IS 'Configuration name for easy identification';
COMMENT ON COLUMN risk_type_config.is_default IS 'Whether this is the default risk config for the tenant';
COMMENT ON COLUMN tenant_api_keys.is_default IS 'Whether this is the default API key (used for platform operations)';
COMMENT ON COLUMN tenant_api_keys.last_used_at IS 'Last time this API key was used for detection';

-- Step 7: Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_tenant_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for tenant_api_keys
DROP TRIGGER IF EXISTS trigger_update_tenant_api_keys_updated_at ON tenant_api_keys;
CREATE TRIGGER trigger_update_tenant_api_keys_updated_at
    BEFORE UPDATE ON tenant_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_api_keys_updated_at();

-- Migration completed successfully
