-- Update field lengths to accommodate English values
-- Date: 2025-10-06
-- Description: Increase VARCHAR field lengths for English risk levels and actions

-- Update detection_results table
ALTER TABLE detection_results ALTER COLUMN security_risk_level TYPE VARCHAR(20);
ALTER TABLE detection_results ALTER COLUMN compliance_risk_level TYPE VARCHAR(20);
ALTER TABLE detection_results ALTER COLUMN data_risk_level TYPE VARCHAR(20);
ALTER TABLE detection_results ALTER COLUMN suggest_action TYPE VARCHAR(20);
ALTER TABLE detection_results ALTER COLUMN sensitivity_level TYPE VARCHAR(20);

-- Update response_templates table
ALTER TABLE response_templates ALTER COLUMN risk_level TYPE VARCHAR(20);

-- Update data_security_entity_types table (if exists)
ALTER TABLE data_security_entity_types ALTER COLUMN risk_level TYPE VARCHAR(20);

-- Update ban_policies table (if exists)
ALTER TABLE ban_policies ALTER COLUMN risk_level_threshold TYPE VARCHAR(20);

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'Schema update completed: All field lengths increased to VARCHAR(20)';
END $$;
