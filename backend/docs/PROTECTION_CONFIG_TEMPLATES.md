# Protection Config Templates

## Overview

Protection Config Templates are a core feature that allows tenants to create multiple sets of protection configurations. Each API key can be associated with a specific template, enabling different protection strategies for different AI applications.

## Concept

A **Protection Config Template** groups all protection settings in one place:

- **Risk Type Configuration**: Which risk types (S1-S12) are enabled
- **Sensitivity Thresholds**: High/medium/low sensitivity levels and trigger thresholds
- **Data Security Patterns**: Sensitive data detection and anonymization rules
- **Blacklist/Whitelist**: Keyword filtering lists (via API key associations)
- **Ban Policies**: User blocking policies based on risk behavior
- **Refusal Answer Library**: Pre-configured responses for blocked content
- **Knowledge Bases**: Custom response knowledge bases

## Architecture

### Database Structure

```
┌─────────────────────────────────────┐
│  risk_type_config                   │
│  (Protection Config Templates)      │
├─────────────────────────────────────┤
│ id (PK)                             │
│ tenant_id (FK)                      │
│ name                                │
│ is_default                          │
│ s1_enabled ... s12_enabled          │
│ sensitivity thresholds              │
└─────────────────────────────────────┘
         ▲
         │ template_id (FK)
         │
┌────────┴────────┬─────────────┬──────────────┬──────────────┬─────────────┐
│                 │             │              │              │             │
│ tenant_api_keys │ whitelist   │ response_    │ knowledge_   │ data_       │
│                 │             │ templates    │ bases        │ security_   │
│                 │             │              │              │ entity_types│
│                 │             │              │              │             │
│                 │             │              │              │ ban_policies│
└─────────────────┴─────────────┴──────────────┴──────────────┴─────────────┘
```

### Key Design Principles

1. **One Template per API Key**: Each API key is associated with exactly one protection config template
2. **Template Isolation**: Configuration items (whitelists, knowledge bases, etc.) can be template-specific or tenant-wide (NULL template_id)
3. **Default Template**: Each tenant has a default template used for new API keys
4. **Backwards Compatibility**: Existing configurations migrate to the default template automatically

## Usage

### 1. Creating a Protection Config Template

Use the existing risk config API to create a new template:

```bash
POST /api/v1/risk-config
Content-Type: application/json

{
  "name": "Production Strict Config",
  "is_default": false,
  "s1_enabled": true,
  "s2_enabled": true,
  ...
  "high_sensitivity_threshold": 0.40,
  "medium_sensitivity_threshold": 0.60,
  "low_sensitivity_threshold": 0.95,
  "sensitivity_trigger_level": "medium"
}
```

### 2. Creating an API Key with Template

```bash
POST /api/v1/api-keys
Content-Type: application/json

{
  "name": "Production App",
  "template_id": 123,  # ID of the protection config template
  "is_default": false
}
```

### 3. Associating Configuration Items with Templates

#### Data Security Patterns

```python
# Create a data security pattern for a specific template
pattern = DataSecurityEntityType(
    tenant_id=tenant_id,
    template_id=template_id,  # Associate with template
    entity_type="CREDIT_CARD_NUMBER",
    display_name="Credit Card Number",
    category="high",
    recognition_method="regex",
    recognition_config={"pattern": r"\d{4}-\d{4}-\d{4}-\d{4}"},
    anonymization_method="mask"
)
```

#### Whitelists

```python
# Create a whitelist for a specific template
whitelist = Whitelist(
    tenant_id=tenant_id,
    template_id=template_id,  # Associate with template
    name="Production Whitelist",
    keywords=["safe keyword 1", "safe keyword 2"],
    is_active=True
)
```

#### Knowledge Bases

```python
# Create a knowledge base for a specific template
kb = KnowledgeBase(
    tenant_id=tenant_id,
    template_id=template_id,  # Associate with template
    category="S1",
    name="Production KB",
    file_path="/path/to/kb.jsonl",
    is_active=True
)
```

#### Ban Policies

```python
# Create a ban policy for a specific template
ban_policy = BanPolicy(
    tenant_id=tenant_id,
    template_id=template_id,  # Associate with template
    enabled=True,
    risk_level="high_risk",
    trigger_count=3,
    time_window_minutes=10,
    ban_duration_minutes=60
)
```

### 4. Template-Wide vs Tenant-Wide Configurations

Configuration items can be either:

1. **Template-Specific** (`template_id` is set): Only applies when using API keys associated with this template
2. **Tenant-Wide** (`template_id` is NULL): Applies to all API keys regardless of template

This allows sharing common configurations across templates while customizing specific settings.

## Use Cases

### Use Case 1: Different Risk Levels for Different Apps

A SaaS company has:
- **Public-facing chatbot**: Requires strict content filtering (high sensitivity)
- **Internal assistant**: Moderate filtering (medium sensitivity)
- **Testing environment**: Minimal filtering (low sensitivity)

**Solution**:
```python
# Create three templates
strict_template = create_template(
    name="Public Chatbot Config",
    sensitivity_trigger_level="high",
    all_risk_types_enabled=True
)

moderate_template = create_template(
    name="Internal Assistant Config",
    sensitivity_trigger_level="medium",
    s1_enabled=False  # Disable some risk types
)

test_template = create_template(
    name="Test Environment Config",
    sensitivity_trigger_level="low",
    s9_enabled=True  # Only prompt injection
)

# Create API keys for each
chatbot_key = create_api_key(
    name="Chatbot Key",
    template_id=strict_template.id
)

internal_key = create_api_key(
    name="Internal Key",
    template_id=moderate_template.id
)

test_key = create_api_key(
    name="Test Key",
    template_id=test_template.id
)
```

### Use Case 2: Regional Compliance

A global company needs different compliance rules for different regions:
- **China**: Strict political content filtering
- **EU**: GDPR-focused data protection
- **US**: Moderate filtering

**Solution**:
```python
# China template - strict political filtering
china_template = create_template(
    name="China Compliance",
    s1_enabled=True,  # General political
    s2_enabled=True,  # Sensitive political
    s3_enabled=True   # National image
)

# Add China-specific data patterns
create_data_pattern(
    template_id=china_template.id,
    entity_type="CHINA_ID_CARD",
    pattern=r"..."
)

# EU template - GDPR focus
eu_template = create_template(
    name="EU GDPR Compliance",
    s11_enabled=True  # Privacy focused
)

# Add EU-specific data patterns
create_data_pattern(
    template_id=eu_template.id,
    entity_type="EU_PASSPORT",
    pattern=r"..."
)
```

## Migration Guide

When migrating from the old system to protection config templates:

### Automatic Migration

The migration script automatically:
1. Renames `risk_config_id` to `template_id` in `tenant_api_keys`
2. Adds `template_id` column to all configuration tables
3. Associates existing configurations with each tenant's default template

### Manual Steps

After migration, you can:

1. **Review Default Templates**: Check that each tenant's default template has correct settings
2. **Create Additional Templates**: Create new templates for different use cases
3. **Update API Keys**: Associate API keys with appropriate templates
4. **Organize Configurations**: Move configurations to specific templates as needed

## API Reference

### Protection Config Template Endpoints

All endpoints are under `/api/v1/risk-config`:

- `POST /api/v1/risk-config` - Create a new template
- `GET /api/v1/risk-config` - List all templates for tenant
- `GET /api/v1/risk-config/{id}` - Get specific template
- `PUT /api/v1/risk-config/{id}` - Update template
- `DELETE /api/v1/risk-config/{id}` - Delete template (if not in use)

### API Key Template Association

- `POST /api/v1/api-keys` - Create API key with `template_id`
- `PUT /api/v1/api-keys/{id}` - Update API key's `template_id`
- `GET /api/v1/api-keys` - List API keys (includes `template_name`)

## Best Practices

### 1. Template Naming

Use descriptive names that indicate the template's purpose:
- ✅ "Production High Security"
- ✅ "Internal Testing - Low Sensitivity"
- ✅ "EU GDPR Compliance"
- ❌ "Config 1"
- ❌ "Test"

### 2. Default Template

Always maintain a sensible default template:
- Enable all critical risk types
- Use medium sensitivity as default
- Include basic data protection patterns

### 3. Template Organization

Consider organizing templates by:
- **Environment**: Production, Staging, Testing
- **Application**: Chatbot, Assistant, API
- **Region**: US, EU, Asia
- **Compliance**: GDPR, HIPAA, PCI-DSS

### 4. Shared vs Template-Specific

Use template-specific configurations for:
- Risk type sensitivity settings
- Application-specific knowledge bases
- Region-specific data patterns

Use tenant-wide (NULL template_id) for:
- Company-wide blacklists
- Common refusal templates
- Global knowledge bases

## Troubleshooting

### Issue: Cannot Delete Template

**Error**: "Cannot delete config: N API key(s) are using it"

**Solution**: First reassociate those API keys to a different template:
```bash
PUT /api/v1/api-keys/{key_id}
{
  "template_id": <other_template_id>
}
```

### Issue: Configuration Not Applied

**Symptom**: Changes to template not reflected in detection results

**Checklist**:
1. Verify API key is associated with the correct template
2. Check if configuration item has `template_id` set (should match API key's template)
3. Ensure configuration is active (`is_active=true`)
4. Check template's `is_default` flag if using default key

### Issue: Template Not Found

**Error**: "Template not found" when creating API key

**Solution**: Create the template first or use an existing template ID:
```bash
# List available templates
GET /api/v1/risk-config

# Use existing template ID or create new one
POST /api/v1/risk-config
```

## Future Enhancements

Planned features for protection config templates:

1. **Template Cloning**: Quickly duplicate templates for similar use cases
2. **Template Comparison**: Side-by-side comparison of different templates
3. **Template Import/Export**: Share templates between tenants
4. **Template Versioning**: Track changes to templates over time
5. **Template Presets**: Pre-configured templates for common use cases

## Related Documentation

- [Risk Type Configuration](RISK_TYPE_CONFIG.md)
- [Data Security](DATA_SECURITY.md)
- [API Key Management](API_KEY_MANAGEMENT.md)
- [Sensitivity Thresholds](SENSITIVITY_THRESHOLDS.md)
