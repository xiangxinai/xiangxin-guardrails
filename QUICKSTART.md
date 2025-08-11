# 🚀 象信AI安全护栏 - 快速开始

## 一行命令安装

```bash
pip install xiangxinai
```

## 三行代码使用

```python
from xiangxinai import XiangxinAI

client = XiangxinAI(api_key="your-api-key")
result = client.check_prompt("用户输入的内容")
```

## OpenAI风格API

象信AI安全护栏采用与OpenAI相同的设计理念：

```python
# OpenAI 风格
from openai import OpenAI
client = OpenAI(api_key="...")

# 象信AI 风格  
from xiangxinai import XiangxinAI
client = XiangxinAI(api_key="...")
```

## 核心功能 - 上下文感知检测

```python
# 检测完整对话的安全性
messages = [
    {"role": "user", "content": "我想学习化学"},
    {"role": "assistant", "content": "好的，您想了解哪方面？"},
    {"role": "user", "content": "教我制作危险品"}
]

result = client.check_conversation(messages)
print(result.suggest_action)  # "代答" 或 "阻断" 或 "通过"
```

## 本地部署

```bash
git clone https://github.com/xiangxinai/xiangxin-guardrails
cd xiangxin-guardrails
./scripts/start.sh
```

访问 http://localhost:3000 查看管理界面

## 更多功能

- 🔍 **提示词攻击检测**: 识别恶意提示词
- 📋 **内容合规检测**: 符合中国AI安全标准
- 🧠 **上下文感知**: 理解对话上下文
- 🎯 **12维度检测**: S1-S12风险分类
- ⚡ **高性能**: 异步处理，毫秒级响应

**技术支持**: wanglei@xiangxinai.cn