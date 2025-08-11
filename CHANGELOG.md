# 更新日志 Changelog

本文件记录象信AI安全护栏平台的所有重要变更。

All notable changes to Xiangxin AI Guardrails platform are documented in this file.

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，
版本号遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [未发布 Unreleased]

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