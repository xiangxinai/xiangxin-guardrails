# Protection Config Template Implementation Summary

## Overview

This document summarizes the implementation of the Protection Config Template feature, which allows tenants to create multiple configuration templates and associate different API keys with different protection strategies.

## Problem Statement

Previously, the system required all protection configurations (risk types, sensitivity, data security, blacklists, etc.) to be tenant-level. This meant:

- A tenant could only have ONE set of protection rules
- Different AI applications couldn't have different protection strategies
- No way to have different configs for production vs. testing environments

Users requested the ability to:
1. Create multiple protection configuration templates
2. Associate each API key with a specific template
3. Group ALL protection settings (risk types, sensitivity, data security, ban policies, blacklists, whitelists, knowledge bases) under a template

## Solution Design

### Core Concept: Protection Config Template

A Protection Config Template is a grouping of all protection settings:

```
Protection Config Template
├── Risk Type Configuration (S1-S12 switches)
├── Sensitivity Thresholds (high/medium/low)
├── Data Security Patterns (associated via template_id)
├── Whitelists (associated via template_id)
├── Response Templates (associated via template_id)
├── Knowledge Bases (associated via template_id)
└── Ban Policies (associated via template_id)
```

### Database Changes

#### 1. Renamed Column in `tenant_api_keys`

```sql
-- Before
tenant_api_keys.risk_config_id -> RiskTypeConfig

-- After
tenant_api_keys.template_id -> RiskTypeConfig (now represents full protection template)
```

#### 2. Added `template_id` to Configuration Tables

All protection-related tables now have an optional `template_id` foreign key:

- `whitelist.template_id`
- `response_templates.template_id`
- `knowledge_bases.template_id`
- `data_security_entity_types.template_id`
- `ban_policies.template_id`

**Note**: `blacklist` uses the existing `api_key_blacklist_associations` table for template linkage.

#### 3. Semantic Clarification

The `risk_type_config` table now serves as the **Protection Config Template** table. While we kept the table name for backwards compatibility, the concept has expanded from just "risk type config" to a full "protection template."

## Implementation Files

### Database Migration

1. **Migration Script**: `backend/database/migrations/add_protection_config_template_support.sql`
   - Renames `risk_config_id` to `template_id` in `tenant_api_keys`
   - Adds `template_id` column to all configuration tables
   - Migrates existing data to default templates
   - Creates helper function for creating default templates

2. **Rollback Script**: `backend/database/migrations/rollback_protection_config_template_support.sql`
   - Reverses all changes if needed

### Code Changes

1. **Models** (`backend/database/models.py`):
   - Updated `TenantApiKey`: `risk_config_id` → `template_id`
   - Added `template_id` to: `Whitelist`, `ResponseTemplate`, `KnowledgeBase`, `DataSecurityEntityType`
   - Added `BanPolicy` model with `template_id`
   - Added `protection_template` relationships

2. **API Key Service** (`backend/services/api_key_service.py`):
   - Updated all methods to use `template_id` instead of `risk_config_id`
   - Updated response format: `template_id` and `template_name`

3. **API Routes** (`backend/routers/api_keys.py`):
   - Updated request/response models to use `template_id`
   - Updated all endpoints to use new parameter names

4. **Risk Config Service** (`backend/services/risk_config_service.py`):
   - Updated class documentation to reflect "Protection Config Template" concept
   - No functional changes needed (already supported multiple configs)

### Documentation

1. **Comprehensive Guide**: `backend/docs/PROTECTION_CONFIG_TEMPLATES.md`
   - Architecture overview
   - Usage examples
   - Use cases
   - Migration guide
   - Best practices
   - Troubleshooting

2. **Implementation Summary**: This file

## How It Works

### 1. Template Creation

Tenants can create multiple protection config templates:

```python
# Create a strict template for production
prod_template = RiskTypeConfig(
    tenant_id=tenant_id,
    name="Production Strict",
    is_default=False,
    s1_enabled=True,
    s2_enabled=True,
    ...
    sensitivity_trigger_level="high"
)

# Create a lenient template for testing
test_template = RiskTypeConfig(
    tenant_id=tenant_id,
    name="Test Environment",
    is_default=False,
    s9_enabled=True,  # Only prompt injection
    sensitivity_trigger_level="low"
)
```

### 2. API Key Association

Each API key is associated with one template:

```python
# Production API key uses strict template
prod_key = TenantApiKey(
    tenant_id=tenant_id,
    name="Production App",
    api_key="sk-xxai-...",
    template_id=prod_template.id
)

# Test API key uses lenient template
test_key = TenantApiKey(
    tenant_id=tenant_id,
    name="Test App",
    api_key="sk-xxai-...",
    template_id=test_template.id
)
```

### 3. Configuration Association

Protection configurations can be template-specific:

```python
# Create whitelist only for production template
prod_whitelist = Whitelist(
    tenant_id=tenant_id,
    template_id=prod_template.id,  # Only applies to prod template
    name="Production Whitelist",
    keywords=["safe1", "safe2"]
)

# Create data pattern only for production template
prod_data_pattern = DataSecurityEntityType(
    tenant_id=tenant_id,
    template_id=prod_template.id,  # Only applies to prod template
    entity_type="SSN",
    pattern=r"..."
)

# Create global configuration (applies to all templates)
global_blacklist = Blacklist(
    tenant_id=tenant_id,
    # No template_id - applies to all
    name="Company-wide Blacklist",
    keywords=["bad1", "bad2"]
)
```

### 4. Detection Flow

When a detection request comes in:

1. Identify which API key is being used
2. Get the template associated with that API key
3. Load all configurations associated with that template:
   - Risk type settings from the template itself
   - Data security patterns with matching `template_id`
   - Whitelists with matching `template_id`
   - Knowledge bases with matching `template_id`
   - Ban policies with matching `template_id`
   - Plus all global configs (NULL `template_id`)
4. Apply detection using the combined configuration

## Use Cases

### Use Case 1: Environment-Based Configuration

```
Production Template
├── All risk types enabled
├── High sensitivity (0.4 threshold)
├── Strict data protection patterns
└── Comprehensive knowledge bases

Staging Template
├── Most risk types enabled
├── Medium sensitivity (0.6 threshold)
├── Basic data protection
└── Limited knowledge bases

Testing Template
├── Only critical risk types
├── Low sensitivity (0.95 threshold)
├── Minimal data protection
└── No knowledge bases
```

### Use Case 2: Application-Specific Configuration

```
Public Chatbot Template
├── All risk types enabled
├── High sensitivity
├── Public-appropriate knowledge base
└── Strict ban policies

Internal Assistant Template
├── Fewer risk types
├── Medium sensitivity
├── Internal knowledge base
└── Relaxed ban policies

Admin Tool Template
├── Minimal filtering
├── Low sensitivity
├── Admin-specific patterns
└── No ban policies
```

### Use Case 3: Regional Compliance

```
China Template
├── S1, S2, S3 enabled (political content)
├── China-specific data patterns (ID cards, phone numbers)
├── China-compliant knowledge base
└── Strict ban policies

EU Template
├── S11 enabled (privacy focused)
├── GDPR-specific data patterns
├── EU-compliant responses
└── Privacy-focused policies

US Template
├── Moderate filtering
├── US-specific patterns
├── US-appropriate content
└── Standard policies
```

## Migration Path

### For Existing Deployments

1. **Run Migration Script**:
   ```bash
   psql -U xiangxin -d xiangxin_guardrails \
     -f backend/database/migrations/add_protection_config_template_support.sql
   ```

2. **Verify Migration**:
   - All existing API keys should now have `template_id` pointing to their tenant's default template
   - All existing configurations should be associated with default templates
   - System should continue to work as before

3. **Optional: Create Additional Templates**:
   - Use the API to create new templates
   - Associate API keys with different templates
   - Create template-specific configurations

### Backwards Compatibility

The migration is designed to be **fully backwards compatible**:

- Existing API keys automatically get associated with default template
- Existing configurations automatically get associated with default template
- No code changes required in detection service (already handles configs by API key)
- API responses include both old and new field names initially

## Testing Checklist

- [ ] Run migration script on test database
- [ ] Verify existing API keys still work
- [ ] Create new template via API
- [ ] Create new API key with template
- [ ] Test detection with different templates
- [ ] Verify configuration isolation between templates
- [ ] Test global vs template-specific configs
- [ ] Test template deletion (should prevent if in use)
- [ ] Test API key template reassignment
- [ ] Verify frontend displays template info correctly

## Frontend Changes Needed

The frontend will need updates to:

1. **Template Management Page**:
   - List all templates
   - Create/edit/delete templates
   - Show which API keys use each template

2. **API Key Management**:
   - Show template association for each key
   - Allow selecting template when creating key
   - Allow changing template for existing key

3. **Configuration Pages**:
   - Show template filter/selector
   - Indicate which template a config belongs to
   - Option to make configs global (NULL template_id)

4. **Dashboard/Overview**:
   - Show stats per template
   - Compare templates side-by-side

## Benefits

1. **Flexibility**: Different protection strategies for different apps/environments
2. **Isolation**: Configurations don't interfere with each other
3. **Maintainability**: Easier to manage complex protection requirements
4. **Scalability**: Support many applications with different needs
5. **Compliance**: Meet different regulatory requirements per region/use case

## Future Enhancements

1. **Template Cloning**: Duplicate templates quickly
2. **Template Import/Export**: Share templates between tenants
3. **Template Versioning**: Track changes over time
4. **Template Presets**: Pre-configured templates for common scenarios
5. **Template Comparison Tool**: Side-by-side comparison UI
6. **Template Testing**: Test configurations before applying
7. **Template Analytics**: Per-template detection statistics

## Conclusion

The Protection Config Template feature provides a powerful and flexible way for tenants to manage multiple protection configurations. The implementation maintains backwards compatibility while enabling advanced use cases for complex deployments.

## Questions or Issues?

For questions or issues, refer to:
- [Protection Config Templates Documentation](backend/docs/PROTECTION_CONFIG_TEMPLATES.md)
- [Database Migration Files](backend/database/migrations/)
- Contact the development team
