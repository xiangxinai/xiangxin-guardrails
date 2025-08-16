# 象信AI安全护栏 - 客户集成指南

## 概述

本文档详细说明如何将象信AI安全护栏集成到您的系统中，实现用户级别的内容安全检测和配置管理。

## 部署架构

### 私有化部署模式
- 所有服务（前端、后端、数据库）部署在客户环境
- 数据库仅存储配置信息（黑白名单、代答模板等）
- 检测结果可选择存储到数据库或仅写入日志文件
- 客户通过API管理每个用户的安全配置

### 与SaaS模式的区别
| 功能 | SaaS模式 | 私有化部署模式 |
|------|----------|----------------|
| 数据存储 | 完整存储检测结果 | 可选存储检测结果 |
| 配置管理 | Web界面管理 | API接口管理 |
| 用户系统 | 内置用户系统 | 对接客户用户系统 |
| 数据隔离 | 按用户隔离 | 按用户隔离 |

## 1. 部署配置

### 1.1 环境变量配置

在 `.env` 文件中配置以下参数：

```bash
# 基础配置
APP_NAME=Xiangxin Guardrails
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/guardrails_db

# JWT配置（重要：客户需要知道此密钥）
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
JWT_ALGORITHM=HS256  
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 检测结果存储开关（关键配置）
STORE_DETECTION_RESULTS=false  # true=存储到数据库, false=仅写日志文件

# 模型配置
GUARDRAILS_MODEL_API_URL=http://localhost:58002/v1
GUARDRAILS_MODEL_API_KEY=your-model-api-key
GUARDRAILS_MODEL_NAME=Xiangxin-Guardrails-Text

# 数据目录
DATA_DIR=/path/to/data/directory
```

### 1.2 关键配置说明

#### STORE_DETECTION_RESULTS
- `true`: 检测结果存储到数据库（适合需要完整数据分析的场景）
- `false`: 检测结果仅写入日志文件（推荐，减少数据库压力）

#### JWT_SECRET_KEY  
- **极其重要**: 客户需要使用相同的密钥来生成JWT token
- 建议使用64位随机字符串：`openssl rand -base64 64`

## 2. API认证机制

### 2.1 JWT Token结构

客户需要为每个用户生成包含以下字段的JWT token：

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "sub": "550e8400-e29b-41d4-a716-446655440001", 
  "email": "user@example.com",
  "role": "user",
  "exp": 1234567890
}
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户UUID字符串，用于数据隔离 |
| sub | string | 是 | JWT标准主题字段，通常等于user_id |
| email | string | 是 | 用户邮箱地址 |
| role | string | 是 | 固定值"user" |
| exp | number | 是 | 过期时间戳 |

## 3. 配置管理API

### 3.1 认证方式

所有API请求需要在Header中携带JWT token：

```http
Authorization: Bearer <jwt_token>
```

### 3.2 黑名单管理

#### 获取黑名单
```http
GET /config/blacklist
Authorization: Bearer <user_jwt_token>
```

**响应示例：**
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

#### 创建黑名单
```http
POST /config/blacklist
Authorization: Bearer <user_jwt_token>
Content-Type: application/json

{
  "name": "敏感词列表",
  "keywords": ["敏感词1", "敏感词2", "敏感词3"],
  "description": "用户专属敏感词过滤", 
  "is_active": true
}
```

#### 更新黑名单
```http
PUT /config/blacklist/{blacklist_id}
Authorization: Bearer <user_jwt_token>
Content-Type: application/json

{
  "name": "更新的敏感词列表",
  "keywords": ["新敏感词1", "新敏感词2"],
  "description": "更新后的描述",
  "is_active": true
}
```

#### 删除黑名单
```http
DELETE /config/blacklist/{blacklist_id}
Authorization: Bearer <user_jwt_token>
```

### 3.3 白名单管理

白名单API与黑名单API结构完全相同，仅路径不同：

- `GET /config/whitelist` - 获取白名单
- `POST /config/whitelist` - 创建白名单  
- `PUT /config/whitelist/{whitelist_id}` - 更新白名单
- `DELETE /config/whitelist/{whitelist_id}` - 删除白名单

### 3.4 代答模板管理

#### 获取代答模板
```http
GET /config/responses
Authorization: Bearer <user_jwt_token>
```

#### 创建代答模板
```http
POST /config/responses
Authorization: Bearer <user_jwt_token>
Content-Type: application/json

{
  "category": "S1",  
  "risk_level": "中风险",
  "template_content": "抱歉，我不能回答涉及政治话题的问题。",
  "is_default": true,
  "is_active": true
}
```

**风险类别说明：**
| 类别 | 名称 | 风险等级 |
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

## 4. 内容检测API

### 4.1 检测接口

```http
POST /v1/guardrails
Authorization: Bearer <user_jwt_token>
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

### 4.2 检测响应

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

### 4.3 建议动作说明

| 动作 | 说明 | 适用场景 |
|------|------|----------|
| 通过 | 内容安全，可以正常处理 | 无风险内容 |
| 代答 | 用预设回复替代原回答 | 低风险、中风险内容 |
| 阻断 | 拒绝处理，返回错误 | 高风险内容 |

## 5. 客户端集成示例

### 5.1 Python集成示例

```python
import jwt
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class GuardrailsClient:
    def __init__(self, api_base_url: str, jwt_secret: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.jwt_secret = jwt_secret
    
    def generate_user_token(self, user_id: str, user_email: str, 
                          expire_hours: int = 1) -> str:
        """为指定用户生成临时JWT token"""
        payload = {
            "user_id": str(user_id),
            "sub": str(user_id),
            "email": user_email,
            "role": "user",
            "exp": datetime.utcnow() + timedelta(hours=expire_hours)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def _make_request(self, method: str, endpoint: str, user_id: str, 
                     user_email: str, **kwargs) -> requests.Response:
        """发起API请求"""
        token = self.generate_user_token(user_id, user_email)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            
        kwargs['headers'] = headers
        url = f"{self.api_base_url}{endpoint}"
        
        return requests.request(method, url, **kwargs)
    
    # 黑名单管理
    def get_blacklists(self, user_id: str, user_email: str) -> List[Dict]:
        """获取用户黑名单"""
        response = self._make_request("GET", "/config/blacklist", 
                                    user_id, user_email)
        response.raise_for_status()
        return response.json()
    
    def create_blacklist(self, user_id: str, user_email: str,
                        name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict:
        """创建黑名单"""
        data = {
            "name": name,
            "keywords": keywords,
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("POST", "/config/blacklist",
                                    user_id, user_email, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_blacklist(self, user_id: str, user_email: str,
                        blacklist_id: int, name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict:
        """更新黑名单"""
        data = {
            "name": name,
            "keywords": keywords, 
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("PUT", f"/config/blacklist/{blacklist_id}",
                                    user_id, user_email, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_blacklist(self, user_id: str, user_email: str,
                        blacklist_id: int) -> Dict:
        """删除黑名单"""
        response = self._make_request("DELETE", f"/config/blacklist/{blacklist_id}",
                                    user_id, user_email)
        response.raise_for_status()
        return response.json()
    
    # 白名单管理（方法结构与黑名单相同）
    def get_whitelists(self, user_id: str, user_email: str) -> List[Dict]:
        """获取用户白名单"""
        response = self._make_request("GET", "/config/whitelist",
                                    user_id, user_email)
        response.raise_for_status()
        return response.json()
    
    def create_whitelist(self, user_id: str, user_email: str,
                        name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict:
        """创建白名单"""
        data = {
            "name": name,
            "keywords": keywords,
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("POST", "/config/whitelist",
                                    user_id, user_email, json=data)
        response.raise_for_status()
        return response.json()
    
    # 代答模板管理
    def get_response_templates(self, user_id: str, user_email: str) -> List[Dict]:
        """获取用户代答模板"""
        response = self._make_request("GET", "/config/responses",
                                    user_id, user_email)
        response.raise_for_status()
        return response.json()
    
    def create_response_template(self, user_id: str, user_email: str,
                               category: str, risk_level: str,
                               template_content: str, is_default: bool = True,
                               is_active: bool = True) -> Dict:
        """创建代答模板"""
        data = {
            "category": category,
            "risk_level": risk_level,
            "template_content": template_content,
            "is_default": is_default,
            "is_active": is_active
        }
        response = self._make_request("POST", "/config/responses",
                                    user_id, user_email, json=data)
        response.raise_for_status()
        return response.json()
    
    # 内容检测
    def check_content(self, user_id: str, user_email: str,
                     messages: List[Dict[str, str]]) -> Dict:
        """检测内容安全性"""
        data = {"messages": messages}
        response = self._make_request("POST", "/v1/guardrails",
                                    user_id, user_email, json=data)
        response.raise_for_status()
        return response.json()

# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    client = GuardrailsClient(
        api_base_url="http://your-guardrails-api.com",
        jwt_secret="your-jwt-secret-key"  # 与护栏系统相同
    )
    
    # 用户信息
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    user_email = "user@example.com"
    
    # 为用户创建黑名单
    blacklist = client.create_blacklist(
        user_id=user_id,
        user_email=user_email,
        name="敏感词过滤",
        keywords=["敏感词1", "敏感词2"],
        description="用户专属敏感词列表"
    )
    print("创建黑名单:", blacklist)
    
    # 检测内容
    result = client.check_content(
        user_id=user_id,
        user_email=user_email,
        messages=[{
            "role": "user",
            "content": "这里是要检测的内容"
        }]
    )
    print("检测结果:", result)
```

### 5.2 Node.js集成示例

```javascript
const jwt = require('jsonwebtoken');
const axios = require('axios');

class GuardrailsClient {
    constructor(apiBaseUrl, jwtSecret) {
        this.apiBaseUrl = apiBaseUrl.replace(/\/+$/, '');
        this.jwtSecret = jwtSecret;
    }

    generateUserToken(userId, userEmail, expireHours = 1) {
        const payload = {
            user_id: userId,
            sub: userId,
            email: userEmail,
            role: 'user',
            exp: Math.floor(Date.now() / 1000) + (expireHours * 60 * 60)
        };
        return jwt.sign(payload, this.jwtSecret, { algorithm: 'HS256' });
    }

    async makeRequest(method, endpoint, userId, userEmail, data = null) {
        const token = this.generateUserToken(userId, userEmail);
        const config = {
            method,
            url: `${this.apiBaseUrl}${endpoint}`,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            config.data = data;
        }

        try {
            const response = await axios(config);
            return response.data;
        } catch (error) {
            throw new Error(`API请求失败: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 黑名单管理
    async getBlacklists(userId, userEmail) {
        return await this.makeRequest('GET', '/config/blacklist', userId, userEmail);
    }

    async createBlacklist(userId, userEmail, name, keywords, description = '', isActive = true) {
        const data = { name, keywords, description, is_active: isActive };
        return await this.makeRequest('POST', '/config/blacklist', userId, userEmail, data);
    }

    // 内容检测
    async checkContent(userId, userEmail, messages) {
        const data = { messages };
        return await this.makeRequest('POST', '/v1/guardrails', userId, userEmail, data);
    }
}

// 使用示例
const client = new GuardrailsClient(
    'http://your-guardrails-api.com',
    'your-jwt-secret-key'
);

async function example() {
    const userId = '550e8400-e29b-41d4-a716-446655440001';
    const userEmail = 'user@example.com';

    try {
        // 创建黑名单
        const blacklist = await client.createBlacklist(
            userId,
            userEmail,
            '敏感词过滤',
            ['敏感词1', '敏感词2'],
            '用户专属敏感词列表'
        );
        console.log('创建黑名单:', blacklist);

        // 检测内容
        const result = await client.checkContent(
            userId,
            userEmail,
            [{ role: 'user', content: '这里是要检测的内容' }]
        );
        console.log('检测结果:', result);
    } catch (error) {
        console.error('操作失败:', error.message);
    }
}

example();
```

## 6. 日志管理

### 6.1 日志文件位置

当 `STORE_DETECTION_RESULTS=false` 时，检测结果写入日志文件：

```
{DATA_DIR}/logs/detection/detection_YYYYMMDD.jsonl
```

### 6.2 日志格式

每行一条JSON记录：

```json
{
  "request_id": "guardrails-abc123",
  "user_id": "550e8400-e29b-41d4-a716-446655440001", 
  "content": "用户输入内容",
  "suggest_action": "代答",
  "suggest_answer": "建议回答",
  "model_response": "模型原始响应",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "security_risk_level": "无风险",
  "security_categories": [],
  "compliance_risk_level": "中风险", 
  "compliance_categories": ["一般政治话题"],
  "created_at": "2024-01-01T12:00:00.000Z",
  "hit_keywords": null
}
```

### 6.3 日志分析示例

```python
import json
from pathlib import Path
from datetime import datetime

def analyze_detection_logs(log_dir: str, date: str = None):
    """分析检测日志"""
    log_path = Path(log_dir)
    
    if date:
        # 分析指定日期的日志
        log_file = log_path / f"detection_{date.replace('-', '')}.jsonl"
        files = [log_file] if log_file.exists() else []
    else:
        # 分析所有日志文件
        files = list(log_path.glob("detection_*.jsonl"))
    
    stats = {
        "total_requests": 0,
        "actions": {"通过": 0, "代答": 0, "阻断": 0},
        "risk_levels": {"无风险": 0, "低风险": 0, "中风险": 0, "高风险": 0},
        "users": set()
    }
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    stats["total_requests"] += 1
                    stats["actions"][data.get("suggest_action", "未知")] += 1
                    
                    compliance_risk = data.get("compliance_risk_level", "无风险")
                    security_risk = data.get("security_risk_level", "无风险")
                    overall_risk = max(compliance_risk, security_risk, 
                                     key=lambda x: ["无风险", "低风险", "中风险", "高风险"].index(x))
                    stats["risk_levels"][overall_risk] += 1
                    
                    if data.get("user_id"):
                        stats["users"].add(data["user_id"])
                        
                except json.JSONDecodeError:
                    continue
    
    stats["unique_users"] = len(stats["users"])
    del stats["users"]  # 删除用户ID集合，避免泄露
    
    return stats

# 使用示例
stats = analyze_detection_logs("/path/to/logs/detection", "2024-01-01")
print(f"统计结果: {stats}")
```

## 7. 常见问题

### Q1: JWT token过期了怎么办？
**A**: JWT token有过期时间，客户端需要在token过期前重新生成。建议设置较短的过期时间（如1小时），每次API调用时动态生成token。

### Q2: 如何确保JWT密钥安全？
**A**: 
- JWT密钥应存储在安全的配置管理系统中
- 不要在代码中硬编码JWT密钥
- 定期轮换JWT密钥（需要同时更新护栏系统配置）
- 使用强随机密钥（推荐64位以上）

### Q3: 可以为同一用户设置多个黑名单吗？
**A**: 可以。每个用户可以创建多个黑名单和白名单，系统会检查所有激活的列表。

### Q4: 白名单和黑名单冲突时如何处理？
**A**: 黑名单优先级高于白名单。如果内容同时匹配黑名单和白名单，会按照黑名单的规则处理。

### Q5: 如何批量导入关键词？
**A**: 可以通过API接口批量创建，将关键词列表作为数组传入 `keywords` 字段。

### Q6: 检测结果的准确率如何？
**A**: 系统采用多层检测机制：
1. 关键词快速匹配（黑白名单）
2. AI模型深度分析
3. 用户自定义代答模板

准确率依赖于关键词配置的完整性和AI模型的质量。

## 8. 技术支持

- **技术支持邮箱**: wanglei@xiangxinai.cn
- **文档更新**: 请关注最新版本的集成文档
- **API变更**: 重要API变更会通过邮件通知

---

*本文档版本: v1.0*  
*更新时间: 2024-01-01*