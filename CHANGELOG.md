# 更新日志 Changelog

本文件记录象信AI安全护栏平台的所有重要变更。

All notable changes to Xiangxin AI Guardrails platform are documented in this file.

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，
版本号遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [未发布 Unreleased]

### 新增 Added
- 🏗️ **双服务架构重构**
  - 拆分为检测服务(detection_service.py)和管理服务(admin_service.py)
  - 检测服务专注高并发处理，只做认证和写日志文件
  - 管理服务负责完整管理功能和日志导入数据库
  - 数据库连接数优化：从4,800降至176（减少96%）

- 🔌 **私有化集成模式** 🆕
  - 支持与客户现有用户系统深度集成
  - 新增 `STORE_DETECTION_RESULTS` 配置开关，控制检测结果存储方式
  - 客户可通过API管理用户级别的黑白名单和代答模板
  - JWT认证确保用户数据完全隔离
  - 数据库仅存储配置信息，检测数据可选择性存储

- 🚀 **性能优化**
  - 检测服务连接池优化：从150连接/worker降至5连接/worker
  - 新增轻量级DetectionGuardrailService，移除不必要的数据库写入
  - 异步日志导入服务(LogToDbService)，定期将日志文件导入数据库
  - 检测API响应速度显著提升

- 📁 **新增文件**
  - `backend/detection_service.py` - 高并发检测服务入口
  - `backend/admin_service.py` - 低并发管理服务入口
  - `backend/services/detection_guardrail_service.py` - 轻量级检测服务
  - `backend/services/log_to_db_service.py` - 日志导入数据库服务
  - `backend/routers/detection_guardrails.py` - 检测专用路由
  - `backend/start_detection_service.py` - 检测服务启动脚本
  - `backend/start_admin_service.py` - 管理服务启动脚本
  - `backend/start_both_services.sh` - 双服务启动脚本
  - `backend/stop_both_services.sh` - 双服务停止脚本
  - `backend/README_DUAL_SERVICES.md` - 双服务架构说明文档

- 📖 **私有化集成文档和SDK** 🆕
  - `backend/docs/客户集成指南.md` - 详细的客户系统集成说明
  - `backend/docs/API接口文档.md` - 完整的API接口文档
  - `backend/docs/私有化部署指南.md` - Docker和源码部署指导
  - `backend/client-sdk/python/guardrails_client.py` - Python客户端SDK
  - `backend/client-sdk/nodejs/guardrails-client.js` - Node.js客户端SDK

### 变更 Changed
- 🔧 **配置优化**
  - 更新.env配置支持双服务端口配置
  - 新增检测服务配置：DETECTION_PORT、DETECTION_UVICORN_WORKERS
  - 新增管理服务配置：ADMIN_PORT、ADMIN_UVICORN_WORKERS
  - 数据库连接池分离配置
  - 新增 `STORE_DETECTION_RESULTS` 环境变量控制检测结果存储策略

- 📊 **数据流架构重设计**
  ```
  # SaaS模式 (STORE_DETECTION_RESULTS=true)
  检测API → 检测服务 → 认证缓存 + 写日志文件
  日志文件 → 管理服务 → 日志导入器 → 数据库
  管理API → 管理服务 → 数据库查询
  
  # 私有化集成模式 (STORE_DETECTION_RESULTS=false)
  检测API → 检测服务 → 认证缓存 + 写日志文件
  配置API → 管理服务 → 数据库（仅配置数据）
  客户中控台 → 通过JWT管理用户配置
  ```

### 修复 Fixed
- 🐛 **数据库连接池问题**
  - 解决32个worker×150连接=4,800连接的资源浪费问题
  - 修复高并发下数据库连接耗尽的风险
  - 优化内存使用，避免不必要的数据库操作

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