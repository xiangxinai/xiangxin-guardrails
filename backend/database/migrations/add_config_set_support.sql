-- Migration: Add Config Set Support
-- Purpose: Enhance RiskTypeConfig to serve as a complete ConfigSet
-- by adding blacklist association and description field

-- 1. Add description field to risk_type_config (for ConfigSet description)
ALTER TABLE risk_type_config
ADD COLUMN IF NOT EXISTS description TEXT;

-- 2. Add template_id to blacklist table (associate blacklist with config set)
ALTER TABLE blacklist
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL;

-- 3. Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_blacklist_template_id ON blacklist(template_id);

-- 4. Add comment to clarify the semantic change
COMMENT ON TABLE risk_type_config IS 'Configuration Set (ConfigSet) - Contains all protection configurations including risk types, sensitivity thresholds, and associations to blacklists, whitelists, response templates, knowledge bases, data security settings, and ban policies';

-- Note:
-- - The table name 'risk_type_config' is kept for backward compatibility
-- - In application code, this table represents a complete "Configuration Set"
-- - API Key binds to a ConfigSet via template_id
-- - All protection configs (blacklist, whitelist, etc.) associate with the same ConfigSet
