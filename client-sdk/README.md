# 象信AI安全护栏 客户端SDK

本目录包含象信AI安全护栏系统的官方客户端SDK，支持多种编程语言和双服务架构。

## 🏗️ 架构说明

### 双服务架构 (v2.0+)

象信AI安全护栏采用双服务架构，将功能分离以提供更好的性能和可扩展性：

```
┌─────────────────┐    ┌─────────────────┐
│   检测服务      │    │   管理服务      │
│   (端口 5000)   │    │   (端口 5001)   │
│                 │    │                 │
│ • 高并发检测    │    │ • 配置管理      │
│ • 内容安全分析  │    │ • 结果查询      │
│ • 实时响应      │    │ • 统计分析      │
│ • 轻量级        │    │ • 用户管理      │
└─────────────────┘    └─────────────────┘
       │                       │
       └───────────┬───────────┘
                   │
            ┌─────────────┐
            │  客户端SDK  │
            │             │
            │ • 自动路由  │
            │ • 统一接口  │
            │ • 错误处理  │
            │ • 重试机制  │
            └─────────────┘
```

**服务分工：**
- **检测服务**：专门处理 `/v1/guardrails` 内容检测请求，优化为高并发、低延迟
- **管理服务**：处理 `/api/v1/*` 管理接口，包括黑白名单、代答模板、结果查询等

### 认证方式

**API Key 认证（推荐）**
- 简单安全，适合生产环境
- 无需用户身份信息
- 自动权限管理

**JWT 认证（向后兼容）**
- 兼容旧版本
- 需要提供用户ID和邮箱
- 灵活的权限控制

## 📦 可用的SDK

### [Python SDK](./python/) [![PyPI](https://img.shields.io/badge/PyPI-v2.0.0-blue)](./python/)

**特性：**
- 支持 Python 3.7+
- 异步和同步操作
- 完整的类型提示
- 丰富的错误处理

**安装：**
```bash
pip install xiangxin-guardrails-client
```

**快速开始：**
```python
from guardrails_client import GuardrailsClient

# API Key方式
client = GuardrailsClient(
    detection_url="http://detection:5000",
    admin_url="http://admin:5001",
    api_key="your-api-key"
)

result = client.check_content([
    {"role": "user", "content": "要检测的内容"}
])
```

### [Node.js SDK](./nodejs/) [![npm](https://img.shields.io/badge/npm-v2.0.0-green)](./nodejs/)

**特性：**
- 支持 Node.js 14+
- Promise/async-await 支持
- TypeScript 声明文件
- 自动重试机制

**安装：**
```bash
npm install xiangxin-guardrails-client
```

**快速开始：**
```javascript
const { GuardrailsClient } = require('xiangxin-guardrails-client');

// API Key方式
const client = new GuardrailsClient(
    'http://detection:5000',
    'http://admin:5001',
    { apiKey: 'your-api-key' }
);

const result = await client.checkContent([
    { role: 'user', content: '要检测的内容' }
]);
```

### [Java SDK](./java/) [![Maven](https://img.shields.io/badge/Maven-v2.0.0-orange)](./java/)

**特性：**
- 支持 Java 8+
- 建造者模式配置
- 完整的异常处理
- Maven/Gradle 支持

**安装（Maven）：**
```xml
<dependency>
    <groupId>com.xiangxin</groupId>
    <artifactId>guardrails-client</artifactId>
    <version>2.0.0</version>
</dependency>
```

**快速开始：**
```java
GuardrailsClient client = new GuardrailsClient.Builder()
    .detectionUrl("http://detection:5000")
    .adminUrl("http://admin:5001")
    .apiKey("your-api-key")
    .build();

List<Message> messages = Arrays.asList(
    new Message("user", "要检测的内容")
);
DetectionResult result = client.checkContent(messages);
```

## 🚀 功能对比

| 功能 | Python | Node.js | Java |
|------|--------|---------|------|
| 内容检测 | ✅ | ✅ | ✅ |
| 批量检测 | ✅ | ✅ | ✅ |
| 黑名单管理 | ✅ | ✅ | ✅ |
| 白名单管理 | ✅ | ✅ | ✅ |
| 代答模板 | ✅ | ✅ | ✅ |
| 结果查询 | ✅ | ✅ | ✅ |
| 健康检查 | ✅ | ✅ | ✅ |
| API Key认证 | ✅ | ✅ | ✅ |
| JWT认证 | ✅ | ✅ | ✅ |
| 自动重试 | ✅ | ✅ | ✅ |
| 连接池 | ✅ | ✅ | ✅ |
| 类型提示 | ✅ | 🔄* | ✅ |
| 异步支持 | ✅ | ✅ | ❌ |

*Node.js SDK 计划在后续版本提供 TypeScript 声明文件

## 📋 API 接口

### 内容检测

```
POST /v1/guardrails
```

**请求格式：**
```json
{
  "model": "Xiangxin-Guardrails-Text",
  "messages": [
    {"role": "user", "content": "要检测的内容"},
    {"role": "assistant", "content": "助手回答"}
  ]
}
```

**响应格式：**
```json
{
  "id": "req_123456",
  "overall_risk_level": "中风险",
  "suggest_action": "代答",
  "suggest_answer": "抱歉，我不能回答这个问题。",
  "result": {
    "compliance": {
      "risk_level": "中风险",
      "categories": ["一般政治话题"]
    },
    "security": {
      "risk_level": "无风险",
      "categories": []
    }
  }
}
```

### 配置管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 黑名单列表 | GET | `/api/v1/config/blacklist` | 获取黑名单 |
| 创建黑名单 | POST | `/api/v1/config/blacklist` | 创建黑名单 |
| 白名单列表 | GET | `/api/v1/config/whitelist` | 获取白名单 |
| 代答模板 | GET | `/api/v1/config/responses` | 获取模板 |

### 结果查询

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 结果列表 | GET | `/api/v1/results` | 分页查询结果 |
| 结果详情 | GET | `/api/v1/results/{id}` | 获取详细信息 |

## 🔒 安全最佳实践

### 1. API Key 管理

```bash
# 环境变量方式（推荐）
export GUARDRAILS_API_KEY="your-api-key"
export GUARDRAILS_DETECTION_URL="http://detection:5000"
export GUARDRAILS_ADMIN_URL="http://admin:5001"
```

### 2. 网络安全

- 使用 HTTPS 连接生产环境
- 配置防火墙限制访问来源
- 启用请求速率限制

### 3. 错误处理

```python
try:
    result = client.check_content(messages)
except RateLimitError as e:
    # 处理限速错误
    time.sleep(60)  # 等待后重试
except AuthenticationError as e:
    # 处理认证错误
    logger.error(f"认证失败: {e}")
except GuardrailsError as e:
    # 处理其他护栏系统错误
    logger.error(f"系统错误: {e}")
```

## 📊 性能优化

### 1. 连接池配置

```python
# Python
client = GuardrailsClient(
    detection_url="http://detection:5000",
    admin_url="http://admin:5001",
    api_key="your-api-key",
    timeout=30,
    max_retries=3
)
```

```javascript
// Node.js
const client = new GuardrailsClient(
    'http://detection:5000',
    'http://admin:5001',
    { 
        apiKey: 'your-api-key',
        timeout: 30000,
        maxRetries: 3
    }
);
```

```java
// Java
GuardrailsClient client = new GuardrailsClient.Builder()
    .detectionUrl("http://detection:5000")
    .adminUrl("http://admin:5001")
    .apiKey("your-api-key")
    .connectTimeout(30)
    .readTimeout(30)
    .maxRetries(3)
    .build();
```

### 2. 批量处理

对于大量内容检测，使用批量接口提高效率：

```python
# 批量检测
content_list = ["内容1", "内容2", "内容3"]
results = client.batch_check_content(content_list)
```

## 🐛 故障排查

### 常见问题

**1. 连接超时**
```
解决方案：增加超时时间，检查网络连接
```

**2. 认证失败**
```
解决方案：检查API Key是否正确，确认服务地址
```

**3. 限速错误**
```
解决方案：降低请求频率，实现退避重试
```

### 调试模式

```python
# Python - 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

```javascript
// Node.js - 启用调试
process.env.DEBUG = 'guardrails:*'
```

## 🔄 版本迁移

### 从 v1.x 迁移到 v2.0

**主要变化：**
1. 双服务架构：需要提供两个服务地址
2. API Key认证：推荐使用API Key替代JWT
3. 端点变化：管理接口路径前缀变更

**迁移步骤：**

```python
# v1.x 写法
client = GuardrailsClient(
    api_base_url="http://guardrails:5000",
    jwt_secret="secret"
)

# v2.0 写法
client = GuardrailsClient(
    detection_url="http://detection:5000",
    admin_url="http://admin:5001",
    api_key="your-api-key"
)
```

## 📞 技术支持

- **GitHub Issues**: [提交问题](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- **技术文档**: [完整文档](https://docs.xiangxin.ai)
- **邮件支持**: support@xiangxin.ai
- **企业支持**: enterprise@xiangxin.ai

## 📄 许可证

本项目采用 [MIT 许可证](../LICENSE)。

## 🎯 路线图

- [ ] Go SDK
- [ ] PHP SDK  
- [ ] .NET SDK
- [ ] TypeScript 声明文件
- [ ] gRPC 协议支持
- [ ] 流式检测接口
- [ ] 离线模式支持

---

*最后更新: 2024-12-19*
