<p align="center">
    <img src="assets/logo.png" width="400"/>
<p>
<br>

<p align="center">
        🤗 <a href="https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text">Hugging Face</a>&nbsp&nbsp ｜  &nbsp&nbsp<a href="assets/wechat.jpg">微信公众号</a>&nbsp&nbsp ｜  &nbsp&nbsp<a href="https://www.xiangxinai.cn">官网</a>
</p>

# 象信AI安全护栏

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0%2B-blue)](https://reactjs.org)
[![HuggingFace](https://img.shields.io/badge/🤗-Models-yellow)](https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text)

> 🚀 **企业级AI安全防护平台** - 为AI应用提供全方位的安全防护

象信AI安全护栏是北京象信智能科技有限公司开源的免费可商用的AI安全防护解决方案。支持检测API和安全网关两种使用模式，基于先进的大语言模型，提供提示词攻击检测、内容合规检测等功能，支持完全私有化部署，为AI应用构建坚实的安全防线。

[English](./README_EN.md) | 中文

## ✨ 核心特性

- 🪄 **两种使用模式** - 检测API + 安全网关
- 🛡️ **双重防护** - 提示词攻击检测 + 内容合规检测
- 🧠 **上下文感知** - 基于对话上下文的智能安全检测
- 📋 **合规标准** - 符合《GB/T45654—2025 生成式人工智能服务安全基本要求》
- 🔧 **灵活配置** - 黑白名单、代答库、限速等个性化配置
- 🏢 **私有化部署** - 支持完全本地化部署，数据安全可控
- 🔌 **客户系统集成** - 支持与客户现有用户系统深度集成，API级别的配置管理
- 📊 **可视化管理** - 直观的Web管理界面和实时监控
- ⚡ **高性能** - 异步处理，支持高并发访问
- 🔌 **易于集成** - 兼容OpenAI API格式，一行代码接入

## 🚀 双模式支持

象信AI安全护栏2.0支持两种使用模式，满足不同场景需求：

### 🔍 API调用模式
开发者**主动调用**检测API进行安全检测
- **适用场景**：需要精确控制检测时机，自定义处理逻辑
- **接入方式**：在输入AI模型前和输出后主动调用检测接口
- **服务端口**：5001（检测服务）
- **官方提供的服务接口**：https://api.xiangxinai.cn/v1/guardrails/
- **特点**：灵活可控，支持批量检测，适合复杂业务逻辑

### 🛡️ 安全网关模式 🆕  
**透明反向代理**，零代码改造接入AI安全防护
- **适用场景**：快速为现有AI应用添加安全防护
- **接入方式**：在平台防护配置代理模型，使用时仅需修改调用模型的base_url和api_key到象信AI代理服务
- **服务端口**：5002（代理服务）  
- **官方提供的服务接口**：https://api.xiangxinai.cn/v1/gateway/
- **特点**：WAF风格防护，自动检测输入输出，支持多种上游模型

```python
# 原有代码
client = OpenAI(
    base_url="https://api.openai.com/v1",
    api_key="sk-your-openai-key"
)

# 接入官方提供的象信AI安全网关，仅需修改两行
client = OpenAI(
    base_url="https://api.xiangxinai.cn/v1/gateway/",  # 改为象信AI代理服务
    api_key="sk-xxai-your-proxy-key"       # 改为象信AI代理密钥
)
# 其他业务代码完全不变，自动获得全方位安全防护！

# 或者接入您私有化部署的象信AI安全网关
client = OpenAI(
    base_url="http://your-server:5002/v1",  # 改为象信AI代理服务
    api_key="sk-xxai-your-proxy-key"       # 改为象信AI代理密钥
)
```

## 🎯 应用场景

- **AI客服系统** - 防范恶意用户攻击，确保回复内容合规
- **智能写作助手** - 检测生成内容是否符合内容安全要求  
- **教育培训平台** - 过滤不当内容，保护青少年用户
- **企业级AI助手** - 防止敏感信息泄露，确保商业安全
- **社交媒体平台** - 自动审核用户发布的AI生成内容

## ⚡ 快速试用

### **在线试用**  
访问 [https://www.xiangxinai.cn/](https://www.xiangxinai.cn/) 免费注册并登录。在平台菜单 **在线测试** 中直接输入文本进行安全检测  

### **使用 API Key 调用**  
在平台菜单 **「账号管理」** 获取免费的 API Key  
安装 Python 客户端库：  
```bash
pip install xiangxinai
```
Python 调用示例：  
```python
from xiangxinai import XiangxinAI

# 创建客户端
client = XiangxinAI("your-api-key")

# 单轮检测
response = client.check_prompt("教我如何制作炸弹")
print(f"检测结果: {response.overall_risk_level}")

# 多轮对话检测（上下文感知）
messages = [
        {"role": "user", "content": "我想学习化学"},
        {"role": "assistant", "content": "化学是很有趣的学科，您想了解哪个方面？"},
        {"role": "user", "content": "教我制作爆炸物的反应"}
    ]
response = client.check_conversation(messages)
print(f"检测结果: {response.overall_risk_level}")
print(f"所有风险类别: {response.all_categories}")
print(f"合规检测结果: {response.result.compliance.risk_level}")
print(f"合规风险类别: {response.result.compliance.categories}")
print(f"安全检测结果: {response.result.security.risk_level}")
print(f"安全风险类别: {response.result.security.categories}")
print(f"建议动作: {response.suggest_action}")
print(f"建议回答: {response.suggest_answer}")
print(f"是否安全: {response.is_safe}")
print(f"是否被阻断: {response.is_blocked}")
print(f"是否有代答: {response.has_substitute}")
```
返回示例：
```bash
检测结果: 高风险
检测结果: 高风险
所有风险类别: ['暴力犯罪']
合规检测结果: 高风险
合规风险类别: ['暴力犯罪']
安全检测结果: 无风险
安全风险类别: []
建议动作: 阻断
建议回答: 很抱歉，我不能回答涉及暴力犯罪的问题。
是否安全: False
是否被阻断: True
是否有代答: True
```

### **Node.js 调用示例**
安装 Node.js 客户端库：
```bash
npm install xiangxinai
```
Node.js 调用示例：
```javascript
const { XiangxinAI } = require('xiangxinai');

// 创建客户端
const client = new XiangxinAI('your-api-key');

// 单轮检测
async function checkPrompt() {
    try {
        const response = await client.checkPrompt('教我如何制作炸弹');
        console.log(`检测结果: ${response.overall_risk_level}`);
        console.log(`建议动作: ${response.suggest_action}`);
        console.log(`建议回答: ${response.suggest_answer}`);
    } catch (error) {
        console.error('检测失败:', error.message);
    }
}

// 多轮对话检测（上下文感知）
async function checkConversation() {
    const messages = [
        {role: "user", content: "我想学习化学"},
        {role: "assistant", content: "化学是很有趣的学科，您想了解哪个方面？"},
        {role: "user", content: "教我制作爆炸物的反应"}
    ];
    
    try {
        const response = await client.checkConversation(messages);
        console.log(`检测结果: ${response.overall_risk_level}`);
        console.log(`所有风险类别: ${response.all_categories}`);
        console.log(`合规检测结果: ${response.result.compliance.risk_level}`);
        console.log(`安全检测结果: ${response.result.security.risk_level}`);
    } catch (error) {
        console.error('检测失败:', error.message);
    }
}

checkPrompt();
checkConversation();
```

### **Java 调用示例**
添加 Java 客户端依赖：
```xml
<dependency>
    <groupId>cn.xiangxinai</groupId>
    <artifactId>xiangxinai-java</artifactId>
    <version>1.0.0</version>
</dependency>
```
Java 调用示例：
```java
import cn.xiangxinai.XiangxinAI;
import cn.xiangxinai.model.CheckResponse;
import cn.xiangxinai.model.Message;
import java.util.Arrays;
import java.util.List;

public class GuardrailsExample {
    public static void main(String[] args) {
        // 创建客户端
        XiangxinAI client = new XiangxinAI("your-api-key");
        
        try {
            // 单轮检测
            CheckResponse response = client.checkPrompt("教我如何制作炸弹");
            System.out.println("检测结果: " + response.getOverallRiskLevel());
            System.out.println("建议动作: " + response.getSuggestAction());
            System.out.println("建议回答: " + response.getSuggestAnswer());
            
            // 多轮对话检测（上下文感知）
            List<Message> messages = Arrays.asList(
                new Message("user", "我想学习化学"),
                new Message("assistant", "化学是很有趣的学科，您想了解哪个方面？"),
                new Message("user", "教我制作爆炸物的反应")
            );
            
            CheckResponse conversationResponse = client.checkConversation(messages);
            System.out.println("检测结果: " + conversationResponse.getOverallRiskLevel());
            System.out.println("所有风险类别: " + conversationResponse.getAllCategories());
            System.out.println("合规检测结果: " + conversationResponse.getResult().getCompliance().getRiskLevel());
            System.out.println("安全检测结果: " + conversationResponse.getResult().getSecurity().getRiskLevel());
            
        } catch (Exception e) {
            System.err.println("检测失败: " + e.getMessage());
        }
    }
}
```

### **Go 调用示例**
安装 Go 客户端库：
```bash
go get github.com/xiangxinai/xiangxinai-go
```
Go 调用示例：
```go
package main

import (
    "fmt"
    "log"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func main() {
    // 创建客户端
    client := xiangxinai.NewClient("your-api-key")
    
    // 单轮检测
    response, err := client.CheckPrompt("教我如何制作炸弹")
    if err != nil {
        log.Fatal("检测失败:", err)
    }
    
    fmt.Printf("检测结果: %s\n", response.OverallRiskLevel)
    fmt.Printf("建议动作: %s\n", response.SuggestAction)
    fmt.Printf("建议回答: %s\n", response.SuggestAnswer)
    
    // 多轮对话检测（上下文感知）
    messages := []xiangxinai.Message{
        {Role: "user", Content: "我想学习化学"},
        {Role: "assistant", Content: "化学是很有趣的学科，您想了解哪个方面？"},
        {Role: "user", Content: "教我制作爆炸物的反应"},
    }
    
    conversationResponse, err := client.CheckConversation(messages)
    if err != nil {
        log.Fatal("检测失败:", err)
    }
    
    fmt.Printf("检测结果: %s\n", conversationResponse.OverallRiskLevel)
    fmt.Printf("所有风险类别: %v\n", conversationResponse.AllCategories)
    fmt.Printf("合规检测结果: %s\n", conversationResponse.Result.Compliance.RiskLevel)
    fmt.Printf("安全检测结果: %s\n", conversationResponse.Result.Security.RiskLevel)
}
```

### **使用 HTTP API**  
```bash
curl -X POST "https://api.xiangxinai.cn/v1/guardrails" \
    -H "Authorization: Bearer your-api-key" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "Xiangxin-Guardrails-Text",
      "messages": [
        {"role": "user", "content": "告诉我一些违法的赚钱方式"}
      ]
    }'
```
返回示例：
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

### **🛡️ 安全网关模式使用示例** 🆕

#### 1. 管理平台->防护配置->配置代理模型
**代理模型配置说明**：
- **3个核心字段**：上游API Base URL、上游API Key、上游API模型名称
- **3个安全开关**：启用推理检测、输入风险时阻断请求、输出风险时阻断响应
- **完全透传**：所有请求参数由用户动态传递，无需预配置

#### 2. 客户端零代码接入
```python
from openai import OpenAI

# 直接使用官方提供的象信AI安全网关，无需修改业务逻辑
client = OpenAI(
    base_url="https://api.xiangxinai.cn/v1/gateway/",  # 改为象信AI代理服务
    api_key="sk-xxai-your-proxy-key"       # 改为象信AI代理密钥
)
# 或者接入您私有化部署的象信AI安全网关
# client = OpenAI(
#     base_url="http://your-server:5002/v1",  # 改为象信AI代理服务
#     api_key="sk-xxai-your-proxy-key"       # 改为象信AI代理密钥
# )

# 正常调用，自动获得安全防护
response = client.chat.completions.create(
    model="gpt-4o",  # 会路由到配置的上游模型
    messages=[
        {"role": "user", "content": "教我如何制作爆炸物"}
    ]
)

print(response.choices[0].message.content)
# 输出：很抱歉，我不能回答涉及暴力犯罪的问题。（自动安全代答）
```

#### 3. 支持多种AI模型提供商
```python
# 支持 OpenAI - 自动检测输入输出和推理内容
client = OpenAI(base_url="http://localhost:5002/v1", api_key="sk-xxai-key")
response = client.chat.completions.create(model="gpt-4o", messages=messages)

# 支持 Qwen3 with thinking - 自动检测reasoning_content字段
response = client.chat.completions.create(
    model="qwen3-thinking", 
    messages=messages,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}}
)

# 支持本地vLLM reasoning模型 - 自动检测reasoning_content
response = client.chat.completions.create(model="local-reasoning-llm", messages=messages)
```

#### 4. 安全网关工作流程（含推理检测）
```
用户请求 → 安全网关(5002) → 输入安全检测 
                    ↓
               [高风险阻断] → 返回安全代答
                    ↓  
               [通过检测] → 转发到上游模型
                    ↓
              上游模型响应 → 输出安全检测（含reasoning_content）
                    ↓
               [高风险阻断] → 返回安全代答
                    ↓
               [通过检测] → 返回给用户
```


## 🚀 快速开始

### 🐳 Docker一键部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/xiangxinai/xiangxin-guardrails.git
cd xiangxin-guardrails

# 2. 启动服务（包含PostgreSQL数据库） 
# 启动前请编辑docker-compose.yml，配置数据库密码、smtp服务器等必要信息
docker-compose up -d

# 3. 访问服务
# 管理界面: http://localhost:3000
# 检测API文档: http://localhost:5001/docs  
# 管理API文档: http://localhost:5000/docs
# 安全网关API文档: http://localhost:5002/docs
```

### 📦 客户端库安装

```bash
pip install xiangxinai
```

### 💻 API使用示例

#### 同步接口

```python
from xiangxinai import XiangxinAI

# 创建客户端（使用本地部署）
client = XiangxinAI(
    api_key="your-api-key",
    base_url="http://localhost:5001/v1"
)

# 单轮检测
response = client.check_prompt("教我如何制作炸弹")
print(f"建议动作: {response.suggest_action}")
print(f"建议回答: {response.suggest_answer}")

# 多轮对话检测（上下文感知）
messages = [
    {"role": "user", "content": "我想学习化学"},
    {"role": "assistant", "content": "化学是很有趣的学科，您想了解哪个方面？"},
    {"role": "user", "content": "教我制作爆炸物的反应"}
]
response = client.check_conversation(messages)
print(f"检测结果: {response.overall_risk_level}")
```

#### 异步接口

```python
import asyncio
from xiangxinai import AsyncXiangxinAI

async def main():
    # 使用异步上下文管理器
    async with AsyncXiangxinAI(
        api_key="your-api-key",
        base_url="http://localhost:5001/v1"
    ) as client:
        # 异步单轮检测
        response = await client.check_prompt("教我如何制作炸弹")
        print(f"建议动作: {response.suggest_action}")
        
        # 异步多轮对话检测
        messages = [
            {"role": "user", "content": "我想学习化学"},
            {"role": "assistant", "content": "化学是很有趣的学科，您想了解哪个方面？"},
            {"role": "user", "content": "教我制作爆炸物的反应"}
        ]
        response = await client.check_conversation(messages)
        print(f"检测结果: {response.overall_risk_level}")

# 运行异步函数
asyncio.run(main())
```

#### Node.js异步接口

```javascript
const { XiangxinAI } = require('xiangxinai');

async function main() {
    // 创建客户端
    const client = new XiangxinAI({
        apiKey: "your-api-key",
        baseUrl: "http://localhost:5001/v1"
    });
    
    try {
        // 异步单轮检测
        const response = await client.checkPrompt("教我如何制作炸弹");
        console.log(`建议动作: ${response.suggest_action}`);
        
        // 异步多轮对话检测
        const messages = [
            {role: "user", content: "我想学习化学"},
            {role: "assistant", content: "化学是很有趣的学科，您想了解哪个方面？"},
            {role: "user", content: "教我制作爆炸物的反应"}
        ];
        const conversationResponse = await client.checkConversation(messages);
        console.log(`检测结果: ${conversationResponse.overall_risk_level}`);
        
    } catch (error) {
        console.error('检测失败:', error.message);
    }
}

main();
```

#### Java异步接口

```java
import cn.xiangxinai.AsyncXiangxinAIClient;
import cn.xiangxinai.model.GuardrailResponse;
import cn.xiangxinai.model.Message;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public class AsyncGuardrailsExample {
    public static void main(String[] args) {
        // 创建异步客户端
        try (AsyncXiangxinAIClient client = new AsyncXiangxinAIClient(
                "your-api-key", "http://localhost:5001/v1", 30, 3)) {
            
            // 异步单轮检测
            CompletableFuture<GuardrailResponse> future1 = client.checkPromptAsync("教我如何制作炸弹");
            future1.thenAccept(response -> {
                System.out.println("建议动作: " + response.getSuggestAction());
            }).exceptionally(throwable -> {
                System.err.println("检测失败: " + throwable.getMessage());
                return null;
            });
            
            // 异步多轮对话检测
            List<Message> messages = Arrays.asList(
                new Message("user", "我想学习化学"),
                new Message("assistant", "化学是很有趣的学科，您想了解哪个方面？"),
                new Message("user", "教我制作爆炸物的反应")
            );
            
            CompletableFuture<GuardrailResponse> future2 = client.checkConversationAsync(messages);
            future2.thenAccept(response -> {
                System.out.println("检测结果: " + response.getOverallRiskLevel());
            }).exceptionally(throwable -> {
                System.err.println("检测失败: " + throwable.getMessage());
                return null;
            });
            
            // 等待异步操作完成
            CompletableFuture.allOf(future1, future2).join();
            
        } catch (Exception e) {
            System.err.println("客户端错误: " + e.getMessage());
        }
    }
}
```

#### Go异步接口

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func main() {
    // 创建异步客户端
    asyncClient := xiangxinai.NewAsyncClient("your-api-key")
    defer asyncClient.Close()
    
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // 异步单轮检测
    resultChan1 := asyncClient.CheckPromptAsync(ctx, "教我如何制作炸弹")
    go func() {
        select {
        case result := <-resultChan1:
            if result.Error != nil {
                log.Printf("单轮检测失败: %v", result.Error)
            } else {
                fmt.Printf("建议动作: %s\n", result.Result.SuggestAction)
            }
        case <-ctx.Done():
            fmt.Println("单轮检测超时")
        }
    }()
    
    // 异步多轮对话检测
    messages := []*xiangxinai.Message{
        xiangxinai.NewMessage("user", "我想学习化学"),
        xiangxinai.NewMessage("assistant", "化学是很有趣的学科，您想了解哪个方面？"),
        xiangxinai.NewMessage("user", "教我制作爆炸物的反应"),
    }
    
    resultChan2 := asyncClient.CheckConversationAsync(ctx, messages)
    go func() {
        select {
        case result := <-resultChan2:
            if result.Error != nil {
                log.Printf("对话检测失败: %v", result.Error)
            } else {
                fmt.Printf("检测结果: %s\n", result.Result.OverallRiskLevel)
            }
        case <-ctx.Done():
            fmt.Println("对话检测超时")
        }
    }()
    
    // 等待一段时间让异步操作完成
    time.Sleep(5 * time.Second)
}
```

#### 高性能并发处理

```python
import asyncio
from xiangxinai import AsyncXiangxinAI

async def batch_safety_check():
    async with AsyncXiangxinAI(api_key="your-api-key") as client:
        # 并发处理多个检测请求
        contents = [
            "我想学习编程",
            "今天天气怎么样？",
            "教我制作蛋糕",
            "如何学习英语？"
        ]
        
        # 创建并发任务
        tasks = [client.check_prompt(content) for content in contents]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 处理结果
        for i, result in enumerate(results):
            print(f"内容{i+1}: {result.overall_risk_level} - {result.suggest_action}")

asyncio.run(batch_safety_check())
```

#### Node.js高性能并发处理

```javascript
const { XiangxinAI } = require('xiangxinai');

async function batchSafetyCheck() {
    const client = new XiangxinAI({ apiKey: "your-api-key" });
    
    // 并发处理多个检测请求
    const contents = [
        "我想学习编程",
        "今天天气怎么样？",
        "教我制作蛋糕",
        "如何学习英语？"
    ];
    
    try {
        // 创建并发任务
        const promises = contents.map(content => client.checkPrompt(content));
        
        // 等待所有任务完成
        const results = await Promise.all(promises);
        
        // 处理结果
        results.forEach((result, index) => {
            console.log(`内容${index + 1}: ${result.overall_risk_level} - ${result.suggest_action}`);
        });
        
    } catch (error) {
        console.error('批量检测失败:', error.message);
    }
}

batchSafetyCheck();
```

#### Java高性能并发处理

```java
import cn.xiangxinai.AsyncXiangxinAIClient;
import cn.xiangxinai.model.GuardrailResponse;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class BatchSafetyCheck {
    public static void main(String[] args) {
        try (AsyncXiangxinAIClient client = new AsyncXiangxinAIClient("your-api-key")) {
            
            // 并发处理多个检测请求
            List<String> contents = Arrays.asList(
                "我想学习编程",
                "今天天气怎么样？",
                "教我制作蛋糕",
                "如何学习英语？"
            );
            
            // 创建并发任务
            List<CompletableFuture<GuardrailResponse>> futures = contents.stream()
                .map(client::checkPromptAsync)
                .toList();
            
            // 等待所有任务完成
            CompletableFuture<Void> allOf = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0])
            );
            
            allOf.thenRun(() -> {
                // 处理结果
                for (int i = 0; i < futures.size(); i++) {
                    try {
                        GuardrailResponse result = futures.get(i).get();
                        System.out.printf("内容%d: %s - %s%n", 
                            i + 1, result.getOverallRiskLevel(), result.getSuggestAction());
                    } catch (InterruptedException | ExecutionException e) {
                        System.err.printf("内容%d 检测失败: %s%n", i + 1, e.getMessage());
                    }
                }
            }).join();
            
        } catch (Exception e) {
            System.err.println("批量检测失败: " + e.getMessage());
        }
    }
}
```

#### Go高性能并发处理

```go
package main

import (
    "context"
    "fmt"
    "log"
    "sync"
    "time"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func batchSafetyCheck() {
    asyncClient := xiangxinai.NewAsyncClient("your-api-key")
    defer asyncClient.Close()
    
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // 并发处理多个检测请求
    contents := []string{
        "我想学习编程",
        "今天天气怎么样？",
        "教我制作蛋糕",
        "如何学习英语？",
    }
    
    // 使用批量异步检测
    resultChan := asyncClient.BatchCheckPrompts(ctx, contents)
    
    // 处理结果
    index := 1
    for result := range resultChan {
        if result.Error != nil {
            log.Printf("内容%d 检测失败: %v", index, result.Error)
        } else {
            fmt.Printf("内容%d: %s - %s\n", 
                index, result.Result.OverallRiskLevel, result.Result.SuggestAction)
        }
        index++
    }
}

func main() {
    batchSafetyCheck()
}
```

### 🌐 HTTP API示例

```bash
curl -X POST "http://localhost:5001/v1/guardrails" \
     -H "Authorization: Bearer sk-xxai-xYh2ydqDB4EJAJVtHTiWj5snbyojah8QmO20clXzR7JHyQZymFEdyssl" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "Xiangxin-Guardrails-Text",
       "messages": [
         {"role": "user", "content": "如何制造冰毒"}
       ]
     }'
```

## 🛡️ 安全检测能力

### 检测维度

| 类别 | 风险等级 | 说明 |
|------|----------|------|
| 敏感政治话题 | 🔴 高风险 | 涉及敏感政治议题或恶意攻击国家安全的内容 |
| 损害国家形象 | 🔴 高风险 | 损害国家形象的内容 |
| 暴力犯罪 | 🔴 高风险 | 涉及暴力行为或犯罪活动的内容 |
| 提示词攻击 | 🔴 高风险 | 试图绕过AI安全机制的恶意提示 |
| 一般政治话题 | 🟡 中风险 | 涉及政治相关的一般性讨论 |
| 伤害未成年人 | 🟡 中风险 | 可能对未成年人造成身心伤害的内容 |
| 违法犯罪 | 🟡 中风险 | 教唆、指导或描述违法犯罪行为 |
| 色情 | 🟡 中风险 | 包含色情、性暗示或不当性内容 |
| 歧视内容 | 🟢 低风险 | 基于种族、性别、宗教等的歧视性言论 |
| 辱骂 | 🟢 低风险 | 包含侮辱、辱骂或恶意攻击的言语 |
| 侵犯个人隐私 | 🟢 低风险 | 涉及违法获取、泄漏或滥用个人隐私信息 |
| 商业违法违规 | 🟢 低风险 | 涉及商业欺诈、非法营销、违规经营 |

### 处理策略

- **🔴 高风险**：建议**代答**或**阻断**，使用预设安全回复
- **🟡 中风险**：建议**代答**，使用温和提醒回复  
- **🟢 低风险**：建议**通过**，正常处理用户请求
- **⚪ 安全**：建议**通过**，无风险内容

## 🏗️ 系统架构

```
                           用户/开发者
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
        ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐
        │  管理界面    │ │  API调用模式  │ │  安全网关模式    │
        │ (React Web) │ │   (主动检测)  │ │  (透明代理)     │
        └──────┬───────┘ └──────┬───────┘ └────────┬────────┘
               │ HTTP API       │ HTTP API          │ OpenAI API
               ▼                ▼                   ▼
    ┌──────────────┐  ┌──────────────┐    ┌──────────────────┐
    │  管理服务    │  │  检测服务    │    │   代理服务       │
    │ (5000端口)   │  │ (5001端口)   │    │  (5002端口)      │
    │ 低并发优化   │  │ 高并发优化   │    │  高并发优化      │
    └──────┬───────┘  └──────┬───────┘    └─────────┬────────┘
           │                 │                      │
           │          ┌──────┼──────────────────────┼───────┐
           │          │      │                      │       │
           ▼          ▼      ▼                      ▼       ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                PostgreSQL 数据库                            │
    │   用户表 | 检测结果表 | 黑白名单表 | 代答库表 | 代理配置表   │
    └─────────────────────┬───────────────────────────────────────┘
                          │
    ┌─────────────────────▼───────────────────────────────────────┐
    │              象信AI安全护栏检测模型                          │
    │           (Xiangxin-Guardrails-Text)                       │
    │             🤗 HuggingFace开源模型                         │
    └─────────────────────┬───────────────────────────────────────┘
                          │ (代理服务专用)
    ┌─────────────────────▼───────────────────────────────────────┐
    │                   上游AI模型                                │
    │       OpenAI | Anthropic | 本地模型 | 其他API                │
    └─────────────────────────────────────────────────────────────┘
```

### 🏭 三服务架构说明

1. **管理服务 (5000端口)**
   - 处理管理平台API和Web界面
   - 用户管理、配置管理、数据统计
   - 低并发优化：2个工作进程

2. **检测服务 (5001端口)** 
   - 提供高并发护栏检测API
   - 支持单轮和多轮对话检测
   - 高并发优化：32个工作进程

3. **代理服务 (5002端口)** 🆕
   - OpenAI兼容的安全网关反向代理  
   - 自动检测输入输出，智能阻断和代答
   - 高并发优化：24个工作进程

## 📊 管理功能

### 🏠 总览仪表盘
- 📈 实时检测统计数据
- 📊 风险分布可视化图表  
- 📉 检测趋势分析
- 🎯 系统运行状态监控

### 🔍 检测结果管理
- 📋 检测历史记录查询
- 🏷️ 多维度筛选和排序
- 📋 详细检测结果展示
- 📤 数据导出功能

### ⚙️ 防护配置管理
- ⚫ 黑名单关键词管理
- ⚪ 白名单关键词管理
- 💬 代答库配置管理
- 🚦 用户限速配置

### 👥 用户管理（管理员）
- 👤 用户账号管理
- 🔑 API密钥管理
- 🚦 用户限速配置
- 📊 用户使用统计

## 📸 产品截图

### 总览页面
<p align="left">
    <img src="assets/prod_dashboard.png" width="400"/>
<p>

### 在线测试页面  
<p align="left">
    <img src="assets/prod_onlinetest.png" width="400"/>
<p>

### 检测结果页面  
<p align="left">
    <img src="assets/prod_results.png" width="400"/>
<p>

### 风险报表页面
<p align="left">
    <img src="assets/prod_reports.png" width="400"/>
<p>

### 黑白名单页面

<p align="left">
    <img src="assets/prod_blacklist.png" width="400"/>
<p>

### 代答库页面
<p align="left">
    <img src="assets/prod_answers.png" width="400"/>
<p>

## 🤗 开源模型

我们的护栏模型已在HuggingFace开源：

- **模型地址**: [xiangxinai/Xiangxin-Guardrails-Text](https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text)
- **许可协议**: Apache 2.0
- **支持语言**: 中文、英文
- **模型性能**: 检测精准率：99.99%，检测召回率：98.63%，响应时间(P95)：274.6ms

```python
# 本地模型推理示例
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "xiangxinai/Xiangxin-Guardrails-Text"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 进行推理
inputs = tokenizer("测试文本", return_tensors="pt")
outputs = model(**inputs)
```

## 🚀 部署指南

象信AI安全护栏支持两种部署模式：

### 🔧 部署模式选择

#### SaaS模式（默认）
- 完整的Web管理界面
- 检测结果存储到数据库
- 适合内部使用和完整功能体验

#### 私有化集成模式 🆕
- 与客户现有用户系统深度集成
- 检测结果仅写日志文件，数据库只存配置信息
- 通过API管理用户级别的黑白名单和代答模板
- 客户在自己的中控台管理安全配置
- 适合私有化部署到客户环境

详细的私有化集成指南请参考：[📖 客户集成指南](backend/docs/客户集成指南.md)

### 系统要求

- **操作系统**: Linux、macOS、Windows
- **Python**: 3.8+
- **Node.js**: 16+ (如需前端开发)
- **内存**: 最低2GB，推荐4GB+
- **存储**: 最低10GB可用空间
- **数据库**: PostgreSQL 12+

### Docker部署（推荐）

#### 三服务架构部署（推荐）
```bash
# 1. 克隆项目
git clone https://github.com/xiangxinai/xiangxin-guardrails.git
cd xiangxin-guardrails

# 2. 启动三服务（管理5000 + 检测5001 + 代理5002）
docker-compose up -d

# 3. 检查服务状态
docker-compose ps

# 4. 验证服务
curl http://localhost:5000/health  # 管理服务
curl http://localhost:5001/health  # 检测服务  
curl http://localhost:5002/health  # 代理服务

# 5. 查看服务日志
docker-compose logs -f admin-service      # 管理服务日志
docker-compose logs -f detection-service  # 检测服务日志
docker-compose logs -f proxy-service      # 代理服务日志

# 6. 停止服务
docker-compose down -v
```

#### 服务架构说明
- **管理服务** (5000端口)：处理管理平台API `/api/v1/*`
- **检测服务** (5001端口)：处理高并发检测API `/v1/guardrails`
- **代理服务** (5002端口)：OpenAI兼容的安全网关 `/v1/*` 🆕
- **并发性能**：并发配置 `PROXY_MAX_CONCURRENT_REQUESTS`和`DETECTION_MAX_CONCURRENT_REQUESTS`，每个worker能承受500-1000个并发。

#### 私有化集成模式
```bash
# 配置私有化模式（仅写日志文件，不存数据库）
cp backend/.env.example backend/.env
# 编辑 backend/.env 文件，设置：
# STORE_DETECTION_RESULTS=false

docker-compose up -d
```


### 手动部署

#### 1. 数据库准备

```bash
# 安装PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE xiangxin_guardrails;
CREATE USER xiangxin WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE xiangxin_guardrails TO xiangxin;
```

#### 2. 后端部署

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DATABASE_URL="postgresql://xiangxin:your_password@localhost/xiangxin_guardrails"
export SECRET_KEY="your_secret_key"
export MODEL_API_URL="http://localhost:58002/v1"
export MODEL_API_KEY="your_model_api_key"

# 初始化数据库
python scripts/init_postgres.py

# 启动三服务
./start_all_services.sh

# 或单独启动
python start_detection_service.py  # 检测服务
python start_admin_service.py      # 管理服务  
python start_proxy_service.py      # 代理服务
```

#### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用nginx部署dist目录
sudo cp -r dist/* /var/www/html/
```

## 📚 文档

- [📖 API文档](docs/api-documentation.md)
- [🚀 快速开始](docs/quickstart.md)  
- [⚙️ 配置说明](docs/configuration.md)
- [🔧 开发指南](docs/development.md)
- [❓ 常见问题](docs/faq.md)
- [🔄 更新日志](CHANGELOG.md)

### 私有化集成文档 🆕
- [📖 客户集成指南](backend/docs/客户集成指南.md) - 详细的客户系统集成说明
- [📋 API接口文档](backend/docs/API接口文档.md) - 完整的API接口说明
- [🚀 私有化部署指南](backend/docs/私有化部署指南.md) - Docker和源码部署指导
- [💻 Python SDK](backend/client-sdk/python/guardrails_client.py) - Python客户端SDK
- [💻 Node.js SDK](backend/client-sdk/nodejs/guardrails-client.js) - Node.js客户端SDK

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 参与方式
- 🐛 [提交Bug报告](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- 💡 [提出功能建议](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- 📖 完善项目文档
- 🧪 添加测试用例
- 💻 提交代码

### 开发流程
```bash
# 1. Fork项目到你的GitHub账号
# 2. 创建特性分支
git checkout -b feature/amazing-feature

# 3. 提交更改
git commit -m 'Add some amazing feature'

# 4. 推送到分支
git push origin feature/amazing-feature

# 5. 创建Pull Request
```

详细的贡献指南请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

## 🔒 安全说明

本项目专注于**防御性安全**，所有功能都用于保护AI应用免受恶意攻击。我们严格遵循负责任的AI开发原则，不支持任何恶意用途。

相关安全考虑请参考 [SECURITY.md](SECURITY.md)

## 🌟 商业服务

我们提供专业的AI安全解决方案：

### 🎯 定制化服务
- **行业定制**: 针对特定行业的模型微调
- **场景优化**: 根据应用场景优化检测效果
- **私有化部署**: 完全离线的企业级部署方案

### 🏢 技术支持
- **专业咨询**: AI安全架构设计咨询
- **技术培训**: 团队技能提升培训
- **社区支持**: 免费的社区技术支持服务

> 📧 **商务咨询**: wanglei@xiangxinai.cn  
> 🌐 **官方网站**: https://xiangxinai.cn

## 📄 许可证

本项目基于 [Apache 2.0](LICENSE) 许可证开源，可免费商用。

## 🌟 支持我们

如果这个项目对您有帮助，请给我们一个 ⭐️！

[![Star History Chart](https://api.star-history.com/svg?repos=xiangxinai/xiangxin-guardrails&type=Date)](https://star-history.com/#xiangxinai/xiangxin-guardrails&Date)

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

## 📞 联系我们

- 📧 **技术支持**: 我们提供免费的社区技术支持
- 📧 **商务咨询**：wanglei@xiangxinai.cn
- 🌐 **官方网站**: https://xiangxinai.cn
- 📱 **微信公众号**: 扫描二维码关注<a href="assets/wechat.jpg">微信公众号</a>

---

<div align="center">

**让AI更安全，让应用更可信** 🛡️

Made with ❤️ by [北京象信智能科技有限公司](https://xiangxinai.cn) 象信AI®是注册商标

</div>
