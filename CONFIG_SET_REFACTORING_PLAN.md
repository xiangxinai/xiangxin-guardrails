# Configuration Set (ConfigSet) Refactoring Implementation Plan

## Executive Summary

This document outlines the plan to refactor the protection configuration center to use a **ConfigSet-centric** approach, where each API Key can be associated with different configuration sets containing all protection settings.

## Current Status Analysis

### ✅ Already Implemented (Backend)

1. **Database Structure** - Mostly complete
   - `RiskTypeConfig` table serves as ConfigSet with:
     - Risk type switches (s1-s12_enabled)
     - Sensitivity thresholds
     - name, description, is_default fields
   - All configuration tables have `template_id` foreign key:
     - `Blacklist.template_id`
     - `Whitelist.template_id`
     - `ResponseTemplate.template_id`
     - `KnowledgeBase.template_id`
     - `DataSecurityEntityType.template_id`
     - `BanPolicy.template_id`
   - `TenantApiKey.template_id` for binding API keys to config sets

2. **Service Layer** - Mostly complete
   - `RiskConfigService` with CRUD operations
   - `clone_risk_config()` method
   - `get_config_associations()` method
   - Support for multiple config sets per tenant

3. **API Layer** - Partially complete
   - API Key management supports `template_id`
   - Risk config CRUD endpoints exist

### ❌ Needs Implementation/Refactoring

1. **Backend**
   - Ensure all configuration APIs support template_id filtering
   - Detection service needs to load config based on API key's template_id
   - Add config set selection/management endpoints

2. **Frontend** - Major refactoring needed
   - Redesign Config.tsx routing structure
   - Add ConfigSet selector to all config sub-pages
   - Update API Key management to show/edit config set bindings
   - Improve ProtectionTemplateManagement UI
   - Enhance ConfigSetDetail page

---

## Implementation Plan

### Phase 1: Backend Enhancements

#### 1.1 Database Verification (COMPLETED)
- ✅ Verify all configuration tables have `template_id` field
- ✅ Ensure proper foreign key relationships

#### 1.2 Backend API Enhancements

**Files to modify:**
- `backend/routers/risk_config_api.py`
- `backend/routers/*.py` (all config-related routers)
- `backend/services/guardrail_service.py`

**Changes needed:**

1. **Config Set Management API** (`risk_config_api.py`):
   ```python
   # Already exists:
   GET  /api/v1/config/risk-configs          # List all config sets
   GET  /api/v1/config/risk-configs/{id}     # Get config set details
   POST /api/v1/config/risk-configs          # Create config set
   PUT  /api/v1/config/risk-configs/{id}     # Update config set
   DELETE /api/v1/config/risk-configs/{id}   # Delete config set
   POST /api/v1/config/risk-configs/{id}/clone  # Clone config set
   GET  /api/v1/config/risk-configs/{id}/associations  # Get associations
   ```

2. **Configuration Sub-resource APIs** - Add `template_id` query parameter:
   ```python
   # Blacklist API
   GET /api/v1/config/blacklists?template_id={id}
   POST /api/v1/config/blacklists  # Body includes template_id

   # Whitelist API
   GET /api/v1/config/whitelists?template_id={id}
   POST /api/v1/config/whitelists  # Body includes template_id

   # Similar for response_templates, knowledge_bases, data_security, ban_policies
   ```

3. **Detection Service** (`guardrail_service.py`):
   - Modify to accept `template_id` parameter
   - Load configuration based on API key's template_id
   - Cache configurations by template_id

#### 1.3 Detection Service Integration

**File:** `backend/services/guardrail_service.py`

**Changes:**
```python
async def detect_guardrail(
    api_key: str,
    messages: List[Dict],
    # ... other params
):
    # 1. Get API key record
    api_key_record = get_api_key_from_db(api_key)
    template_id = api_key_record.template_id

    # 2. Load config set by template_id
    config = load_config_by_template_id(template_id)

    # 3. Load associated resources
    blacklists = load_blacklists(template_id)
    whitelists = load_whitelists(template_id)
    data_security_rules = load_data_security(template_id)
    ban_policies = load_ban_policies(template_id)

    # 4. Perform detection using loaded configs
    # ...
```

---

### Phase 2: Frontend Refactoring

#### 2.1 Routing Structure Redesign

**Current structure:**
```
/config
  ├─ /protection-templates
  ├─ /risk-types
  ├─ /sensitivity-thresholds
  ├─ /data-security
  ├─ /ban-policy
  ├─ /blacklist
  ├─ /whitelist
  ├─ /responses
  └─ /knowledge-bases
```

**New structure:**
```
/config
  ├─ /config-sets                    # List of config sets
  ├─ /config-set/:id                 # Config set detail (with collapsible modules)
  │   ├─ Basic Info
  │   ├─ Risk Types
  │   ├─ Sensitivity Thresholds
  │   ├─ Data Security (DLP)
  │   ├─ Ban Policy
  │   ├─ Blacklist
  │   ├─ Whitelist
  │   ├─ Response Templates
  │   └─ Knowledge Bases
  └─ /api-keys                       # API Key management (with config set binding)
```

#### 2.2 Main Config Page Refactoring

**File:** `frontend/src/pages/Config/Config.tsx`

**New design:**
```tsx
const Config: React.FC = () => {
  const location = useLocation();

  // Route to ConfigSetDetail if viewing a specific config set
  if (location.pathname.includes('/config-set/')) {
    return <ConfigSetDetail />;
  }

  // Default: Show ProtectionTemplateManagement (ConfigSet list)
  return (
    <div>
      <h2>{t('config.title')}</h2>
      <Tabs
        activeKey={getActiveKey()}
        items={[
          {
            key: 'config-sets',
            label: t('config.configSets'),
            children: <ProtectionTemplateManagement />
          },
          {
            key: 'api-keys',
            label: t('config.apiKeys'),
            children: <ApiKeys />
          }
        ]}
        onChange={handleTabChange}
      />
    </div>
  );
};
```

#### 2.3 ConfigSetDetail Page Enhancement

**File:** `frontend/src/pages/Config/ConfigSetDetail.tsx`

**Design:**
- **Top section**: Config set basic info (name, description, is_default)
- **Collapsible sections** (Ant Design Collapse component):
  1. ⚙️ Risk Detection Config
  2. 🎚️ Sensitivity Thresholds
  3. 🔒 Data Security (DLP)
  4. 🚫 Ban Policy
  5. ⚫ Blacklist
  6. ⚪ Whitelist
  7. 📚 Response Templates
  8. 📘 Knowledge Bases
  9. 🔑 Associated API Keys (read-only list)

**Features:**
- Edit button for each section
- Inline editing with form validation
- Auto-save or explicit save button
- Visual feedback for changes

#### 2.4 ProtectionTemplateManagement Enhancement

**File:** `frontend/src/pages/Config/ProtectionTemplateManagement.tsx`

**Features to add:**
1. Clear CTA for creating new config set
2. Template selection (e.g., "Default", "Enterprise", "Strict")
3. Table showing:
   - Name
   - Description
   - Is Default (badge)
   - # of API Keys using it
   - # of Associated resources (blacklists, etc.)
   - Actions: View, Edit, Clone, Delete
4. Search and filter

#### 2.5 API Key Management Page

**File:** `frontend/src/pages/Config/ApiKeys.tsx`

**Enhancements:**
1. Add "Config Set" column showing which config set the key is bound to
2. In create/edit modal, add Config Set selector dropdown
3. Show config set name in key details
4. Allow changing config set binding
5. Visual indicator for default key

---

### Phase 3: Configuration Sub-Pages Refactoring

All configuration sub-pages need to support operating within a selected config set context.

#### 3.1 Add ConfigSet Selector Component

**New file:** `frontend/src/components/ConfigSetSelector.tsx`

```tsx
interface ConfigSetSelectorProps {
  value?: number;
  onChange: (configSetId: number) => void;
  allowCreate?: boolean;
}

const ConfigSetSelector: React.FC<ConfigSetSelectorProps> = ({
  value,
  onChange,
  allowCreate = false
}) => {
  const [configSets, setConfigSets] = useState([]);

  // Load config sets
  // Show select dropdown
  // Option to create new if allowCreate=true

  return (
    <Select
      value={value}
      onChange={onChange}
      options={configSets.map(cs => ({
        label: cs.name,
        value: cs.id
      }))}
      placeholder="Select a config set"
    />
  );
};
```

#### 3.2 Modify All Config Sub-Pages

**Files to modify:**
- `BlacklistManagement.tsx`
- `WhitelistManagement.tsx`
- `ResponseTemplateManagement.tsx`
- `KnowledgeBaseManagement.tsx`
- `RiskTypeManagement.tsx`
- `SensitivityThresholdManagement.tsx`
- `DataSecurity.tsx`
- `BanPolicy.tsx`

**Changes for each:**
1. Add ConfigSetSelector at the top
2. Store selected config set ID in state
3. Filter API calls by `template_id`
4. When creating new items, include `template_id` in request body
5. Show config set name in breadcrumbs or page title

**Example for BlacklistManagement.tsx:**
```tsx
const BlacklistManagement: React.FC = () => {
  const [selectedConfigSet, setSelectedConfigSet] = useState<number>();

  useEffect(() => {
    if (selectedConfigSet) {
      loadBlacklists(selectedConfigSet);
    }
  }, [selectedConfigSet]);

  const loadBlacklists = async (templateId: number) => {
    const response = await api.get(`/api/v1/config/blacklists?template_id=${templateId}`);
    // ...
  };

  return (
    <div>
      <ConfigSetSelector
        value={selectedConfigSet}
        onChange={setSelectedConfigSet}
      />
      {/* Rest of the component */}
    </div>
  );
};
```

---

### Phase 4: User Experience Enhancements

#### 4.1 Quick Actions
- "Duplicate this config set" button
- "Create API key for this config" button
- "Switch to another config set" quick dropdown

#### 4.2 Visual Indicators
- Badge for default config set
- Tag showing # of API keys using each config
- Active/inactive status indicators
- Change indicators (unsaved changes)

#### 4.3 Onboarding
- First-time user flow: Create default config set automatically
- Template library: Pre-configured templates for common scenarios
  - "Strict Security" - All checks enabled, high sensitivity
  - "Balanced" - Default settings
  - "Development" - Relaxed settings for testing

#### 4.4 Validation & Constraints
- Prevent deletion of config set if API keys are using it
- Prevent deletion of last config set
- Warn when modifying default config set
- Confirm before major changes

---

### Phase 5: Testing & Validation

#### 5.1 Backend Testing
- [ ] Test config set CRUD operations
- [ ] Test template_id filtering in all config APIs
- [ ] Test API key config set binding
- [ ] Test detection service loads correct config by API key
- [ ] Test clone config set functionality
- [ ] Test config set associations endpoint

#### 5.2 Frontend Testing
- [ ] Test config set list view
- [ ] Test config set detail page
- [ ] Test creating/editing config sets
- [ ] Test cloning config sets
- [ ] Test API key management with config set binding
- [ ] Test all config sub-pages with config set selector
- [ ] Test navigation between pages
- [ ] Test default config set handling

#### 5.3 Integration Testing
- [ ] Test detection API with different API keys
- [ ] Verify correct config loaded based on API key
- [ ] Test switching between config sets
- [ ] Test creating API key with config set
- [ ] Test modifying config set affects detection

#### 5.4 Edge Cases
- [ ] Deleting config set with dependencies
- [ ] Switching default config set
- [ ] API key with null template_id (fallback to default)
- [ ] Concurrent modifications to same config set
- [ ] Config set name conflicts

---

## Migration Strategy

### For Existing Users

1. **Database Migration** (if needed):
   - Ensure all existing tenants have at least one default config set
   - Migrate existing API keys to point to default config set
   - Migrate existing configurations to be associated with default config set

2. **Backward Compatibility**:
   - Support API keys without template_id (use default config)
   - Support old API endpoints (redirect to new config set endpoints)

3. **Data Migration Script**:
   ```sql
   -- Ensure all tenants have a default config set
   INSERT INTO risk_type_config (tenant_id, name, is_default, ...)
   SELECT id, 'Default Config', true, ...
   FROM tenants
   WHERE id NOT IN (SELECT tenant_id FROM risk_type_config WHERE is_default = true);

   -- Update API keys to use default config set
   UPDATE tenant_api_keys
   SET template_id = (
     SELECT id FROM risk_type_config
     WHERE tenant_id = tenant_api_keys.tenant_id
     AND is_default = true
     LIMIT 1
   )
   WHERE template_id IS NULL;

   -- Update existing configurations to use default config set
   UPDATE blacklist
   SET template_id = (
     SELECT id FROM risk_type_config
     WHERE tenant_id = blacklist.tenant_id
     AND is_default = true
     LIMIT 1
   )
   WHERE template_id IS NULL;

   -- Repeat for whitelist, response_templates, knowledge_bases, etc.
   ```

---

## Implementation Timeline

### Week 1: Backend Foundation
- ✅ Day 1-2: Database verification (COMPLETED)
- Day 2-3: Backend API enhancements
- Day 4-5: Detection service integration

### Week 2: Frontend Core
- Day 1-2: Config.tsx routing refactoring
- Day 3-4: ConfigSetDetail page enhancement
- Day 5: ProtectionTemplateManagement enhancement

### Week 3: Frontend Sub-Pages
- Day 1: ConfigSetSelector component
- Day 2-3: Modify all config sub-pages
- Day 4-5: API Key management page

### Week 4: Polish & Testing
- Day 1-2: UX enhancements
- Day 3-4: Testing & bug fixes
- Day 5: Documentation & deployment

---

## Success Criteria

1. ✅ Each tenant can create multiple config sets
2. ✅ Each API key is associated with a config set
3. ✅ Detection service correctly loads config based on API key
4. ✅ All configuration resources (blacklist, etc.) are scoped to config sets
5. ✅ UI provides intuitive config set management
6. ✅ Existing data is migrated without loss
7. ✅ No breaking changes to public APIs

---

## Rollback Plan

If issues arise during deployment:
1. **Database**: Keep old data intact, new columns are nullable
2. **Backend**: Feature flag to disable config set mode
3. **Frontend**: Deploy old version from git tag
4. **API**: Old endpoints remain functional

---

## Open Questions

1. Should we allow sharing config sets between tenants? (Answer: No, for now)
2. Should we version config sets? (Answer: Future enhancement)
3. Maximum number of config sets per tenant? (Answer: No limit initially, monitor usage)
4. Should we support config set templates/marketplace? (Answer: Future enhancement)

---

## Appendix: Key Files Reference

### Backend
- `backend/database/models.py` - Data models
- `backend/services/risk_config_service.py` - Config set service
- `backend/services/guardrail_service.py` - Detection service
- `backend/routers/risk_config_api.py` - Config set API
- `backend/routers/api_keys.py` - API key management

### Frontend
- `frontend/src/pages/Config/Config.tsx` - Main config page
- `frontend/src/pages/Config/ProtectionTemplateManagement.tsx` - Config set list
- `frontend/src/pages/Config/ConfigSetDetail.tsx` - Config set detail
- `frontend/src/pages/Config/ApiKeys.tsx` - API key management
- `frontend/src/pages/Config/*Management.tsx` - Individual config pages

---

## Notes

- The term "Protection Template" and "Config Set" are used interchangeably
- The database uses `template_id` to reference config sets (via `RiskTypeConfig.id`)
- All changes maintain backward compatibility
- Focus on user experience and intuitive navigation

---

**Document Version:** 1.0
**Last Updated:** 2025-10-10
**Status:** Planning Complete - Ready for Implementation
