# 更新日志 Changelog

本文件记录象信AI安全护栏平台的所有重要变更。

All notable changes to Xiangxin AI Guardrails platform are documented in this file.

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，
版本号遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2025-10-04

### 🚀 重大更新 Major Updates
- 🔐 **敏感数据防泄漏功能 (Data Leak Detection)**
  - 新增基于正则表达式的敏感数据检测和脱敏功能
  - 支持检测身份证号、手机号、邮箱、银行卡号、护照号、IP地址等敏感信息
  - 提供多种脱敏方法：替换、掩码、哈希、加密、重排、随机替换
  - 支持自定义敏感数据类型和正则表达式规则
  - 区分输入和输出检测，灵活配置检测范围
  - 支持系统级和用户级配置

### 新增 Added
- 🔐 **数据安全检测**
  - 新增数据防泄漏配置管理页面
  - 支持自定义敏感数据类型定义（名称、正则表达式、风险等级）
  - 三级风险等级：低风险、中风险、高风险
  - 六种脱敏方法：替换(replace)、掩码(mask)、哈希(hash)、加密(encrypt)、重排(shuffle)、随机替换(random)
  - 输入/输出方向检测配置
  - 内置常见敏感数据类型：ID_CARD_NUMBER、PHONE_NUMBER、EMAIL、BANK_CARD_NUMBER、PASSPORT_NUMBER、IP_ADDRESS等

- 📊 **检测结果增强**
  - 检测结果新增 `data` 字段，包含数据安全检测结果
  - 响应格式：`result.data.risk_level` 和 `result.data.categories`
  - 总览页面新增"发现数据泄漏"统计
  - 在线测试页面新增数据泄漏测试样例
  - 检测结果列表新增"数据泄漏"列
  - 风险报表新增数据泄漏统计

- 🗄️ **数据库变更**
  - 新增 `data_security_patterns` 表：存储敏感数据模式定义
  - 新增 `data_security_config` 表：存储数据防泄漏配置
  - `detection_results` 表新增 `data_risk_level` 和 `data_categories` 字段
  - 新增数据库迁移脚本：
    - `backend/database/migrations/add_data_security_tables.sql`
    - `backend/database/migrations/add_data_security_fields.sql`

- 🔧 **新增文件**
  - `backend/routers/data_security.py` - 数据安全路由
  - `backend/services/data_security_service.py` - 数据安全检测服务
  - `frontend/src/pages/DataSecurity/` - 数据防泄漏配置页面
  - `DATA_SECURITY_README.md` - 数据防泄漏功能文档

### 变更 Changed
- 🔄 **API响应格式更新**
  - 检测结果统一包含三个维度：`compliance`、`security`、`data`
  - 增强的响应格式示例：
    ```json
    {
      "result": {
        "compliance": {"risk_level": "无风险", "categories": []},
        "security": {"risk_level": "无风险", "categories": []},
        "data": {"risk_level": "高风险", "categories": ["PHONE_NUMBER", "ID_CARD_NUMBER"]}
      },
      "suggest_answer": "我的电话是<PHONE_NUMBER>，身份证是<ID_CARD_NUMBER>"
    }
    ```

- 📱 **前端更新**
  - 总览页面重构，新增数据泄漏风险卡片
  - 在线测试页面新增数据泄漏样例
  - 检测结果页面新增数据泄漏筛选和展示
  - 风险报表页面新增数据泄漏统计图表
  - 防护配置新增数据防泄漏子菜单

- 🔧 **后端服务增强**
  - 检测流程整合数据安全检测
  - 支持输入和输出两个方向的数据检测
  - 多风险类型综合决策：以最高风险等级决定最终建议行动
  - 脱敏结果通过 `suggest_answer` 返回

### 修复 Fixed
- 🐛 **数据库连接池优化**
  - 修复高并发场景下数据库连接池泄漏问题
  - 优化连接池配置参数

- 🔧 **正则表达式边界问题**
  - 修复中文文本中正则表达式边界匹配问题
  - 优化中文字符的边界检测逻辑

### SDK 更新 SDK Updates
- 📦 **所有SDK更新以支持新响应格式**
  - Python SDK (xiangxinai)
  - Go SDK (xiangxinai-go)
  - Node.js SDK (xiangxinai)
  - Java SDK (xiangxinai-java)

### 使用示例 Usage Examples

#### 配置敏感数据类型
```python
# 通过API配置敏感数据类型
import requests

response = requests.post(
    "http://localhost:5000/api/v1/data-security/patterns",
    headers={"Authorization": "Bearer your-api-key"},
    json={
        "name": "ID_CARD_NUMBER",
        "pattern": r"\b[1-8]{2}[0-9]{4}[0-9]{4}((0[1-9])|(1[0-2]))((0[1-9])|(1[0-9])|(2[0-9])|(3[0-1]))[0-9]{3}[0-9xX]\b",
        "risk_level": "高",
        "masking_method": "replace"
    }
)
```

#### 检测响应示例
```json
{
    "id": "guardrails-6048ed54e2bb482d894d6cb8c3842153",
    "overall_risk_level": "高风险",
    "suggest_action": "代答",
    "suggest_answer": "我的电话号码是<PHONE_NUMBER>,银行卡号是<BANK_CARD_NUMBER>,身份证号是<ID_CARD_NUMBER>",
    "score": 0.999998927117538,
    "result": {
        "compliance": {"risk_level": "无风险", "categories": []},
        "security": {"risk_level": "无风险", "categories": []},
        "data": {"risk_level": "高风险", "categories": ["BANK_CARD_NUMBER", "ID_CARD_NUMBER", "PHONE_NUMBER"]}
    }
}
```

### 技术特性 Technical Features
- **检测方向配置**：支持仅输入检测、仅输出检测、或双向检测
- **自定义规则**：用户可完全自定义敏感数据检测规则
- **性能优化**：正则匹配优化，支持高并发检测
- **隔离存储**：用户级配置完全隔离

### 文档更新 Documentation Updates
- 更新 README.md 添加数据防泄漏功能说明
- 更新 README_ZH.md 添加数据防泄漏中文文档
- 新增 DATA_SECURITY_README.md 详细功能文档
- 更新 API 文档说明新的响应格式

---

## [2.3.0] - 2025-09-30

### 🚀 重大更新 Major Updates
- 🖼️ **多模态检测功能**
  - 新增图片模态安全检测能力
  - 支持图片内容的合规性和安全性检测
  - 与文本检测保持一致的风险类型和检测标准
  - 完整支持API调用模式和安全网关模式

### 新增 Added
- 🖼️ **图片检测功能**
  - 支持base64编码和URL两种图片输入方式
  - 调用多模态检测模型 `Xiangxin-Guardrails-VL`
  - 图片文件存储在用户专属目录（/mnt/data/xiangxin-guardrails-data/media/{user_uuid}/）
  - 支持在线测试界面上传图片进行检测
  - 新增图片上传组件和预览功能

- 🔌 **API接口增强**
  - 检测API支持混合消息（文本+图片）
  - messages中的content支持数组格式：`[{"type": "text"}, {"type": "image_url"}]`
  - 图片URL支持 `data:image/jpeg;base64,...` 和 `file://...` 两种格式
  - 安全网关代理服务完整支持多模态请求透传

- 📁 **新增文件**
  - `backend/routers/media.py` - 媒体文件管理路由
  - `backend/utils/image_utils.py` - 图片处理工具
  - `backend/utils/url_signature.py` - URL签名验证工具
  - `backend/scripts/migrate_add_image_fields.py` - 数据库迁移脚本
  - `frontend/src/components/ImageUpload/` - 图片上传组件

### 变更 Changed
- 🔄 **检测服务增强**
  - 检测模型调用逻辑支持多模态内容
  - 检测结果数据库表新增图片相关字段
  - 在线测试页面支持图片上传和预览

- 🌐 **API响应格式**
  - 保持与文本检测一致的响应格式
  - 多标签风险支持：可返回多个unsafe标签（如：unsafe\nS1,S2）
  - 敏感度分数和等级适用于图片检测

### 技术特性 Technical Features
- **图片检测模型**：基于视觉-语言模型的多模态安全检测
- **存储管理**：用户级别的媒体文件隔离存储
- **URL安全**：支持签名URL防止未授权访问
- **格式兼容**：兼容OpenAI Vision API消息格式

### 使用示例 Usage Examples

#### Python API调用示例
```python
import base64
from xiangxinai import XiangxinAI

client = XiangxinAI("your-api-key")

# 图片base64编码
with open("image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# 发送图片检测请求
response = client.check_messages([
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "这个图片安全吗？"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
    }
])

print(f"检测结果: {response.overall_risk_level}")
print(f"风险类别: {response.all_categories}")
```

#### cURL调用示例
```bash
curl -X POST "http://localhost:5001/v1/guardrails" \
    -H "Authorization: Bearer your-api-key" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "Xiangxin-Guardrails-VL",
      "messages": [{
        "role": "user",
        "content": [
          {"type": "text", "text": "这个图片安全吗？"},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
      }],
      "logprobs": true
    }'
```

## [2.2.0] - 2025-01-15

### 🚀 重大更新 Major Updates
- 🧠 **代答知识库功能** 
  - 全新的智能代答系统，基于向量相似度搜索
  - 支持上传问答对文件，自动构建知识库向量索引
  - 风险检测时优先匹配知识库中的相似问题，返回对应答案
  - 支持全局知识库和用户级知识库，管理员可配置全局生效的知识库
  
### 新增 Added
- 📚 **代答知识库管理**
  - Web界面支持知识库创建、编辑、删除
  - JSONL格式问答对文件上传和验证
  - 向量索引自动生成和管理
  - 知识库搜索测试功能
  - 支持文件替换和重新索引

- 🎯 **智能代答策略**
  - 风险检测触发时，优先搜索知识库相似问题
  - 基于余弦相似度的问题匹配算法
  - 可配置相似度阈值和返回结果数量
  - 未找到相似问题时，回退到传统拒答模板

### 新增配置 New Configuration
- `EMBEDDING_API_BASE_URL` - Embedding API服务地址
- `EMBEDDING_API_KEY` - Embedding API密钥
- `EMBEDDING_MODEL_NAME` - Embedding模型名称
- `EMBEDDING_MODEL_DIMENSION` - 向量维度配置
- `EMBEDDING_SIMILARITY_THRESHOLD` - 相似度阈值
- `EMBEDDING_MAX_RESULTS` - 最大返回结果数


#### 知识库文件格式
```jsonl
{"questionid": "q1", "question": "什么是人工智能？", "answer": "人工智能是模拟人类智能的技术。"}
{"questionid": "q2", "question": "如何使用机器学习？", "answer": "机器学习是AI的一个重要分支..."}
```

## [2.1.0] - 2025-09-29
增加敏感度阈值配置功能，可自定义检测的敏感度阈值，可用于应对特殊场景或全自动流水线场景。

## [2.0.0] - 2025-01-01

### 🚀 重大更新 Major Updates
- 🛡️ **全新安全网关模式** 
  - 新增反向代理服务(proxy-service)，支持OpenAI兼容的透明代理
  - 实现WAF风格的AI安全防护，自动检测输入和输出
  - 支持上游模型管理，一键配置保护目标模型
  - 零代码改造接入，只需修改base_url和api_key

- 🏗️ **三服务架构重构**
  - **管理服务**(5000端口)：处理管理平台API，低并发优化
  - **检测服务**(5001端口)：高并发护栏检测API
  - **代理服务**(5002端口)：高并发安全网关反向代理
  - 架构优化：数据库连接数从4,800降至176（减少96%）

### 新增 Added
- 🔌 **双模式支持**
  - **API调用模式**：开发者主动调用检测API进行安全检测
  - **安全网关模式**：透明反向代理，自动拦截和检测AI交互

- 🎯 **上游模型管理**
  - Web界面配置上游模型（OpenAI、Claude、本地模型等）
  - API密钥管理和安全存储
  - 请求转发和响应代理
  - 用户级别的模型访问控制

- 🚦 **智能代理策略**
  - 输入检测：用户请求预处理和安全过滤
  - 输出检测：AI回复内容安全审查
  - 自动阻断：高风险内容智能拦截
  - 代答功能：安全回复模板自动替换

- 🐳 **Docker部署架构优化**
  - Docker Compose支持三服务架构
  - 独立的检测、管理、代理服务容器
  - 统一的数据目录挂载和日志管理
  - 自动健康检查和服务发现

- 📁 **新增文件**
  - `backend/proxy_service.py` - 安全网关反向代理服务入口
  - `backend/start_proxy_service.py` - 代理服务启动脚本
  - `backend/start_all_services.sh` - 三服务启动脚本
  - `backend/stop_all_services.sh` - 三服务停止脚本
  - `backend/services/proxy_service.py` - 代理服务核心逻辑
  - `backend/routers/proxy_api.py` - 代理API路由
  - `backend/routers/proxy_management.py` - 代理管理API路由
  - `frontend/src/pages/Config/ProxyModelManagement.tsx` - 上游模型管理界面
  - `examples/proxy_usage_demo.py` - 代理服务使用示例

- 🔌 **私有化集成模式** 🆕
  - 支持与客户现有用户系统深度集成
  - 新增 `STORE_DETECTION_RESULTS` 配置开关，控制检测结果存储方式
  - 客户可通过API管理用户级别的黑白名单和代答模板
  - JWT认证确保用户数据完全隔离

### 变更 Changed
- 🔄 **架构重构**
  - 将单一服务重构为三服务架构，显著提升性能和可扩展性
  - 检测服务：32个高并发进程，专注API检测
  - 管理服务：2个轻量级进程，处理管理功能
  - 代理服务：24个高并发进程，处理安全网关
  - 日志目录配置统一使用DATA_DIR环境变量

- 🌐 **API路由更新**
  - 检测API：`/v1/guardrails` (5001端口)
  - 管理API：`/api/v1/*` (5000端口) 
  - 代理API：OpenAI兼容格式 (5002端口)
  - 新增代理管理API：`/api/v1/proxy/*`
  - 健康检查端点分别对应三个服务

- 📦 **部署配置更新**
  - Docker Compose支持三服务容器独立部署
  - 环境变量新增代理服务相关配置
  - 统一的数据目录挂载策略
  - 自动化服务启动和停止脚本

- 🔧 **配置优化**
  - 新增代理服务配置：`PROXY_PORT`、`PROXY_UVICORN_WORKERS`
  - 优化数据库连接池分离配置
  - 新增上游模型配置管理
  - 支持多种AI模型提供商接入

- 📊 **数据流架构重设计**
  ```
  # API调用模式
  客户端 → 检测服务(5001) → 护栏检测 → 返回结果
  
  # 安全网关模式  
  客户端 → 代理服务(5002) → 输入检测 → 上游模型 → 输出检测 → 返回结果
  
  # 管理模式
  管理界面 → 管理服务(5000) → 配置管理 → 数据库
  ```

### 修复 Fixed
- 🐛 **数据库连接池问题**
  - 解决高并发下数据库连接耗尽的风险
  - 优化三服务架构的连接池分配
  - 减少不必要的数据库操作，提升响应速度

### 技术债务 Technical Debt
- 移除了过时的单一服务启动方式
- 优化了Docker镜像构建策略
- 统一了配置文件管理方式

### 计划中 Planned
- [ ] 多模态内容检测支持（图像、音频）
- [ ] 边缘计算轻量化部署方案
- [ ] 移动端SDK支持
- [ ] 更多语言模型适配
- [ ] 联邦学习隐私保护能力

## [1.0.0] - 2024-08-09

### 新增 Added
- 🛡️ **核心安全检测功能**
  - 12个维度的安全检测能力
  - 提示词攻击检测（S9类别）
  - 内容合规检测（S1-S8, S10-S12类别）
  - 4级风险分类：无风险、低风险、中风险、高风险

- 🧠 **上下文感知检测**
  - 支持多轮对话上下文理解
  - 基于完整会话历史的智能安全评估
  - 上下文相关的风险识别能力

- 🏗️ **完整系统架构**
  - FastAPI后端API服务
  - React前端管理界面
  - PostgreSQL数据库支持
  - Docker容器化部署

- 👥 **用户管理系统**
  - 用户注册、登录、认证
  - API密钥管理
  - 基于JWT的身份验证
  - 管理员权限控制

- ⚙️ **灵活配置管理**
  - 黑名单关键词库管理
  - 白名单关键词库管理
  - 代答模板库配置
  - 用户级别限速配置

- 📊 **可视化管理界面**
  - 实时检测统计仪表盘
  - 检测结果历史查询
  - 风险分布可视化图表
  - 配置管理页面

- 🚦 **限速与监控**
  - 用户级别请求频率限制
  - 实时性能监控
  - 检测结果统计分析
  - 异常访问检测

- 🔌 **API接口**
  - OpenAI兼容的API格式
  - RESTful API设计
  - 完整的API文档
  - 多语言SDK支持

- 🐳 **部署支持**
  - Docker Compose一键部署
  - PostgreSQL数据库初始化脚本
  - 自动健康检查
  - 生产环境配置示例

### 技术特性 Technical Features
- **高性能**：异步处理，支持高并发请求
- **高可用**：容器化部署，支持水平扩展
- **高安全**：数据加密传输，支持完全离线部署
- **高精度**：模型准确率>97%，误报率<0.5%

### 文档 Documentation
- 📖 完整的API文档
- 🚀 快速开始指南
- 🏗️ 详细的产品介绍
- 🤝 贡献指南
- 🔒 安全说明

### 开源模型 Open Source Model
- 🤗 HuggingFace模型开源：`xiangxinai/Xiangxin-Guardrails-Text`
- Apache 2.0许可协议
- 支持中文和英文检测
- 提供完整的推理代码示例

### 客户端库 Client Libraries
- 🐍 Python SDK：`xiangxinai`
- 📱 JavaScript SDK：`xiangxinai-js`
- 🌐 HTTP API兼容OpenAI格式

---

## 版本说明 Version Notes

### 语义化版本控制
- **MAJOR**：不兼容的API修改
- **MINOR**：向后兼容的功能性新增
- **PATCH**：向后兼容的问题修正

### 变更类型说明
- **Added 新增**：新功能
- **Changed 变更**：对现有功能的变更
- **Deprecated 弃用**：不久将移除的功能
- **Removed 移除**：已移除的功能
- **Fixed 修复**：任何bug修复
- **Security 安全**：安全相关的修改

---

## 升级指南 Upgrade Guide

### 从 0.x 升级到 1.0.0
这是首个正式版本，包含以下重大变更：

#### 数据库变更
- 从SQLite迁移到PostgreSQL
- 新的数据库schema和表结构
- 用户数据和配置需要重新导入

#### API变更
- 统一使用OpenAI兼容的API格式
- 新的认证方式（Bearer Token）
- 响应格式标准化

#### 配置变更
- 新的环境变量配置
- Docker Compose配置更新
- 移除了一些过时的配置项

#### 迁移步骤
1. 备份现有数据
2. 更新到新版本代码
3. 运行数据库迁移脚本
4. 更新API调用代码
5. 测试验证功能

---

## 贡献者 Contributors

感谢所有为本项目做出贡献的开发者：

- **核心团队**
  - [@wanglei](mailto:wanglei@xiangxinai.cn) - 项目负责人
  - 象信AI团队

- **社区贡献者**
  - 欢迎您成为第一个社区贡献者！

---

## 支持与联系 Support & Contact

- 📧 **技术支持**：wanglei@xiangxinai.cn
- 🌐 **官方网站**：https://xiangxinai.cn
- 📱 **GitHub Issues**：https://github.com/xiangxinai/xiangxin-guardrails/issues
- 💬 **社区讨论**：https://github.com/xiangxinai/xiangxin-guardrails/discussions

---

*让AI更安全，让应用更可信* 🛡️