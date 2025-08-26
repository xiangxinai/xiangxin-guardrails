# 象信AI安全护栏 Java 客户端SDK

[![Maven Central](https://img.shields.io/maven-central/v/com.xiangxin/guardrails-client.svg)](https://search.maven.org/artifact/com.xiangxin/guardrails-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

象信AI安全护栏 Java 客户端SDK，支持双服务架构，提供内容安全检测和管理功能。

## 版本说明

- **v2.0.0**: 支持双服务架构（检测服务 + 管理服务），支持API Key和JWT两种认证方式
- **v1.x**: 单服务架构（已废弃）

## 架构说明

### 双服务架构

- **检测服务** (端口5000): 高并发内容安全检测
- **管理服务** (端口5001): 配置管理、结果查询、统计分析

### 认证方式

- **API Key认证** (推荐): 简单安全，适合生产环境
- **JWT认证**: 向后兼容，需要用户信息

## 安装

### Maven

```xml
<dependency>
    <groupId>com.xiangxin</groupId>
    <artifactId>guardrails-client</artifactId>
    <version>2.0.0</version>
</dependency>
```

### Gradle

```gradle
implementation 'com.xiangxin:guardrails-client:2.0.0'
```

## 快速开始

### 方式一：API Key认证（推荐）

```java
import com.xiangxin.guardrails.*;
import com.xiangxin.guardrails.models.*;
import java.util.*;

// 创建客户端
GuardrailsClient client = new GuardrailsClient.Builder()
    .detectionUrl("http://your-guardrails-detection:5000")
    .adminUrl("http://your-guardrails-admin:5001")
    .apiKey("your-api-key")
    .build();

try {
    // 检测内容
    List<Message> messages = Arrays.asList(
        new Message("user", "要检测的内容")
    );
    DetectionResult result = client.checkContent(messages);
    System.out.println("检测结果: " + result.getOverallRiskLevel());
    
    // 获取黑名单列表
    List<BlacklistItem> blacklists = client.getBlacklists();
    System.out.println("黑名单数量: " + blacklists.size());
    
} catch (GuardrailsException e) {
    System.err.println("检测失败: " + e.getMessage());
} finally {
    client.close();
}
```

### 方式二：JWT认证（向后兼容）

```java
// 创建客户端
GuardrailsClient client = new GuardrailsClient.Builder()
    .detectionUrl("http://your-guardrails-detection:5000")
    .adminUrl("http://your-guardrails-admin:5001")
    .jwtSecret("your-jwt-secret-key")
    .build();

String userId = "550e8400-e29b-41d4-a716-446655440001";
String userEmail = "user@example.com";

try {
    // 检测内容（需要提供用户信息）
    List<Message> messages = Arrays.asList(
        new Message("user", "要检测的内容")
    );
    DetectionResult result = client.checkContent(messages, userId, userEmail);
    
} catch (GuardrailsException e) {
    System.err.println("检测失败: " + e.getMessage());
} finally {
    client.close();
}
```

## API 参考

### 内容检测

#### 基础检测

```java
// API Key方式
List<Message> messages = Arrays.asList(
    new Message("user", "检测内容"),
    new Message("assistant", "助手回答")
);
DetectionResult result = client.checkContent(messages);

// JWT方式
DetectionResult result = client.checkContent(messages, userId, userEmail);
```

#### 批量检测

```java
List<String> contentList = Arrays.asList("内容1", "内容2", "内容3");
List<BatchResult> results = client.batchCheckContent(contentList);

for (BatchResult batchResult : results) {
    if (batchResult.isSuccess()) {
        System.out.println("检测成功: " + batchResult.getResult().getOverallRiskLevel());
    } else {
        System.err.println("检测失败: " + batchResult.getError());
    }
}
```

### 黑白名单管理

#### 黑名单操作

```java
// 获取黑名单列表
List<BlacklistItem> blacklists = client.getBlacklists();

// 创建黑名单
BlacklistItem newBlacklist = client.createBlacklist(
    "敏感词库",
    Arrays.asList("敏感词1", "敏感词2"),
    "描述信息",
    true  // 是否启用
);

// 更新黑名单
BlacklistItem updated = client.updateBlacklist(
    newBlacklist.getId(),
    "更新后的名称",
    Arrays.asList("新敏感词1", "新敏感词2"),
    "新描述",
    true
);

// 删除黑名单
client.deleteBlacklist(newBlacklist.getId());
```

#### 白名单操作

```java
// 获取白名单列表
List<WhitelistItem> whitelists = client.getWhitelists();

// 创建白名单
WhitelistItem newWhitelist = client.createWhitelist(
    "安全词库",
    Arrays.asList("安全词1", "安全词2"),
    "白名单描述",
    true
);
```

### 代答模板管理

```java
// 获取代答模板列表
List<ResponseTemplate> templates = client.getResponseTemplates();

// 创建代答模板
ResponseTemplate template = client.createResponseTemplate(
    "S1",                    // 风险类别代码
    "中风险",                // 风险等级
    "抱歉，我不能回答这个问题", // 模板内容
    true,                    // 是否为默认模板
    true                     // 是否启用
);
```

### 检测结果查询

```java
// 构建查询条件
ResultsQueryOptions options = new ResultsQueryOptions()
    .setPage(1)
    .setPerPage(20)
    .setRiskLevel("高风险")
    .setCategory("敏感政治话题")
    .setStartDate("2024-01-01")
    .setEndDate("2024-12-31")
    .setContentSearch("搜索关键词");

// 获取结果列表
ResultsPage results = client.getResults(options);
System.out.println("总数: " + results.getTotal());
System.out.println("当前页: " + results.getPage());

// 获取单个结果详情
for (DetectionResultSummary summary : results.getItems()) {
    DetectionResultDetail detail = client.getResult(summary.getId());
    System.out.println("完整内容: " + detail.getContent());
}
```

### 系统管理

#### 健康检查

```java
// 检测服务健康检查
Map<String, Object> detectionHealth = client.healthCheck(GuardrailsClient.ServiceType.DETECTION);

// 管理服务健康检查
Map<String, Object> adminHealth = client.healthCheck(GuardrailsClient.ServiceType.ADMIN);
```

## 配置选项

### 客户端配置

```java
GuardrailsClient client = new GuardrailsClient.Builder()
    .detectionUrl("http://detection-service:5000")
    .adminUrl("http://admin-service:5001")
    .apiKey("your-api-key")
    .connectTimeout(30)       // 连接超时（秒）
    .readTimeout(60)          // 读取超时（秒）
    .writeTimeout(60)         // 写入超时（秒）
    .maxRetries(3)            // 最大重试次数
    .build();
```

## 错误处理

### 异常类型

- `GuardrailsException`: 基础异常
- `AuthenticationException`: 认证失败
- `ValidationException`: 数据验证失败
- `NotFoundException`: 资源不存在
- `RateLimitException`: 请求频率限制

### 错误处理示例

```java
try {
    DetectionResult result = client.checkContent(messages);
} catch (AuthenticationException e) {
    System.err.println("认证失败: " + e.getMessage());
} catch (RateLimitException e) {
    System.err.println("请求过于频繁: " + e.getMessage());
} catch (GuardrailsException e) {
    System.err.println("系统错误: " + e.getMessage());
}
```

## 风险类别

| 类别代码 | 类别名称 | 风险等级 |
|---------|---------|---------|
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

## 完整示例

参考 `src/main/java/com/xiangxin/guardrails/examples/GuardrailsExample.java` 文件查看完整的使用示例。

## 依赖要求

- Java 8+
- OkHttp 4.12.0+
- Jackson 2.16.0+
- Auth0 JWT 4.4.0+

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 技术支持

如有问题或建议，请通过以下方式联系我们：

- 提交 Issue: [GitHub Issues](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- 邮箱: support@xiangxin.ai

## 更新日志

### v2.0.0 (2024-12-19)

- ✨ 支持双服务架构（检测服务 + 管理服务）
- ✨ 支持API Key认证方式（推荐）
- ✅ 兼容JWT认证方式
- 🔄 更新所有API端点以匹配新架构
- ➕ 增加检测结果查询接口
- 🐛 优化错误处理和重试机制
- 🚀 提供完整的批量操作支持
- 📚 完善文档和示例代码
