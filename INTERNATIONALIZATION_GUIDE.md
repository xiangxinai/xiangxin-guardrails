# Internationalization (i18n) Guide

## Overview

Xiangxin AI Guardrails now supports full internationalization with English as the primary language and Chinese as a supported locale. The system automatically detects user language based on their IP address location.

## Language Detection Priority

The system uses the following priority order for language detection:

1. **URL Query Parameter**: `?lng=en` or `?lng=zh`
2. **LocalStorage**: Previously saved user preference
3. **IP Geolocation**: Automatic detection based on user's IP address
   - Chinese IPs → Chinese (zh)
   - All other IPs → English (en)
4. **Browser Language**: Falls back to browser language setting
5. **Default**: English (en)

## Backend API Changes

### Field Values (All in English)

All API responses now use English field values:

#### Risk Levels
- `no_risk` - No Risk
- `low_risk` - Low Risk
- `medium_risk` - Medium Risk
- `high_risk` - High Risk

#### Suggested Actions
- `pass` - Pass through without intervention
- `reject` - Reject and block the request
- `replace` - Replace with suggested answer
- `block` - Block the request
- `allow` - Allow the request

#### Sensitivity Levels
- `high` - High sensitivity
- `medium` - Medium sensitivity
- `low` - Low sensitivity

#### Risk Categories
- `S1` - General Political Topics
- `S2` - Sensitive Political Topics
- `S3` - Damage to National Image
- `S4` - Harm to Minors
- `S5` - Violent Crime
- `S6` - Illegal Activities
- `S7` - Pornography
- `S8` - Discriminatory Content
- `S9` - Prompt Injection
- `S10` - Insults
- `S11` - Privacy Violation
- `S12` - Business Violations

### Database Migration

To migrate existing data from Chinese to English values:

```bash
# Option 1: Using Python script (recommended)
cd backend
python database/migrations/migrate_to_english.py

# Option 2: Using SQL script directly
psql -h localhost -p 54321 -U xiangxin -d xiangxin_guardrails \
  -f database/migrations/migrate_to_english_fields.sql
```

## Frontend i18n Implementation

### Basic Usage

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('dashboard.title')}</h1>
      <p>{t('dashboard.totalRequests')}</p>
    </div>
  );
}
```

### Translating Backend Values

Use the i18n mapper utilities to translate backend English values:

```typescript
import { useTranslation } from 'react-i18next';
import {
  translateRiskLevel,
  translateAction,
  translateCategory
} from '@/utils/i18nMapper';

function ResultDisplay({ result }) {
  const { t } = useTranslation();

  return (
    <div>
      <Tag>{translateRiskLevel(result.risk_level, t)}</Tag>
      <Badge>{translateAction(result.suggest_action, t)}</Badge>
      <span>{translateCategory(result.category, t)}</span>
    </div>
  );
}
```

### Adding Language Switcher

The `LanguageSwitcher` component is available for use in any part of the application:

```typescript
import LanguageSwitcher from '@/components/LanguageSwitcher/LanguageSwitcher';

function Header() {
  return (
    <div>
      <LanguageSwitcher />
    </div>
  );
}
```

### Adding New Translations

1. Add translation keys to both language files:

**frontend/src/locales/en.json**:
```json
{
  "myFeature": {
    "title": "My Feature",
    "description": "This is my feature"
  }
}
```

**frontend/src/locales/zh.json**:
```json
{
  "myFeature": {
    "title": "我的功能",
    "description": "这是我的功能"
  }
}
```

2. Use in components:
```typescript
const { t } = useTranslation();
<h1>{t('myFeature.title')}</h1>
```

## Adding New Languages

To add support for a new language (e.g., Japanese):

1. Create language file: `frontend/src/locales/ja.json`

2. Update `frontend/src/i18n.ts`:
```typescript
import jaTranslations from './locales/ja.json';

i18n.init({
  resources: {
    en: { translation: enTranslations },
    zh: { translation: zhTranslations },
    ja: { translation: jaTranslations }  // Add here
  },
  // ...
});
```

3. Update language detector: `frontend/src/utils/languageDetector.ts`
```typescript
// Add country code mapping for Japan
if (countryCode.toUpperCase() === 'JP') {
  return 'ja';
}
```

4. Update language switcher with new option

## Testing i18n

### Test Language Switching

1. **Via URL**:
   - English: `http://localhost:5173/platform?lng=en`
   - Chinese: `http://localhost:5173/platform?lng=zh`

2. **Via Language Switcher**:
   - Click the language switcher in the header
   - Select desired language

3. **Clear localStorage** to test IP-based detection:
```javascript
localStorage.removeItem('i18nextLng');
window.location.reload();
```

### Verify Backend Integration

```bash
# Test detection API with English response
curl -X POST "http://localhost:5001/v1/guardrails" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Xiangxin-Guardrails-Text",
    "messages": [{"role": "user", "content": "test content"}]
  }'

# Should return:
# {
#   "id": "guardrails-xxx",
#   "overall_risk_level": "no_risk",  // English value
#   "suggest_action": "pass",          // English value
#   ...
# }
```

## Best Practices

1. **Always use translation keys** instead of hardcoded text:
   ```typescript
   // ❌ Bad
   <Button>登录</Button>

   // ✅ Good
   <Button>{t('login.loginButton')}</Button>
   ```

2. **Use mapper utilities** for backend values:
   ```typescript
   // ❌ Bad
   <Tag>{riskLevel}</Tag>

   // ✅ Good
   <Tag>{translateRiskLevel(riskLevel, t)}</Tag>
   ```

3. **Organize translation keys** hierarchically:
   ```json
   {
     "feature": {
       "section": {
         "item": "Translation"
       }
     }
   }
   ```

4. **Keep backend values in English** - only frontend displays translated values

5. **Test both languages** before deploying new features

## Troubleshooting

### Language not changing

1. Clear browser localStorage and cookies
2. Check browser console for errors
3. Verify language files are properly formatted JSON
4. Ensure i18n is initialized before app renders

### IP detection not working

1. Check if geolocation services are accessible
2. Verify network/firewall settings
3. Check browser console for API errors
4. Fallback will use browser language or default to English

### Missing translations

1. Check translation key exists in both `en.json` and `zh.json`
2. Verify key path is correct (case-sensitive)
3. Reload page after adding new translations
4. Check browser console for missing key warnings

## API Reference

### Translation Hook
```typescript
const { t, i18n } = useTranslation();
t(key: string): string           // Translate a key
i18n.language: string            // Current language
i18n.changeLanguage(lng: string) // Change language
```

### Mapper Utilities
```typescript
translateRiskLevel(value: string, t: TFunction): string
translateAction(value: string, t: TFunction): string
translateSensitivity(value: string, t: TFunction): string
translateCategory(value: string, t: TFunction): string
getRiskLevelColor(riskLevel: string): string
getActionColor(action: string): string
```

### Language Detector
```typescript
detectLanguageByIP(): Promise<string>
initializeLanguage(): Promise<string>
changeLanguage(lang: string): void
```

## Migration Checklist

- [x] Backend field values converted to English
- [x] Database migration scripts created
- [x] Frontend i18n framework set up
- [x] Language files created (en, zh)
- [x] IP-based language detection implemented
- [x] Language switcher component created
- [x] Mapper utilities for backend values created
- [ ] All frontend components updated to use i18n
- [ ] Documentation updated to English
- [ ] Testing completed

## Support

For questions or issues related to internationalization:
- Check this guide first
- Review example code in `frontend/src/components/LanguageSwitcher`
- Check translation mapping in `I18N_MAPPING.md`
- Report issues on GitHub
