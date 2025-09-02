# 更新日志 Changelog

本文件记录象信AI安全护栏平台的所有重要变更。

All notable changes to Xiangxin AI Guardrails platform are documented in this file.

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，
版本号遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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