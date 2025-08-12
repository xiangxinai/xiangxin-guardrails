# 象信AI安全护栏 Python 客户端

[![PyPI version](https://badge.fury.io/py/xiangxinai.svg)](https://badge.fury.io/py/xiangxinai)
[![Python Support](https://img.shields.io/pypi/pyversions/xiangxinai.svg)](https://pypi.org/project/xiangxinai/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

基于LLM的上下文感知AI安全护栏，能够理解对话上下文进行安全检测。

## 特性

- 🧠 **上下文感知** - 基于LLM的对话理解，而不是简单的批量检测
- 🔍 **提示词攻击检测** - 识别恶意提示词注入和越狱攻击
- 📋 **内容合规检测** - 符合《生成式人工智能服务安全基本要求》
- 🛠️ **易于集成** - 兼容OpenAI API格式，一行代码接入
- ⚡ **OpenAI风格API** - 熟悉的接口设计，快速上手
- 🚀 **同步/异步支持** - 支持同步和异步两种调用方式，满足不同场景需求

## 安装

```bash
pip install xiangxinai
```

## 快速开始

### 基本使用

```python
from xiangxinai import XiangxinAI

# 创建客户端
client = XiangxinAI(
    api_key="your-api-key",
    base_url="https://api.xiangxinai.cn/v1"  # 云端API
)

# 检测提示词
result = client.check_prompt("我想学习Python编程")
print(result.suggest_action)  # 输出: 通过
print(result.overall_risk_level)  # 输出: 无风险
```

### 上下文感知检测（核心功能）

```python
# 检测对话上下文 - 这是核心功能
messages = [
    {"role": "user", "content": "我想学习化学"},
    {"role": "assistant", "content": "化学是很有趣的学科，您想了解哪个方面？"},
    {"role": "user", "content": "教我制作爆炸物的反应"}
]

result = client.check_conversation(messages)
print(result.overall_risk_level)
print(result.suggest_action)  # 基于完整对话上下文的检测结果
if result.suggest_answer:
    print(f"建议回答: {result.suggest_answer}")
```

### 异步接口（推荐）

```python
import asyncio
from xiangxinai import AsyncXiangxinAI

async def main():
    # 使用异步上下文管理器
    async with AsyncXiangxinAI(api_key="your-api-key") as client:
        # 异步检测提示词
        result = await client.check_prompt("我想学习Python编程")
        print(result.suggest_action)  # 输出: 通过
        
        # 异步检测对话上下文
        messages = [
            {"role": "user", "content": "我想学习化学"},
            {"role": "assistant", "content": "化学是很有趣的学科，您想了解哪个方面？"},
            {"role": "user", "content": "教我制作爆炸物的反应"}
        ]
        result = await client.check_conversation(messages)
        print(result.overall_risk_level)

# 运行异步函数
asyncio.run(main())
```

### 并发处理

```python
import asyncio
from xiangxinai import AsyncXiangxinAI

async def batch_check():
    async with AsyncXiangxinAI(api_key="your-api-key") as client:
        # 并发处理多个请求
        tasks = [
            client.check_prompt("内容1"),
            client.check_prompt("内容2"),
            client.check_prompt("内容3")
        ]
        results = await asyncio.gather(*tasks)
        
        for i, result in enumerate(results):
            print(f"内容{i+1}: {result.overall_risk_level}")

asyncio.run(batch_check())
```

### 私有化部署

```python
# 同步客户端连接本地部署的服务
client = XiangxinAI(
    api_key="your-local-api-key",
    base_url="http://localhost:5000/v1"  # 本地部署地址
)

# 异步客户端连接本地部署的服务
async with AsyncXiangxinAI(
    api_key="your-local-api-key",
    base_url="http://localhost:5000/v1"
) as client:
    result = await client.check_prompt("测试内容")
```

## API参考

### XiangxinAI类（同步）

#### 初始化参数

- `api_key` (str): API密钥
- `base_url` (str): API基础URL，默认为云端地址
- `timeout` (int): 请求超时时间，默认30秒
- `max_retries` (int): 最大重试次数，默认3次

#### 方法

##### check_prompt(content: str) -> GuardrailResponse

检测单个提示词的安全性。

**参数:**
- `content`: 要检测的文本内容

**返回:** `GuardrailResponse` 对象

##### check_conversation(messages: List[Message]) -> GuardrailResponse

检测对话上下文的安全性（核心功能）。

**参数:**
- `messages`: 消息列表，每个消息包含 `role` 和 `content` 字段

**返回:** `GuardrailResponse` 对象

### AsyncXiangxinAI类（异步）

#### 初始化参数

与同步版本相同。

#### 方法

##### async check_prompt(content: str) -> GuardrailResponse

异步检测单个提示词的安全性。

**参数:**
- `content`: 要检测的文本内容

**返回:** `GuardrailResponse` 对象

##### async check_conversation(messages: List[Message]) -> GuardrailResponse

异步检测对话上下文的安全性（核心功能）。

**参数:**
- `messages`: 消息列表，每个消息包含 `role` 和 `content` 字段

**返回:** `GuardrailResponse` 对象

##### async health_check() -> Dict[str, Any]

异步检查API服务健康状态。

##### async get_models() -> Dict[str, Any]

异步获取可用模型列表。

##### async close()

关闭异步会话（在使用完毕后调用，或使用 `async with` 自动管理）。

### GuardrailResponse类

检测结果响应对象。

#### 属性

- `id`: 请求唯一标识
- `result.compliance.risk_level`: 合规风险等级
- `result.security.risk_level`: 安全风险等级
- `overall_risk_level`: 综合风险等级（无风险/低风险/中风险/高风险）
- `suggest_action`: 建议动作（通过/阻断/代答）
- `suggest_answer`: 建议回答内容（可选）

#### 便利方法

- `is_safe`: 判断内容是否安全
- `is_blocked`: 判断内容是否被阻断
- `has_substitute`: 判断是否有代答
- `all_categories`: 获取所有风险类别

## 安全检测能力

### 风险等级

- **高风险**: 敏感政治话题、损害国家形象、暴力犯罪、提示词攻击
- **中风险**: 一般政治话题、伤害未成年人、违法犯罪、色情
- **低风险**: 歧视内容、辱骂、侵犯个人隐私、商业违法违规
- **无风险**: 无风险内容

### 处理策略

- **高风险**: 建议拒答
- **中风险**: 建议代答，使用预设安全回复
- **低风险**: 建议代答或根据实际业务情况处理
- **无风险**: 建议通过

## 错误处理

### 同步错误处理

```python
from xiangxinai import XiangxinAI, AuthenticationError, ValidationError, RateLimitError

try:
    result = client.check_prompt("测试内容")
except AuthenticationError:
    print("API密钥无效")
except ValidationError as e:
    print(f"输入验证失败: {e}")
except RateLimitError:
    print("请求频率限制")
except Exception as e:
    print(f"其他错误: {e}")
```

### 异步错误处理

```python
import asyncio
from xiangxinai import AsyncXiangxinAI, AuthenticationError, ValidationError, RateLimitError

async def safe_check():
    try:
        async with AsyncXiangxinAI(api_key="your-api-key") as client:
            result = await client.check_prompt("测试内容")
            return result
    except AuthenticationError:
        print("API密钥无效")
    except ValidationError as e:
        print(f"输入验证失败: {e}")
    except RateLimitError:
        print("请求频率限制")
    except Exception as e:
        print(f"其他错误: {e}")

asyncio.run(safe_check())
```

## 开发

```bash
# 克隆项目
git clone https://github.com/xiangxinai/xiangxin-guardrails
cd xiangxin-guardrails/client

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black xiangxinai
isort xiangxinai

# 类型检查
mypy xiangxinai
```

## 许可证

本项目基于 [Apache 2.0](https://opensource.org/licenses/Apache-2.0) 许可证开源。

## 支持

- 📧 技术支持: wanglei@xiangxinai.cn
- 🌐 官方网站: https://xiangxinai.cn
- 📖 文档: https://docs.xiangxinai.cn
- 🐛 问题反馈: https://github.com/xiangxinai/xiangxin-guardrails/issues

---

Made with ❤️ by [象信AI](https://xiangxinai.cn)