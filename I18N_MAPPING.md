# Internationalization Field Mapping

## Overview
This document maps all Chinese fields to their English equivalents for the internationalization process.

## API Response Fields

### Risk Levels (风险等级)
| Chinese | English | Value |
|---------|---------|-------|
| 无风险 | no_risk | no_risk |
| 低风险 | low_risk | low_risk |
| 中风险 | medium_risk | medium_risk |
| 高风险 | high_risk | high_risk |

### Suggested Actions (建议操作)
| Chinese | English | Value |
|---------|---------|-------|
| 通过 | pass | pass |
| 阻断 | block | block |
| 拒答 | reject | reject |
| 代答 | replace | replace |
| 放行 | allow | allow |

### Risk Categories (风险类别)
| Code | Chinese | English |
|------|---------|---------|
| S1 | 一般政治话题 | General Political Topics |
| S2 | 敏感政治话题 | Sensitive Political Topics |
| S3 | 损害国家形象 | Damage to National Image |
| S4 | 伤害未成年人 | Harm to Minors |
| S5 | 暴力犯罪 | Violent Crime |
| S6 | 违法犯罪 | Illegal Activities |
| S7 | 色情 | Pornography |
| S8 | 歧视内容 | Discriminatory Content |
| S9 | 提示词攻击 | Prompt Injection |
| S10 | 辱骂 | Insults |
| S11 | 侵犯个人隐私 | Privacy Violation |
| S12 | 商业违法违规 | Business Violations |

### Sensitivity Levels (敏感度等级)
| Chinese | English | Value |
|---------|---------|-------|
| 高 | high | high |
| 中 | medium | medium |
| 低 | low | low |

### Detection Types (检测类型)
| Chinese | English |
|---------|---------|
| 提示词攻击 | Security (Prompt Injection) |
| 内容合规 | Compliance |
| 数据泄漏 | Data Leakage |

### Data Entity Types (数据实体类型)
| Chinese | English |
|---------|---------|
| 身份证号 | ID_CARD_NUMBER |
| 银行卡号 | BANK_CARD_NUMBER |
| 电话号码 | PHONE_NUMBER |
| 邮箱地址 | EMAIL_ADDRESS |

### Anonymization Methods (脱敏方法)
| Chinese | English |
|---------|---------|
| 替换 | replace |
| 掩码 | mask |
| 哈希 | hash |
| 加密 | encrypt |
| 重排 | shuffle |
| 随机替换 | random |

## Database Schema Changes

### DetectionResult Table
- `suggest_action`: '通过' → 'pass', '拒答' → 'reject', '代答' → 'replace'
- `security_risk_level`: '无风险' → 'no_risk', '低风险' → 'low_risk', '中风险' → 'medium_risk', '高风险' → 'high_risk'
- `compliance_risk_level`: Same as security_risk_level
- `data_risk_level`: Same as security_risk_level
- `sensitivity_level`: '高' → 'high', '中' → 'medium', '低' → 'low'

### ResponseTemplate Table
- `risk_level`: '无风险' → 'no_risk', '低风险' → 'low_risk', '中风险' → 'medium_risk', '高风险' → 'high_risk'

### DataSecurityEntityType Table
- `risk_level`: '低' → 'low', '中' → 'medium', '高' → 'high'

## Code Constants to Update

### backend/services/guardrail_service.py
```python
# Old
RISK_LEVEL_MAPPING = {
    'S2': '高风险',
    'S3': '高风险',
    # ...
}

# New
RISK_LEVEL_MAPPING = {
    'S2': 'high_risk',
    'S3': 'high_risk',
    # ...
}
```

### Category Names
```python
# Old
CATEGORY_NAMES = {
    'S1': '一般政治话题',
    # ...
}

# New
CATEGORY_NAMES = {
    'S1': 'General Political Topics',
    # ...
}
```

## Frontend i18n Structure

### Language Files Location
- `/frontend/src/locales/en.json` - English translations
- `/frontend/src/locales/zh.json` - Chinese translations

### Key Naming Convention
Use dot notation for hierarchical structure:
- `risk.level.no_risk` → "No Risk" (EN) / "无风险" (ZH)
- `risk.level.low_risk` → "Low Risk" (EN) / "低风险" (ZH)
- `action.pass` → "Pass" (EN) / "通过" (ZH)
- `category.S1` → "General Political Topics" (EN) / "一般政治话题" (ZH)

## Migration Strategy

1. **Phase 1**: Update backend API responses to use English values
2. **Phase 2**: Add database migration to update existing records
3. **Phase 3**: Set up frontend i18n and create translation files
4. **Phase 4**: Update all code comments to English
5. **Phase 5**: Update documentation

## Backward Compatibility

During transition period:
- Accept both Chinese and English values in API requests
- Map old Chinese values to new English values internally
- Gradually deprecate Chinese values

## Testing Checklist

- [ ] API responses return English field values
- [ ] Frontend displays correct translations based on locale
- [ ] IP-based language detection works correctly
- [ ] All existing functionality works with new English fields
- [ ] Database migration completes successfully
