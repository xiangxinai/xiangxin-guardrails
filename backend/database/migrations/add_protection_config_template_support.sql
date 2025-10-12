-- Migration: Add Protection Config Template support
-- This migration enables configuration templates that group all protection settings
-- (risk types, sensitivity, data security, blacklist/whitelist, ban policies, knowledge bases)
-- Each API key will be associated with a specific protection config template

-- ============================================================================
-- Step 1: Rename risk_config_id to template_id in tenant_api_keys
-- ============================================================================

-- Rename the column to better reflect its purpose
ALTER TABLE tenant_api_keys
RENAME COLUMN risk_config_id TO template_id;

COMMENT ON COLUMN tenant_api_keys.template_id IS 'Protection config template ID - groups all protection settings';

-- ============================================================================
-- Step 2: Add template_id to all configuration tables
-- ============================================================================

-- Whitelist table
ALTER TABLE whitelist
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_whitelist_template_id ON whitelist(template_id);

COMMENT ON COLUMN whitelist.template_id IS 'Associated protection config template. NULL means tenant-level (shared across all templates)';

-- Response templates table
ALTER TABLE response_templates
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_response_templates_template_id ON response_templates(template_id);

COMMENT ON COLUMN response_templates.template_id IS 'Associated protection config template. NULL means tenant-level (shared across all templates)';

-- Knowledge bases table
ALTER TABLE knowledge_bases
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_knowledge_bases_template_id ON knowledge_bases(template_id);

COMMENT ON COLUMN knowledge_bases.template_id IS 'Associated protection config template. NULL means tenant-level (shared across all templates)';

-- Data security entity types table
ALTER TABLE data_security_entity_types
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_data_security_entity_types_template_id ON data_security_entity_types(template_id);

COMMENT ON COLUMN data_security_entity_types.template_id IS 'Associated protection config template. NULL means tenant-level (shared across all templates)';

-- Ban policies table
ALTER TABLE ban_policies
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES risk_type_config(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_ban_policies_template_id ON ban_policies(template_id);

COMMENT ON COLUMN ban_policies.template_id IS 'Associated protection config template. NULL means tenant-level (shared across all templates)';

-- ============================================================================
-- Step 3: Update comments and documentation
-- ============================================================================

COMMENT ON TABLE risk_type_config IS 'Protection Config Templates - groups all protection settings including risk types, sensitivity thresholds, and references to other configs';
COMMENT ON COLUMN risk_type_config.name IS 'Template name (e.g., "Production Config", "Test Config")';
COMMENT ON COLUMN risk_type_config.is_default IS 'Whether this is the default template for the tenant';

-- ============================================================================
-- Step 4: Data migration - associate existing configs with default templates
-- ============================================================================

-- For each tenant, associate their existing whitelist entries with their default template
UPDATE whitelist w
SET template_id = (
    SELECT id FROM risk_type_config
    WHERE tenant_id = w.tenant_id AND is_default = TRUE
    LIMIT 1
)
WHERE template_id IS NULL;

-- For each tenant, associate their existing response templates with their default template
UPDATE response_templates rt
SET template_id = (
    SELECT id FROM risk_type_config
    WHERE tenant_id = rt.tenant_id AND is_default = TRUE
    LIMIT 1
)
WHERE template_id IS NULL AND tenant_id IS NOT NULL;

-- For each tenant, associate their existing knowledge bases with their default template
UPDATE knowledge_bases kb
SET template_id = (
    SELECT id FROM risk_type_config
    WHERE tenant_id = kb.tenant_id AND is_default = TRUE
    LIMIT 1
)
WHERE template_id IS NULL AND is_global = FALSE;

-- For each tenant, associate their existing data security patterns with their default template
UPDATE data_security_entity_types ds
SET template_id = (
    SELECT id FROM risk_type_config
    WHERE tenant_id = ds.tenant_id AND is_default = TRUE
    LIMIT 1
)
WHERE template_id IS NULL AND is_global = FALSE;

-- For each tenant, associate their existing ban policies with their default template
UPDATE ban_policies bp
SET template_id = (
    SELECT id FROM risk_type_config
    WHERE tenant_id = bp.tenant_id AND is_default = TRUE
    LIMIT 1
)
WHERE template_id IS NULL;

-- ============================================================================
-- Step 5: Add helper functions for template management
-- ============================================================================

-- Function to create a default template when a new tenant is created
CREATE OR REPLACE FUNCTION create_default_protection_template(p_tenant_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_template_id INTEGER;
BEGIN
    -- Create default protection config template
    INSERT INTO risk_type_config (
        tenant_id,
        name,
        is_default,
        s1_enabled, s2_enabled, s3_enabled, s4_enabled,
        s5_enabled, s6_enabled, s7_enabled, s8_enabled,
        s9_enabled, s10_enabled, s11_enabled, s12_enabled,
        high_sensitivity_threshold,
        medium_sensitivity_threshold,
        low_sensitivity_threshold,
        sensitivity_trigger_level
    ) VALUES (
        p_tenant_id,
        'Default Template',
        TRUE,
        TRUE, TRUE, TRUE, TRUE,
        TRUE, TRUE, TRUE, TRUE,
        TRUE, TRUE, TRUE, TRUE,
        0.40, 0.60, 0.95, 'medium'
    )
    RETURNING id INTO v_template_id;

    RETURN v_template_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_default_protection_template IS 'Creates a default protection config template for a new tenant';

-- ============================================================================
-- Migration completed successfully
-- ============================================================================
