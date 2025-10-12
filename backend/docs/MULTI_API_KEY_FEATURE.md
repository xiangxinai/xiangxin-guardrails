# Multi-API Key Feature

## Overview

The Multi-API Key feature enables tenants to create and manage multiple API keys, each with its own configuration settings. This allows a single tenant to use different API keys for different applications or environments, with each key having independent:

- Risk type configurations
- Blacklist associations
- Ban policies (future enhancement)

## Use Cases

### 1. Multiple Applications
A tenant with two applications can use different API keys:
- **Key 1 (Production App)**: Detects S1-S12 (all risk types)
- **Key 2 (Customer Support App)**: Only detects S2 (Sensitive Political Topics), S10 (Insults)

### 2. Different Environments
A tenant can use different configurations for different environments:
- **Key 1 (Production)**: Strict ban policy, all risk types enabled
- **Key 2 (Development)**: No ban policy, only critical risks enabled

### 3. Different Blacklists
A tenant can associate different blacklists with different keys:
- **Key 1**: Blacklist A (general offensive terms)
- **Key 2**: Blacklist B (industry-specific terms)

## Architecture

### Database Schema

#### tenant_api_keys Table
```sql
CREATE TABLE tenant_api_keys (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    api_key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    risk_config_id INTEGER REFERENCES risk_type_config(id),
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT _tenant_api_key_name_uc UNIQUE (tenant_id, name)
);
```

#### api_key_blacklist_associations Table
```sql
CREATE TABLE api_key_blacklist_associations (
    id UUID PRIMARY KEY,
    api_key_id UUID REFERENCES tenant_api_keys(id),
    blacklist_id INTEGER REFERENCES blacklist(id),
    created_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT _api_key_blacklist_uc UNIQUE (api_key_id, blacklist_id)
);
```

#### Updated risk_type_config Table
```sql
ALTER TABLE risk_type_config ADD COLUMN name VARCHAR(100) NOT NULL;
ALTER TABLE risk_type_config ADD COLUMN is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE risk_type_config DROP CONSTRAINT risk_type_config_tenant_id_key;
ALTER TABLE risk_type_config ADD CONSTRAINT _tenant_risk_config_name_uc UNIQUE (tenant_id, name);
```

### Component Structure

```
backend/
├── database/
│   ├── models.py (TenantApiKey, ApiKeyBlacklistAssociation models)
│   └── migrations/
│       ├── add_multi_api_key_support.sql
│       └── rollback_multi_api_key_support.sql
├── services/
│   ├── api_key_service.py (CRUD operations for API keys)
│   └── risk_config_service.py (Updated to support config-specific lookups)
├── routers/
│   └── api_keys.py (REST API endpoints)
└── utils/
    └── user.py (Updated to support new API key lookup)
```

## API Endpoints

### Base URL
All endpoints are prefixed with `/api/v1/api-keys`

### Endpoints

#### 1. Create API Key
```http
POST /api/v1/api-keys
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Production App Key",
  "risk_config_id": 1,
  "is_default": false
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Production App Key",
  "api_key": "sk-xxai-...",
  "is_active": true,
  "is_default": false,
  "risk_config_id": 1,
  "risk_config_name": "Production Config",
  "blacklist_ids": [],
  "last_used_at": null,
  "created_at": "2025-10-09T12:00:00Z",
  "updated_at": "2025-10-09T12:00:00Z"
}
```

#### 2. List API Keys
```http
GET /api/v1/api-keys
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "total": 2,
  "api_keys": [
    {
      "id": "uuid1",
      "name": "Default Key",
      "api_key": "sk-xxai-...",
      "is_active": true,
      "is_default": true,
      "risk_config_id": 1,
      "risk_config_name": "Default Config",
      "blacklist_ids": [1, 2],
      "last_used_at": "2025-10-09T12:00:00Z",
      "created_at": "2025-10-09T10:00:00Z",
      "updated_at": "2025-10-09T11:00:00Z"
    },
    {
      "id": "uuid2",
      "name": "Test App Key",
      "api_key": "sk-xxai-...",
      "is_active": true,
      "is_default": false,
      "risk_config_id": 2,
      "risk_config_name": "Test Config",
      "blacklist_ids": [],
      "last_used_at": null,
      "created_at": "2025-10-09T12:00:00Z",
      "updated_at": "2025-10-09T12:00:00Z"
    }
  ]
}
```

#### 3. Get API Key Details
```http
GET /api/v1/api-keys/{api_key_id}
Authorization: Bearer <jwt_token>
```

#### 4. Update API Key
```http
PUT /api/v1/api-keys/{api_key_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "risk_config_id": 2,
  "is_active": true,
  "is_default": false
}
```

#### 5. Delete API Key
```http
DELETE /api/v1/api-keys/{api_key_id}
Authorization: Bearer <jwt_token>
```

**Note:** Cannot delete if:
- It's the only key for the tenant
- It's the default key (set another as default first)

#### 6. Regenerate API Key
```http
POST /api/v1/api-keys/{api_key_id}/regenerate
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "api_key": "sk-xxai-new-key...",
  "message": "API key regenerated successfully"
}
```

#### 7. Associate Blacklist
```http
POST /api/v1/api-keys/{api_key_id}/blacklists
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "blacklist_id": 123
}
```

#### 8. Disassociate Blacklist
```http
DELETE /api/v1/api-keys/{api_key_id}/blacklists/{blacklist_id}
Authorization: Bearer <jwt_token>
```

## Migration Guide

### Running the Migration

1. **Backup your database** before running any migrations.

2. **Run the migration script:**
```bash
PGPASSWORD=your_password psql -h localhost -p 5432 -U xiangxin -d xiangxin_guardrails \
  -f backend/database/migrations/add_multi_api_key_support.sql
```

3. **Verify migration:**
```bash
PGPASSWORD=your_password psql -h localhost -p 5432 -U xiangxin -d xiangxin_guardrails \
  -c "SELECT COUNT(*) FROM tenant_api_keys;"
```

You should see one API key per tenant (migrated from the legacy api_key column).

### What the Migration Does

1. Creates `tenant_api_keys` table
2. Creates `api_key_blacklist_associations` table
3. Updates `risk_type_config` table schema
4. Migrates existing tenant API keys to the new table
5. Links existing risk configs to default API keys

### Rollback

If you need to rollback:
```bash
PGPASSWORD=your_password psql -h localhost -p 5432 -U xiangxin -d xiangxin_guardrails \
  -f backend/database/migrations/rollback_multi_api_key_support.sql
```

**Warning:** Rollback will delete all non-default API keys!

## Backward Compatibility

The system maintains backward compatibility:

1. **Legacy API key column:** The `tenants.api_key` column is kept but deprecated
2. **Automatic lookup:** `get_user_by_api_key()` checks both new and old tables
3. **Default key migration:** Existing API keys are migrated as "Default Key"

## Usage Examples

### Python Client

```python
import requests

# Using different API keys for different apps
PROD_API_KEY = "sk-xxai-prod-key..."
TEST_API_KEY = "sk-xxai-test-key..."

# Production detection (strict)
response = requests.post(
    "http://localhost:5001/v1/guardrails",
    headers={"Authorization": f"Bearer {PROD_API_KEY}"},
    json={
        "model": "Xiangxin-Guardrails-Text",
        "messages": [{"role": "user", "content": "test content"}]
    }
)

# Test detection (lenient)
response = requests.post(
    "http://localhost:5001/v1/guardrails",
    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    json={
        "model": "Xiangxin-Guardrails-Text",
        "messages": [{"role": "user", "content": "test content"}]
    }
)
```

### Managing API Keys via API

```python
import requests

JWT_TOKEN = "your-jwt-token"
BASE_URL = "http://localhost:5000"

# Create a new API key
response = requests.post(
    f"{BASE_URL}/api/v1/api-keys",
    headers={"Authorization": f"Bearer {JWT_TOKEN}"},
    json={
        "name": "Mobile App Key",
        "risk_config_id": 2,
        "is_default": False
    }
)
new_key = response.json()
print(f"Created key: {new_key['api_key']}")

# List all keys
response = requests.get(
    f"{BASE_URL}/api/v1/api-keys",
    headers={"Authorization": f"Bearer {JWT_TOKEN}"}
)
keys = response.json()
print(f"Total keys: {keys['total']}")
```

## Best Practices

### 1. Naming Convention
Use descriptive names for API keys:
- ✅ "Production Web App"
- ✅ "Development Environment"
- ✅ "Mobile iOS App"
- ❌ "Key 1"
- ❌ "Test"

### 2. Key Rotation
Regularly rotate API keys for security:
1. Create a new key with the same configuration
2. Update your application to use the new key
3. Delete the old key after verification

### 3. Default Key
Always maintain one default key:
- Used for platform operations
- Cannot be deleted until another key is set as default

### 4. Configuration Management
Create reusable risk configs:
- "Strict Production" (all risk types)
- "Lenient Development" (critical risks only)
- "Customer Facing" (no S1, no S10)

## Troubleshooting

### Issue: Cannot delete API key
**Error:** "Cannot delete the only API key"
**Solution:** Create another key first, then delete

### Issue: Cannot delete default key
**Error:** "Cannot delete the default API key"
**Solution:** Set another key as default first

### Issue: API key not working after migration
**Check:**
1. Verify key exists in `tenant_api_keys` table
2. Check `is_active` flag is true
3. Verify tenant is active and verified

### Issue: Risk config not applied
**Check:**
1. Verify API key has `risk_config_id` set
2. Check risk config exists and belongs to tenant
3. Verify risk type is enabled in config

## Future Enhancements

### Planned Features
1. **Ban Policy per API Key** - Different ban policies for different keys
2. **Rate Limit per API Key** - Independent rate limits
3. **Whitelist Associations** - Associate whitelists with API keys
4. **Key Scopes** - Restrict keys to specific operations (detect input only, etc.)
5. **Key Expiration** - Set expiration dates for keys
6. **Usage Analytics** - Detailed usage stats per key

## Security Considerations

1. **API Key Storage:** API keys are stored in plain text in the database (same as before)
2. **API Key Format:** Keys use `sk-xxai-` prefix with 56 random characters
3. **Key Regeneration:** Old keys are immediately invalidated
4. **Access Control:** Users can only manage their own API keys
5. **Audit Trail:** `last_used_at` tracks key usage

## Support

For questions or issues:
- GitHub Issues: https://github.com/xiangxinai/xiangxin-guardrails/issues
- Documentation: Check CLAUDE.md for additional context
