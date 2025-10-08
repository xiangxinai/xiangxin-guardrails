-- Migration: Convert Chinese field values to English
-- Date: 2025-10-06
-- Description: This migration updates all Chinese risk levels, suggested actions, and sensitivity levels to English equivalents

-- Update detection_results table
-- Risk levels: 无风险->no_risk, 低风险->low_risk, 中风险->medium_risk, 高风险->high_risk
UPDATE detection_results SET security_risk_level = 'no_risk' WHERE security_risk_level = '无风险';
UPDATE detection_results SET security_risk_level = 'low_risk' WHERE security_risk_level = '低风险';
UPDATE detection_results SET security_risk_level = 'medium_risk' WHERE security_risk_level = '中风险';
UPDATE detection_results SET security_risk_level = 'high_risk' WHERE security_risk_level = '高风险';

UPDATE detection_results SET compliance_risk_level = 'no_risk' WHERE compliance_risk_level = '无风险';
UPDATE detection_results SET compliance_risk_level = 'low_risk' WHERE compliance_risk_level = '低风险';
UPDATE detection_results SET compliance_risk_level = 'medium_risk' WHERE compliance_risk_level = '中风险';
UPDATE detection_results SET compliance_risk_level = 'high_risk' WHERE compliance_risk_level = '高风险';

UPDATE detection_results SET data_risk_level = 'no_risk' WHERE data_risk_level = '无风险';
UPDATE detection_results SET data_risk_level = 'low_risk' WHERE data_risk_level = '低风险';
UPDATE detection_results SET data_risk_level = 'medium_risk' WHERE data_risk_level = '中风险';
UPDATE detection_results SET data_risk_level = 'high_risk' WHERE data_risk_level = '高风险';

-- Suggested actions: 通过->pass, 拒答->reject, 代答->replace, 阻断->block, 放行->allow
UPDATE detection_results SET suggest_action = 'pass' WHERE suggest_action = '通过';
UPDATE detection_results SET suggest_action = 'reject' WHERE suggest_action = '拒答';
UPDATE detection_results SET suggest_action = 'replace' WHERE suggest_action = '代答';
UPDATE detection_results SET suggest_action = 'block' WHERE suggest_action = '阻断';
UPDATE detection_results SET suggest_action = 'allow' WHERE suggest_action = '放行';

-- Sensitivity levels: 高->high, 中->medium, 低->low
UPDATE detection_results SET sensitivity_level = 'high' WHERE sensitivity_level = '高';
UPDATE detection_results SET sensitivity_level = 'medium' WHERE sensitivity_level = '中';
UPDATE detection_results SET sensitivity_level = 'low' WHERE sensitivity_level = '低';

-- Update response_templates table
UPDATE response_templates SET risk_level = 'no_risk' WHERE risk_level = '无风险';
UPDATE response_templates SET risk_level = 'low_risk' WHERE risk_level = '低风险';
UPDATE response_templates SET risk_level = 'medium_risk' WHERE risk_level = '中风险';
UPDATE response_templates SET risk_level = 'high_risk' WHERE risk_level = '高风险';

-- Update data_security_entity_types table (if exists)
UPDATE data_security_entity_types SET risk_level = 'low' WHERE risk_level = '低';
UPDATE data_security_entity_types SET risk_level = 'medium' WHERE risk_level = '中';
UPDATE data_security_entity_types SET risk_level = 'high' WHERE risk_level = '高';

-- Update ban_policies table (if exists)
UPDATE ban_policies SET risk_level_threshold = 'no_risk' WHERE risk_level_threshold = '无风险';
UPDATE ban_policies SET risk_level_threshold = 'low_risk' WHERE risk_level_threshold = '低风险';
UPDATE ban_policies SET risk_level_threshold = 'medium_risk' WHERE risk_level_threshold = '中风险';
UPDATE ban_policies SET risk_level_threshold = 'high_risk' WHERE risk_level_threshold = '高风险';

-- Print migration completion message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: All Chinese field values have been converted to English';
END $$;
