# 配置集使用指南 / Config Set Usage Guide

## 概述 / Overview

配置集（Config Set）是象信AI安全护栏平台的核心配置管理单元，它将所有防护配置组合在一起，实现灵活的配置管理。

A Config Set is the core configuration management unit in the Xiangxin AI Guardrails Platform, grouping all protection settings together for flexible configuration management.

## 配置集包含的内容 / What's in a Config Set

一个配置集包含两部分：

A config set contains two parts:

### 1. 直接配置 / Direct Configuration

这些配置直接在配置集中设置：

These settings are configured directly in the config set:

- ✅ **风险类型开关** (Risk Type Switches) - S1 到 S12
- ✅ **敏感度阈值** (Sensitivity Thresholds) - 高/中/低敏感度阈值
- ✅ **触发等级** (Trigger Level) - 检测触发的最低敏感度等级
- ✅ **描述** (Description) - 配置集的描述信息

### 2. 关联配置 / Associated Configurations

这些配置在各自的管理页面创建，然后关联到配置集：

These configurations are created in their respective management pages, then associated with the config set:

- 🔗 **黑名单** (Blacklists) - 已支持配置集关联 / Config set association supported
- 🔗 **白名单** (Whitelists) - 已有 template_id 字段 / Has template_id field
- 🔗 **响应模板** (Response Templates) - 已有 template_id 字段 / Has template_id field
- 🔗 **知识库** (Knowledge Bases) - 已有 template_id 字段 / Has template_id field
- 🔗 **数据安全实体** (Data Security Entities) - 已有 template_id 字段 / Has template_id field
- 🔗 **封禁策略** (Ban Policies) - 已有 template_id 字段 / Has template_id field

## 使用流程 / Usage Flow

### 方案 A：先创建配置集，后关联配置

**Approach A: Create Config Set First, Then Associate Configurations**

```
1. 创建配置集 (Create Config Set)
   └─ 导航到"防护配置模版" (Navigate to "Protection Templates")
   └─ 点击"创建模版" (Click "Create Template")
   └─ 设置风险类型和敏感度 (Configure risk types and sensitivity)
   └─ 保存 (Save)

2. 创建并关联黑名单 (Create and Associate Blacklist)
   └─ 导航到"黑名单" (Navigate to "Blacklist")
   └─ 点击"添加黑名单" (Click "Add Blacklist")
   └─ 在"配置集"下拉框中选择刚创建的配置集 (Select the config set)
   └─ 输入关键词 (Enter keywords)
   └─ 保存 (Save)

3. 创建并关联白名单、响应模板等 (Create and associate whitelists, response templates, etc.)
   └─ 同样的流程 (Same process)

4. 查看配置集详情 (View Config Set Details)
   └─ 在配置集列表点击"查看" (Click "View" in config set list)
   └─ 查看所有关联的配置 (See all associated configurations)
```

### 方案 B：先创建配置，后关联到配置集

**Approach B: Create Configurations First, Then Associate with Config Set**

```
1. 创建黑名单 (Create Blacklist)
   └─ 导航到"黑名单" (Navigate to "Blacklist")
   └─ 创建黑名单，暂不选择配置集 (Create blacklist without selecting config set)
   └─ 保存 (Save)

2. 创建配置集 (Create Config Set)
   └─ 导航到"防护配置模版" (Navigate to "Protection Templates")
   └─ 创建配置集 (Create config set)

3. 编辑黑名单，关联到配置集 (Edit Blacklist, Associate with Config Set)
   └─ 返回黑名单列表 (Go back to blacklist list)
   └─ 点击"编辑" (Click "Edit")
   └─ 选择配置集 (Select config set)
   └─ 保存 (Save)
```

## 为什么采用这种设计？

**Why This Design?**

### 优点 / Advantages

1. **灵活性** (Flexibility)
   - 可以将同一个黑名单关联到多个配置集（通过复制）
   - 可以独立管理各个配置模块
   - 可以先创建配置，后决定关联到哪个配置集

2. **清晰的职责分离** (Clear Separation of Concerns)
   - 配置集负责核心检测设置（风险类型、敏感度）
   - 各个配置模块负责具体的规则（黑名单关键词、白名单等）

3. **易于扩展** (Easy to Extend)
   - 添加新的配置模块很简单
   - 不需要修改配置集的数据结构

### 当前状态 / Current Status

✅ **已完成** (Completed):
- 配置集的创建、编辑、删除、克隆 (Config set CRUD and clone)
- 配置集详情页面（折叠式模块展示所有关联）(Config set detail page with collapsible modules)
- 黑名单的配置集关联 (Blacklist config set association)

🚧 **待完成** (To Do):
- 白名单、响应模板、知识库、数据安全、封禁策略的配置集选择器
- 在配置集详情页面直接管理关联（添加/移除）

## 关于"为什么创建配置集时看不到其他配置"的说明

**About "Why Can't I See Other Configurations When Creating a Config Set"**

这是**设计使然**，不是缺陷：

This is **by design**, not a bug:

1. **配置集创建时**：只设置核心检测参数（风险类型、敏感度）
   **When creating a config set**: Only set core detection parameters

2. **黑名单/白名单等**：在各自的管理页面创建，选择关联到哪个配置集
   **Blacklists/Whitelists etc**: Create in their respective pages, select which config set to associate

3. **查看完整配置**：在配置集详情页面查看所有关联的配置
   **View complete configuration**: Use the config set detail page to see all associations

## 示例场景 / Example Scenario

### 场景：为生产环境和测试环境创建不同的配置

**Scenario: Create Different Configurations for Production and Test Environments**

```
步骤 1: 创建两个配置集 (Step 1: Create two config sets)
├─ "生产环境配置" (Production Config)
│  ├─ 启用所有风险类型 (Enable all risk types)
│  └─ 高敏感度 (High sensitivity)
│
└─ "测试环境配置" (Test Config)
   ├─ 只启用关键风险类型 (Only enable critical risk types)
   └─ 低敏感度 (Low sensitivity)

步骤 2: 创建黑名单并关联 (Step 2: Create blacklists and associate)
├─ "生产黑名单" → 关联到"生产环境配置"
│  (Production Blacklist → Associate with Production Config)
│
└─ "测试黑名单" → 关联到"测试环境配置"
   (Test Blacklist → Associate with Test Config)

步骤 3: 创建 API Key 并绑定配置集 (Step 3: Create API keys and bind to config sets)
├─ "Production API Key" → 绑定到"生产环境配置"
│  (Bind to Production Config)
│
└─ "Test API Key" → 绑定到"测试环境配置"
   (Bind to Test Config)

结果 (Result):
- 使用 Production API Key 调用时，使用生产环境的严格配置
  (When calling with Production API Key, use strict production settings)
- 使用 Test API Key 调用时，使用测试环境的宽松配置
  (When calling with Test API Key, use relaxed test settings)
```

## 快速开始 / Quick Start

### 1. 创建你的第一个配置集

1. 登录平台 (Login to the platform)
2. 导航到 **配置 → 防护配置模版** (Navigate to **Config → Protection Templates**)
3. 点击 **创建模版** (Click **Create Template**)
4. 填写：
   - 名称：例如"我的第一个配置集" (Name: e.g., "My First Config Set")
   - 描述：例如"用于测试的配置集" (Description: e.g., "Config set for testing")
   - 选择要启用的风险类型 (Select risk types to enable)
   - 设置敏感度阈值 (Set sensitivity thresholds)
5. 点击 **保存** (Click **Save**)

### 2. 创建黑名单并关联到配置集

1. 导航到 **配置 → 黑名单** (Navigate to **Config → Blacklist**)
2. 点击 **添加黑名单** (Click **Add Blacklist**)
3. 填写：
   - 名称：例如"测试黑名单" (Name: e.g., "Test Blacklist")
   - **配置集**：选择刚创建的配置集 (Config Set: Select the config set you just created)
   - 关键词：输入一些测试关键词 (Keywords: Enter some test keywords)
4. 点击 **确定** (Click **OK**)

### 3. 查看配置集详情

1. 返回 **防护配置模版** (Go back to **Protection Templates**)
2. 找到你创建的配置集 (Find the config set you created)
3. 点击 **查看** (Click **View**)
4. 你会看到：
   - 基础信息 (Basic information)
   - 风险检测配置 (Risk detection configuration)
   - 关联的黑名单（应该能看到刚创建的黑名单）(Associated blacklists - should see the blacklist you just created)

## 常见问题 / FAQ

### Q: 为什么我在创建配置集时看不到黑名单选项？

**A: 这是设计使然。** 黑名单是在黑名单管理页面创建的，然后通过"配置集"字段关联到配置集。这样设计的好处是：
- 可以先创建黑名单，后决定关联到哪个配置集
- 可以轻松修改黑名单的关联配置集
- 各个配置模块独立管理，职责清晰

**A: This is by design.** Blacklists are created in the blacklist management page, then associated with a config set via the "Config Set" field. Benefits:
- Create blacklists first, decide later which config set to associate
- Easily change which config set a blacklist is associated with
- Independent management of each configuration module

### Q: 如果不选择配置集会怎样？

**A: 如果在创建黑名单/白名单时不选择配置集，该配置会全局应用（对所有配置集生效）。**

**A: If you don't select a config set when creating a blacklist/whitelist, it applies globally (to all config sets).**

### Q: 可以将同一个黑名单关联到多个配置集吗？

**A: 数据库层面不支持直接关联到多个配置集（template_id 是单值字段）。但你可以克隆黑名单，然后关联到不同的配置集。**

**A: The database doesn't support direct association with multiple config sets (template_id is a single-value field). But you can clone the blacklist and associate copies with different config sets.**

### Q: 我修改了配置集，需要重启服务吗？

**A: 不需要。** 配置是动态加载的。当 API Key 调用检测服务时，会实时读取绑定的配置集及其关联的所有配置。

**A: No.** Configurations are loaded dynamically. When an API Key calls the detection service, it reads the bound config set and all associated configurations in real-time.

## 未来改进 / Future Improvements

1. **一站式创建** - 在创建配置集时直接创建和选择关联配置
   **One-stop creation** - Create and select associated configs directly when creating a config set

2. **批量关联** - 批量将多个黑名单关联到同一个配置集
   **Bulk association** - Associate multiple blacklists with the same config set in bulk

3. **配置集比较** - 对比两个配置集的差异
   **Config set comparison** - Compare differences between two config sets

4. **深度克隆** - 克隆配置集时同时克隆所有关联的配置
   **Deep clone** - Clone all associated configurations when cloning a config set
