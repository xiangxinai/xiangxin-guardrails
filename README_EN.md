# Xiangxin AI Guardrails 🛡️

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0%2B-blue)](https://reactjs.org)
[![HuggingFace](https://img.shields.io/badge/🤗-Models-yellow)](https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text)

> 🚀 **Enterprise-grade AI Safety Guardrails Platform** - Comprehensive security protection for AI applications

Xiangxin AI Guardrails is an open-source and free-for-commercial-use AI security solution. Built on advanced large language models, it provides prompt attack detection, content compliance detection, and supports complete on-premise deployment to build robust security defenses for AI applications.

English | [中文](./README.md)

## ✨ Features

- 🔍 **Prompt Injection Detection** - Identify malicious prompt injections and jailbreak attacks
- 📋 **Content Compliance** - Compliance with AI content safety standards
- 🛠️ **Easy Integration** - OpenAI API compatible, one-line integration
- 🏢 **Private Deployment** - Full local deployment support for data security
- 📊 **Visual Management** - Intuitive web interface for real-time monitoring
- ⚡ **High Performance** - Built with FastAPI for async processing
- 🎯 **Precise Detection** - 12-dimensional safety detection with 4-level risk classification
- 🔧 **Flexible Configuration** - Support for blacklist, whitelist, and response templates

## ⚡ Quick Start

### **Try Online**  
Visit [https://www.xiangxinai.cn/](https://www.xiangxinai.cn/) to register and log in for free.  
In the platform menu **Online Test**, directly enter text for a safety check.  

### **Use API Key**  
In the platform menu **Account Management**, obtain your free API Key.  
Install the Python client library:  
```bash
pip install xiangxinai
```
Python usage example:  
```python
from xiangxinai import XiangxinAI

# Create client
client = XiangxinAI("your-api-key")

# Single-turn detection
response = client.check_prompt("Teach me how to make a bomb")
print(f"Detection result: {response.overall_risk_level}")

# Multi-turn conversation detection (context-aware)
messages = [
    {"role": "user", "content": "I want to study chemistry"},
    {"role": "assistant", "content": "Chemistry is a very interesting subject. Which area would you like to learn about?"},
    {"role": "user", "content": "Teach me the reaction to make explosives"}
]
response = client.check_conversation(messages)
print(f"Detection result: {response.overall_risk_level}")
print(f"All risk categories: {response.all_categories}")
print(f"Compliance check result: {response.result.compliance.risk_level}")
print(f"Compliance risk categories: {response.result.compliance.categories}")
print(f"Security check result: {response.result.security.risk_level}")
print(f"Security risk categories: {response.result.security.categories}")
print(f"Suggested action: {response.suggest_action}")
print(f"Suggested answer: {response.suggest_answer}")
print(f"Is safe: {response.is_safe}")
print(f"Is blocked: {response.is_blocked}")
print(f"Has substitute answer: {response.has_substitute}")
```
Example Output:
```
Detection result: High Risk
Detection result: High Risk
All risk categories: ['Violent Crime']
Compliance check result: High Risk
Compliance risk categories: ['Violent Crime']
Security check result: No Risk
Security risk categories: []
Suggested action: Block
Suggested answer: Sorry, I cannot provide information related to violent crimes.
Is safe: False
Is blocked: True
Has substitute answer: True
```
Use HTTP API
```bash
curl -X POST "https://api.xiangxinai.cn/v1/guardrails" \
    -H "Authorization: Bearer your-api-key" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "Xiangxin-Guardrails-Text",
      "messages": [
        {"role": "user", "content": "Tell me some illegal ways to make money"}
      ]
    }'
```
Example output:
```json
{
    "id": "guardrails-fd59073d2b8d4cfcb4072cee4ddc88b2",
    "result": {
        "compliance": {
            "risk_level": "中风险",
            "categories": [
                "违法犯罪"
            ]
        },
        "security": {
            "risk_level": "无风险",
            "categories": [

            ]
        }
    },
    "overall_risk_level": "中风险",
    "suggest_action": "代答",
    "suggest_answer": "很抱歉，我不能提供涉及违法犯罪的信息。"
}
```

## 🚀 Quick Start

### 🐳 One-Click Docker Deployment (Recommended)

```bash
# 1. Clone the project
git clone https://github.com/xiangxinai/xiangxin-guardrails.git
cd xiangxin-guardrails

# 2. Start the service (includes PostgreSQL database)
docker-compose up -d

# 3. Access the service
# Admin panel: http://localhost:3000
# API docs: http://localhost:5000/docs
```

### 📦 Install Client Library

```bash
pip install xiangxinai
```

### 💻 API Usage Example

#### Synchronous Interface

```python
from xiangxinai import XiangxinAI

# Create client (using local deployment)
client = XiangxinAI(
    api_key="your-api-key",
    base_url="http://localhost:5000/v1"
)

# Single-turn check
response = client.check_prompt("Teach me how to make a bomb")
print(f"Suggested Action: {response.suggest_action}")
print(f"Suggested Answer: {response.suggest_answer}")

# Multi-turn conversation check (context-aware)
messages = [
    {"role": "user", "content": "I want to study chemistry"},
    {"role": "assistant", "content": "Chemistry is a very interesting subject. Which area would you like to learn about?"},
    {"role": "user", "content": "Teach me the reaction to make explosives"}
]
response = client.check_conversation(messages)
print(f"Detection Result: {response.overall_risk_level}")
```

#### Asynchronous Interface

```python
import asyncio
from xiangxinai import AsyncXiangxinAI

async def main():
    # Use async context manager
    async with AsyncXiangxinAI(
        api_key="your-api-key",
        base_url="http://localhost:5000/v1"
    ) as client:
        # Async single-turn check
        response = await client.check_prompt("Teach me how to make a bomb")
        print(f"Suggested Action: {response.suggest_action}")
        
        # Async multi-turn conversation check
        messages = [
            {"role": "user", "content": "I want to study chemistry"},
            {"role": "assistant", "content": "Chemistry is a very interesting subject. Which area would you like to learn about?"},
            {"role": "user", "content": "Teach me the reaction to make explosives"}
        ]
        response = await client.check_conversation(messages)
        print(f"Detection Result: {response.overall_risk_level}")

# Run async function
asyncio.run(main())
```

#### High-Performance Concurrent Processing

```python
import asyncio
from xiangxinai import AsyncXiangxinAI

async def batch_safety_check():
    async with AsyncXiangxinAI(api_key="your-api-key") as client:
        # Process multiple detection requests concurrently
        contents = [
            "I want to learn programming",
            "How's the weather today?",
            "Teach me how to bake a cake",
            "How can I learn English?"
        ]
        
        # Create concurrent tasks
        tasks = [client.check_prompt(content) for content in contents]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Process results
        for i, result in enumerate(results):
            print(f"Content {i+1}: {result.overall_risk_level} - {result.suggest_action}")

asyncio.run(batch_safety_check())
```

### 🌐 HTTP API Example

```bash
curl -X POST "http://localhost:5000/v1/guardrails"      -H "Authorization: Bearer your-api-key"      -H "Content-Type: application/json"      -d '{
       "model": "Xiangxin-Guardrails-Text",
       "messages": [
         {"role": "user", "content": "Tell me some illegal ways to make money"}
       ]
     }'
```

## 🛡️ Safety Detection Capabilities

### Detection Dimensions

| Label | Category | Risk Level | Description |
|-------|----------|------------|-------------|
| S2 | Sensitive Political Topics | 🔴 High | Sensitive political issues or attacks on national security |
| S3 | Disrespect to National Leaders | 🔴 High | Inappropriate remarks about national leaders |
| S5 | Violence & Crime | 🔴 High | Content involving violence or criminal activities |
| S9 | Prompt Attacks | 🔴 High | Malicious prompts attempting to bypass AI safety |
| S1 | General Political Topics | 🟡 Medium | General political discussions |
| S4 | Harm to Minors | 🟡 Medium | Content potentially harmful to minors |
| S6 | Illegal Activities | 🟡 Medium | Teaching or describing illegal activities |
| S7 | Sexual Content | 🟡 Medium | Pornographic or sexually suggestive content |
| S8 | Discriminatory Content | 🟢 Low | Discriminatory speech based on race, gender, religion |
| S10 | Abusive Language | 🟢 Low | Insulting or abusive language |
| S11 | Privacy Invasion | 🟢 Low | Content involving privacy violations |
| S12 | Commercial Violations | 🟢 Low | Business fraud or illegal marketing |

### Processing Strategies

- **🔴 High Risk**: **Substitute** with preset safety responses
- **🟡 Medium Risk**: **Substitute** with gentle reminder responses
- **🟢 Low Risk**: **Allow** normal processing
- **⚪ Safe**: **Allow** no risk content

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend Web UI                       │
│              (React + TypeScript)                      │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP API
┌─────────────────────▼───────────────────────────────────┐
│                  Backend API Service                    │
│                 (Python FastAPI)                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │Guardrails API│ │Config Module │ │Statistics Module│   │
│  └─────────────┘ └──────────────┘ └─────────────────┘   │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │Blacklist Mod│ │Response Mod  │ │Logging Module   │   │
│  └─────────────┘ └──────────────┘ └─────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   SQLite Database                        │
│  Results | Config | Blacklist | Whitelist | Templates   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            Xiangxin AI Guardrails Model                 │
│            (XiangxinGuard-C Model)                     │
│        🤗 HuggingFace Open Source + Cloud API          │
└─────────────────────────────────────────────────────────┘
```

## 📊 Management Interface

### Dashboard
- 📈 Detection statistics display
- 📊 Risk distribution charts
- 📉 Detection trend graphs
- 🎯 Real-time monitoring panel

### Detection Results
- 🔍 Historical detection queries
- 🏷️ Multi-dimensional filtering
- 📋 Detailed result display
- 📤 Data export functionality

### Protection Configuration
- ⚫ Blacklist management
- ⚪ Whitelist management
- 💬 Response template configuration
- ⚙️ Flexible rule settings

## 🤗 Open Source Model

Our guardrail model is open-sourced on HuggingFace:

- **Model**: [xiangxinai/Xiangxin-Guardrails-Text](https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text)
- **Model Size**: 7B parameters
- **Languages**: Chinese, English
- **Model Performance**: Precision: 99.99%, Recall: 98.63%, Response(P95): 274.6ms

```python
# Local model inference example
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "xiangxinai/Xiangxin-Guardrails-Text"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Perform inference
inputs = tokenizer("Test text", return_tensors="pt")
outputs = model(**inputs)
```

## 🤝 Commercial Services

We provide professional AI safety solutions:

### 🎯 Model Fine-tuning Services
- **Industry Customization**: Professional fine-tuning for finance, healthcare, education
- **Scenario Optimization**: Optimize detection for specific use cases
- **Continuous Improvement**: Ongoing optimization based on usage data

### 🏢 Enterprise Support
- **Technical Support**: 24/7 professional technical support
- **SLA Guarantee**: 99.9% availability guarantee
- **Private Deployment**: Completely offline private deployment solutions

### 🔧 Custom Development
- **API Customization**: Custom API interfaces for business needs
- **UI Customization**: Customized management interface and user experience
- **Integration Services**: Deep integration with existing systems

> 📧 **Contact Us**: wanglei@xiangxinai.cn  
> 🌐 **Official Website**: https://xiangxinai.cn

## 🚀 Deployment Guide

### Docker Deployment (Recommended)

```bash
# 1. Clone the project
git clone https://github.com/xiangxinai/xiangxin-guardrails
cd xiangxin-guardrails

# 2. Start services
./scripts/start.sh

# 3. Access services
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

### Manual Deployment

#### Backend Deployment

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file to configure parameters

# Start service
python main.py
```

#### Frontend Deployment

```bash
cd frontend

# Install dependencies
npm install

# Build project
npm run build

# Deploy dist directory using nginx or other web servers
```

### Requirements

- **Python**: 3.8+
- **Node.js**: 16+
- **Memory**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 10GB available space
- **OS**: Linux, macOS, Windows

## 📚 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Introduction Guide](docs/product-introduction.md)

## 🤝 Contributing

We welcome all forms of contributions!

### How to Contribute
- 🐛 [Submit Bug Reports](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- 💡 [Propose New Features](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- 📖 Improve documentation
- 🧪 Add test cases
- 💻 Submit code

### Development Workflow
```bash
# 1. Fork the project
# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Commit changes
git commit -m 'Add some amazing feature'

# 4. Push to branch
git push origin feature/amazing-feature

# 5. Create Pull Request
```

## 📄 License

This project is licensed under [Apache 2.0](LICENSE).

## 🌟 Support Us

If this project helps you, please give us a ⭐️

[![Star History Chart](https://api.star-history.com/svg?repos=XiangxinAI/xiangxin-guardrails&type=Date)](https://star-history.com/#XiangxinAI/xiangxin-guardrails&Date)

## 📞 Contact Us

- 📧 **Technical Support**: wanglei@xiangxinai.cn
- 🌐 **Official Website**: https://xiangxinai.cn
- 💬 **Community**: Join our technical discussion group

---

<div align="center">

**Making AI Safer, Making Applications More Trustworthy** 🛡️

Made with ❤️ by [Xiangxin AI](https://xiangxinai.cn)

</div>