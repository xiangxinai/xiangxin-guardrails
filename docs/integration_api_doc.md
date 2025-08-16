# 象信AI安全护栏 - API接口文档

## 概述

本文档详细描述象信AI安全护栏系统的所有API接口，包括认证方式、请求格式、响应格式和错误处理。

## 基础信息

- **API版本**: v1.0
- **基础URL**: `http://your-domain.com`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

所有API请求都需要在请求头中包含JWT token：

```http
Authorization: Bearer <jwt_token>
```

### JWT Token格式

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "sub": "550e8400-e29b-41d4-a716-446655440001",
  "email": "user@example.com", 
  "role": "user",
  "exp": 1234567890
}
```

## 接口列表

### 1. 内容检测接口

#### POST /v1/guardrails

**描述**: 检测内容安全性

**请求**:
```http
POST /v1/guardrails
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "用户输入的内容"
    }
  ]
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| messages | array | 是 | 消息列表 |
| messages[].role | string | 是 | 消息角色: "user", "assistant", "system" |
| messages[].content | string | 是 | 消息内容 |

**响应**:
```json
{
  "id": "guardrails-abc123",
  "result": {
    "compliance": {
      "risk_level": "中风险",
      "categories": ["一般政治话题"]
    },
    "security": {
      "risk_level": "无风险",
      "categories": []
    }
  },
  "overall_risk_level": "中风险",
  "suggest_action": "代答", 
  "suggest_answer": "抱歉，我不能回答涉及政治话题的问题。"
}
```

**响应字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 请求唯一标识 |
| result | object | 检测结果 |
| result.compliance | object | 内容合规检测结果 |
| result.security | object | 安全检测结果 |
| overall_risk_level | string | 总体风险等级: "无风险", "低风险", "中风险", "高风险" |
| suggest_action | string | 建议动作: "通过", "代答", "阻断" |
| suggest_answer | string | 建议回答（当suggest_action为"代答"或"阻断"时） |

#### GET /v1/guardrails/health

**描述**: 检测服务健康检查

**响应**:
```json
{
  "status": "healthy",
  "service": "detection_guardrails",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /v1/guardrails/models

**描述**: 获取可用模型列表

**响应**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "Xiangxin-Guardrails-Text",
      "object": "model",
      "created": 1640995200,
      "owned_by": "xiangxinai"
    }
  ]
}
```

### 2. 黑名单管理接口

#### GET /config/blacklist

**描述**: 获取当前用户的黑名单列表

**响应**:
```json
[
  {
    "id": 1,
    "name": "敏感词列表",
    "keywords": ["敏感词1", "敏感词2"],
    "description": "用户专属敏感词过滤",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /config/blacklist

**描述**: 创建新的黑名单

**请求**:
```json
{
  "name": "敏感词列表",
  "keywords": ["敏感词1", "敏感词2", "敏感词3"],
  "description": "用户专属敏感词过滤",
  "is_active": true
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 黑名单名称（最大100字符） |
| keywords | array | 是 | 关键词列表（每个关键词最大50字符） |
| description | string | 否 | 描述信息（最大500字符） |
| is_active | boolean | 否 | 是否启用（默认true） |

**响应**:
```json
{
  "success": true,
  "message": "Blacklist created successfully"
}
```

#### PUT /config/blacklist/{blacklist_id}

**描述**: 更新指定的黑名单

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| blacklist_id | integer | 是 | 黑名单ID |

**请求体**: 与创建黑名单相同

**响应**:
```json
{
  "success": true,
  "message": "Blacklist updated successfully"
}
```

#### DELETE /config/blacklist/{blacklist_id}

**描述**: 删除指定的黑名单

**响应**:
```json
{
  "success": true,
  "message": "Blacklist deleted successfully"
}
```

### 3. 白名单管理接口

白名单接口与黑名单接口结构完全相同，仅将路径中的 `blacklist` 替换为 `whitelist`：

- `GET /config/whitelist` - 获取白名单列表
- `POST /config/whitelist` - 创建白名单
- `PUT /config/whitelist/{whitelist_id}` - 更新白名单
- `DELETE /config/whitelist/{whitelist_id}` - 删除白名单

### 4. 代答模板管理接口

#### GET /config/responses

**描述**: 获取当前用户的代答模板列表

**响应**:
```json
[
  {
    "id": 1,
    "category": "S1",
    "risk_level": "中风险",
    "template_content": "抱歉，我不能回答涉及政治话题的问题。",
    "is_default": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /config/responses

**描述**: 创建新的代答模板

**请求**:
```json
{
  "category": "S1",
  "risk_level": "中风险",
  "template_content": "抱歉，我不能回答涉及政治话题的问题。",
  "is_default": true,
  "is_active": true
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 是 | 风险类别代码 |
| risk_level | string | 是 | 风险等级 |
| template_content | string | 是 | 模板内容（最大1000字符） |
| is_default | boolean | 否 | 是否为默认模板（默认true） |
| is_active | boolean | 否 | 是否启用（默认true） |

**风险类别代码**:
| 代码 | 名称 | 风险等级 |
|------|------|----------|
| S1 | 一般政治话题 | 中风险 |
| S2 | 敏感政治话题 | 高风险 |
| S3 | 损害国家形象 | 高风险 |
| S4 | 伤害未成年人 | 中风险 |
| S5 | 暴力犯罪 | 高风险 |
| S6 | 违法犯罪 | 中风险 |
| S7 | 色情 | 中风险 |
| S8 | 歧视内容 | 低风险 |
| S9 | 提示词攻击 | 高风险 |
| S10 | 辱骂 | 低风险 |
| S11 | 侵犯个人隐私 | 低风险 |
| S12 | 商业违法违规 | 低风险 |
| default | 默认模板 | 通用 |

#### PUT /config/responses/{template_id}

**描述**: 更新指定的代答模板

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| template_id | integer | 是 | 模板ID |

#### DELETE /config/responses/{template_id}

**描述**: 删除指定的代答模板

### 5. 系统信息接口

#### GET /config/system-info

**描述**: 获取系统信息

**响应**:
```json
{
  "support_email": "wanglei@xiangxinai.cn",
  "app_name": "Xiangxin Guardrails",
  "app_version": "1.0.0"
}
```

#### GET /config/cache-info

**描述**: 获取缓存状态信息

**响应**:
```json
{
  "status": "success",
  "data": {
    "keyword_cache": {
      "users_with_blacklists": 10,
      "users_with_whitelists": 5,
      "blacklist_lists": 25,
      "blacklist_keywords": 150,
      "whitelist_lists": 8,
      "whitelist_keywords": 50,
      "last_refresh": 1234567890,
      "cache_age_seconds": 300
    },
    "template_cache": {
      "users": 10,
      "templates": 30,
      "last_refresh": 1234567890,
      "cache_age_seconds": 600
    }
  }
}
```

#### POST /config/cache/refresh

**描述**: 手动刷新缓存

**响应**:
```json
{
  "status": "success",
  "message": "All caches refreshed successfully"
}
```

### 6. 服务健康检查

#### GET /health

**描述**: 服务健康检查

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "detection" 
}
```

#### GET /

**描述**: 服务基本信息

**响应**:
```json
{
  "name": "Xiangxin Guardrails - Detection Service",
  "version": "1.0.0",
  "status": "running",
  "service_type": "detection",
  "model_api_url": "http://localhost:58002/v1",
  "workers": 32,
  "max_concurrent": 400
}
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误代码

| HTTP状态码 | 说明 | 示例 |
|-----------|------|------|
| 400 | 请求参数错误 | 缺少必填字段、格式不正确 |
| 401 | 认证失败 | JWT token无效或过期 |
| 403 | 权限不足 | 尝试访问其他用户的资源 |
| 404 | 资源不存在 | 指定的ID不存在 |
| 422 | 数据验证失败 | 字段格式不符合要求 |
| 500 | 服务器内部错误 | 系统异常 |

### 具体错误示例

**401 认证失败**:
```json
{
  "detail": "Invalid authentication credentials"
}
```

**404 资源不存在**:
```json
{
  "detail": "Blacklist not found"
}
```

**422 数据验证失败**:
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 限制和约束

### 请求频率限制

- 检测接口: 1000次/分钟（可配置）
- 配置接口: 100次/分钟
- 健康检查: 无限制

### 数据量限制

| 字段 | 限制 |
|------|------|
| 检测内容长度 | 最大10000字符 |
| 黑名单名称 | 最大100字符 |
| 关键词长度 | 最大50字符 |
| 关键词数量 | 每个列表最大1000个 |
| 模板内容 | 最大1000字符 |
| 描述信息 | 最大500字符 |

### 并发限制

- 检测服务: 最大400并发请求
- 管理服务: 最大50并发请求

## 使用示例

### curl示例

```bash
# 生成JWT token (客户端实现)
JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# 检测内容
curl -X POST "http://your-domain.com/v1/guardrails" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "这里是要检测的内容"
      }
    ]
  }'

# 创建黑名单
curl -X POST "http://your-domain.com/config/blacklist" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "敏感词过滤",
    "keywords": ["敏感词1", "敏感词2"],
    "description": "用户专属敏感词列表",
    "is_active": true
  }'

# 获取黑名单列表
curl -X GET "http://your-domain.com/config/blacklist" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Python requests示例

```python
import requests
import jwt
from datetime import datetime, timedelta

# 生成JWT token
def generate_token(user_id, email, secret_key):
    payload = {
        "user_id": user_id,
        "sub": user_id,
        "email": email,
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')

# API配置
API_BASE = "http://your-domain.com"
JWT_SECRET = "your-jwt-secret-key"
USER_ID = "550e8400-e29b-41d4-a716-446655440001"
USER_EMAIL = "user@example.com"

# 生成token
token = generate_token(USER_ID, USER_EMAIL, JWT_SECRET)
headers = {"Authorization": f"Bearer {token}"}

# 检测内容
response = requests.post(
    f"{API_BASE}/v1/guardrails",
    headers=headers,
    json={
        "messages": [
            {
                "role": "user", 
                "content": "这里是要检测的内容"
            }
        ]
    }
)
print("检测结果:", response.json())

# 创建黑名单
response = requests.post(
    f"{API_BASE}/config/blacklist",
    headers=headers,
    json={
        "name": "敏感词过滤",
        "keywords": ["敏感词1", "敏感词2"],
        "description": "用户专属敏感词列表",
        "is_active": True
    }
)
print("创建结果:", response.json())
```

## 版本变更历史

### v1.0 (2024-01-01)
- 初始版本发布
- 支持内容检测、黑白名单管理、代答模板管理
- 支持JWT认证和用户隔离

---

*文档版本: v1.0*  
*更新时间: 2024-01-01*