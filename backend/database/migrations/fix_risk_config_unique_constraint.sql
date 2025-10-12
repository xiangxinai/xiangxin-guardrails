-- Drop the old unique constraint on tenant_id
-- This allows multiple risk configurations per tenant
DROP INDEX IF EXISTS ix_risk_type_config_user_id;

-- Ensure the correct unique constraint exists (tenant_id + name)
-- This is already defined in models.py, but we verify it here
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = '_tenant_risk_config_name_uc'
    ) THEN
        ALTER TABLE risk_type_config
        ADD CONSTRAINT _tenant_risk_config_name_uc
        UNIQUE (tenant_id, name);
    END IF;
END $$;
