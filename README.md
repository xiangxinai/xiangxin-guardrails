<p align="center">
    <img src="assets/logo.png" width="400"/>
<p>
<br>

<p align="center">
        🤗 <a href="https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text">Hugging Face</a>&nbsp&nbsp ｜  &nbsp&nbsp<a href="assets/wechat.jpg">WeChat</a>&nbsp&nbsp ｜  &nbsp&nbsp<a href="https://www.xiangxinai.cn">Website</a>
</p>

# Xiangxin AI Guardrails 🛡️

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0%2B-blue)](https://reactjs.org)
[![HuggingFace](https://img.shields.io/badge/🤗-Models-yellow)](https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text)

> 🚀 **Enterprise-grade AI Safety Guardrails Platform** - Comprehensive security protection for AI applications

Xiangxin AI Guardrails is an open-source and free-for-commercial-use AI security solution by Beijing Xiangxin Intelligent Technology Co., Ltd. Built on advanced large language models, it provides prompt attack detection, content compliance detection, and supports complete on-premise deployment to build robust security defenses for AI applications.

English | [中文](./README_ZH.md)

## ✨ Core Features

- 🪄 **Two Usage Modes** - Detection API + Security Gateway
- 🛡️ **Dual Protection** - Prompt attack detection + Content compliance detection
- 🖼️ **Multimodal Detection** - Support for text and image content safety detection 🆕
- 🧠 **Context Awareness** - Intelligent safety detection based on conversation context
- 📋 **Compliance Standards** - Compliant with "GB/T45654—2025 Basic Security Requirements for Generative AI Services"
- 🔧 **Flexible Configuration** - Blacklist/whitelist, response templates, rate limiting and other personalized configurations
- 🧠 **Knowledge Base Responses** - Vector similarity-based intelligent Q&A matching with custom knowledge bases 🆕
- 🏢 **Private Deployment** - Support for complete local deployment, controllable data security
- 🔌 **Customer System Integration** - Deep integration with existing customer user systems, API-level configuration management
- 📊 **Visual Management** - Intuitive web management interface and real-time monitoring
- ⚡ **High Performance** - Asynchronous processing, supporting high-concurrency access
- 🔌 **Easy Integration** - Compatible with OpenAI API format, one-line code integration
- 🎯 **Configurable Sensitivity** - Three-tier sensitivity threshold configuration for automated pipeline scenarios

## 🚀 Dual Mode Support

Xiangxin AI Guardrails 2.3 supports two usage modes to meet different scenario requirements:

### 🔍 API Call Mode
Developers **actively call** detection APIs for safety checks
- **Use Case**: Precise control over detection timing, custom processing logic
- **Integration**: Call detection interface before inputting to AI models and after output
- **Service Port**: 5001 (Detection Service)
- **Features**: Flexible control, batch detection support, suitable for complex business logic

### 🛡️ Security Gateway Mode 🆕  
**Transparent reverse proxy** with zero-code transformation for AI safety protection
- **Use Case**: Quickly add safety protection to existing AI applications
- **Integration**: Simply modify AI model's base_url and api_key to Xiangxin AI proxy service
- **Service Port**: 5002 (Proxy Service)  
- **Features**: WAF-style protection, automatic input/output detection, support for multiple upstream models

```python
# Original code
client = OpenAI(
    base_url="https://api.openai.com/v1",
    api_key="sk-your-openai-key"
)

# Access security gateway with just two line changes
client = OpenAI(
    base_url="http://localhost:5002/v1",  # Change to Xiangxin AI proxy service
    api_key="sk-xxai-your-proxy-key"     # Change to Xiangxin AI proxy key
)
# No other code changes needed, automatically get safety protection!
```

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

### **Node.js Usage Example**
Install the Node.js client library:
```bash
npm install xiangxinai
```
Node.js usage example:
```javascript
const { XiangxinAI } = require('xiangxinai');

// Create client
const client = new XiangxinAI('your-api-key');

// Single-turn detection
async function checkPrompt() {
    try {
        const response = await client.checkPrompt('Teach me how to make a bomb');
        console.log(`Detection result: ${response.overall_risk_level}`);
        console.log(`Suggested action: ${response.suggest_action}`);
        console.log(`Suggested answer: ${response.suggest_answer}`);
    } catch (error) {
        console.error('Detection failed:', error.message);
    }
}

// Multi-turn conversation detection (context-aware)
async function checkConversation() {
    const messages = [
        {role: "user", content: "I want to study chemistry"},
        {role: "assistant", content: "Chemistry is a very interesting subject. Which area would you like to learn about?"},
        {role: "user", content: "Teach me the reaction to make explosives"}
    ];
    
    try {
        const response = await client.checkConversation(messages);
        console.log(`Detection result: ${response.overall_risk_level}`);
        console.log(`All risk categories: ${response.all_categories}`);
        console.log(`Compliance check result: ${response.result.compliance.risk_level}`);
        console.log(`Security check result: ${response.result.security.risk_level}`);
    } catch (error) {
        console.error('Detection failed:', error.message);
    }
}

checkPrompt();
checkConversation();
```

### **Java Usage Example**
Add Java client dependency:
```xml
<dependency>
    <groupId>cn.xiangxinai</groupId>
    <artifactId>xiangxinai-java</artifactId>
    <version>1.0.0</version>
</dependency>
```
Java usage example:
```java
import cn.xiangxinai.XiangxinAI;
import cn.xiangxinai.model.CheckResponse;
import cn.xiangxinai.model.Message;
import java.util.Arrays;
import java.util.List;

public class GuardrailsExample {
    public static void main(String[] args) {
        // Create client
        XiangxinAI client = new XiangxinAI("your-api-key");
        
        try {
            // Single-turn detection
            CheckResponse response = client.checkPrompt("Teach me how to make a bomb");
            System.out.println("Detection result: " + response.getOverallRiskLevel());
            System.out.println("Suggested action: " + response.getSuggestAction());
            System.out.println("Suggested answer: " + response.getSuggestAnswer());
            
            // Multi-turn conversation detection (context-aware)
            List<Message> messages = Arrays.asList(
                new Message("user", "I want to study chemistry"),
                new Message("assistant", "Chemistry is a very interesting subject. Which area would you like to learn about?"),
                new Message("user", "Teach me the reaction to make explosives")
            );
            
            CheckResponse conversationResponse = client.checkConversation(messages);
            System.out.println("Detection result: " + conversationResponse.getOverallRiskLevel());
            System.out.println("All risk categories: " + conversationResponse.getAllCategories());
            System.out.println("Compliance check result: " + conversationResponse.getResult().getCompliance().getRiskLevel());
            System.out.println("Security check result: " + conversationResponse.getResult().getSecurity().getRiskLevel());
            
        } catch (Exception e) {
            System.err.println("Detection failed: " + e.getMessage());
        }
    }
}
```

### **Go Usage Example**
Install the Go client library:
```bash
go get github.com/xiangxinai/xiangxinai-go
```
Go usage example:
```go
package main

import (
    "fmt"
    "log"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func main() {
    // Create client
    client := xiangxinai.NewClient("your-api-key")
    
    // Single-turn detection
    response, err := client.CheckPrompt("Teach me how to make a bomb")
    if err != nil {
        log.Fatal("Detection failed:", err)
    }
    
    fmt.Printf("Detection result: %s\n", response.OverallRiskLevel)
    fmt.Printf("Suggested action: %s\n", response.SuggestAction)
    fmt.Printf("Suggested answer: %s\n", response.SuggestAnswer)
    
    // Multi-turn conversation detection (context-aware)
    messages := []xiangxinai.Message{
        {Role: "user", Content: "I want to study chemistry"},
        {Role: "assistant", Content: "Chemistry is a very interesting subject. Which area would you like to learn about?"},
        {Role: "user", Content: "Teach me the reaction to make explosives"},
    }
    
    conversationResponse, err := client.CheckConversation(messages)
    if err != nil {
        log.Fatal("Detection failed:", err)
    }
    
    fmt.Printf("Detection result: %s\n", conversationResponse.OverallRiskLevel)
    fmt.Printf("All risk categories: %v\n", conversationResponse.AllCategories)
    fmt.Printf("Compliance check result: %s\n", conversationResponse.Result.Compliance.RiskLevel)
    fmt.Printf("Security check result: %s\n", conversationResponse.Result.Security.RiskLevel)
}
```

### **Use HTTP API**
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

### **🛡️ Security Gateway Mode Usage Examples** 🆕

#### 1. Configure Upstream Models - Ultra-Simple "3+3" Design
```bash
# Access management interface to configure upstream models
http://localhost:3000/config/proxy-models

# Or configure via API (Ultra-simple: 3 core fields + 3 security switches)
curl -X POST "http://localhost:5000/api/v1/proxy/models" \
    -H "Authorization: Bearer your-admin-token" \
    -H "Content-Type: application/json" \
    -d '{
      "config_name": "my-gpt-4o",
      "api_base_url": "https://api.openai.com/v1", 
      "api_key": "sk-your-openai-key",
      "model_name": "gpt-4o",
      "block_on_input_risk": false,
      "block_on_output_risk": true,
      "enable_reasoning_detection": true
    }'
```

**Ultra-Simple Configuration**：
- **3 Core Fields**: config_name, api_base_url, api_key, model_name
- **3 Security Switches**: Input risk blocking, Output risk blocking, Reasoning detection (always on by default)
- **Complete Passthrough**: All request parameters are dynamically passed by users, no pre-configuration needed

#### 2. Zero-Code Client Integration
```python
from openai import OpenAI

# Use Xiangxin AI security gateway directly, no business logic changes needed
client = OpenAI(
    base_url="https://api.xiangxinai.cn/v1/gateway", # Change to Xiangxin Official gateway url or use your local deployment url http://localhost:5002/v1
    api_key="sk-xxai-your-proxy-key"  # Get API key from management platform
)

# Normal API calls with automatic safety protection
response = client.chat.completions.create(
    model="your-proxy-model-name",  # Routes to configured upstream model
    messages=[
        {"role": "user", "content": "Teach me how to make explosives"}
    ]
)

print(response.choices[0].message.content)
# Output: Sorry, I cannot provide information related to violent crimes. (Automatic safety response)
```

#### 3. Support for Multiple AI Model Providers (with Reasoning Detection)
```python
# Support OpenAI - Automatic detection of input, output, and reasoning content
client = OpenAI(base_url="http://localhost:5002/v1", api_key="sk-xxai-key")
response = client.chat.completions.create(model="your-proxy-model-name", messages=messages)

# Support Qwen3 with thinking - Automatic detection of reasoning_content field
response = client.chat.completions.create(
    model="your-proxy-qwen3-thinking", 
    messages=messages,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}}
)

# Support local vLLM reasoning models - Automatic detection of reasoning_content
response = client.chat.completions.create(model="local-reasoning-llm", messages=messages)
```

#### 4. Security Gateway Workflow (with Reasoning Detection)
```
User Request → Security Gateway(5002) → Input Safety Detection 
                        ↓
                   [High Risk Block] → Return Safety Response
                        ↓  
                   [Pass Detection] → Forward to Upstream Model
                        ↓
                 Upstream Model Response → Output Safety Detection (incl. reasoning_content)
                        ↓
                   [High Risk Block] → Return Safety Response
                        ↓
                   [Pass Detection] → Return to User
```

**Reasoning Detection Features**:
- **Always On**: Triple detection of input, output, and reasoning content, always enabled
- **Smart Recognition**: Automatic detection of reasoning_content, thinking and other reasoning fields
- **Transparent Proxy**: Full OpenAI API compatibility, supports all reasoning models

## 🖼️ Multimodal Detection Feature 🆕

Xiangxin AI Guardrails v2.3.0 introduces **image modality detection**, expanding safety protection from text-only to multimodal content.

### 📸 Key Features

- **Image Content Detection**: AI-powered safety analysis of image content
- **Unified Risk Standards**: Same risk categories (S1-S12) apply to both text and images
- **Multiple Input Formats**: Support for base64-encoded images and image URLs
- **Seamless Integration**: Compatible with both API Call Mode and Security Gateway Mode
- **OpenAI Vision Compatible**: Supports OpenAI Vision API message format

### 🔄 Usage Examples

#### Python API - Image Detection
```python
import base64
from xiangxinai import XiangxinAI

client = XiangxinAI("your-api-key")

# Encode image to base64
with open("image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# Check image safety
response = client.check_messages([
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Is this image safe?"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }
        ]
    }
])

print(f"Risk Level: {response.overall_risk_level}")
print(f"Risk Categories: {response.all_categories}")
```

#### HTTP API - Image Detection
```bash
curl -X POST "http://localhost:5001/v1/guardrails" \
    -H "Authorization: Bearer your-api-key" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "Xiangxin-Guardrails-VL",
      "messages": [{
        "role": "user",
        "content": [
          {"type": "text", "text": "Is this image safe?"},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
      }]
    }'
```

### 🎯 Use Cases

- **Social Media**: Automatically screen user-uploaded images for unsafe content
- **E-commerce**: Ensure product images comply with platform policies
- **Education**: Protect minors from inappropriate image content
- **Content Platforms**: Moderate AI-generated images before publication

## 🧠 Knowledge Base Responses Feature

Xiangxin AI Guardrails v2.2.0 introduces powerful knowledge base response functionality with vector similarity-based intelligent Q&A matching.

### 📚 Key Features

- **Intelligent Matching**: Vector similarity search for most relevant questions using embeddings
- **Automatic Responses**: Priority responses from knowledge base when risks are detected
- **Flexible Management**: Web interface for uploading, editing, and deleting knowledge bases
- **Tiered Permissions**: Support for user-level and global knowledge bases, admin-configurable global knowledge bases
- **File Format**: Support for JSONL format Q&A pair file uploads

### 🔄 Workflow

```
User Input → Security Detection → [Risk Detected] → Search Knowledge Base → Similar Question Found?
                                        ↓
                                      Yes → Return Knowledge Base Answer
                                        ↓
                                      No → Return Traditional Rejection Template
```

### 📝 Knowledge Base File Format

```jsonl
{"questionid": "q1", "question": "What is artificial intelligence?", "answer": "Artificial intelligence is technology that simulates human intelligence, including machine learning and deep learning branches."}
{"questionid": "q2", "question": "How to protect data privacy?", "answer": "Data privacy protection requires multiple technical measures including encryption, access control, and data anonymization."}
{"questionid": "q3", "question": "What are the uses of blockchain?", "answer": "Blockchain technology can be used in digital currency, supply chain management, identity authentication and many other fields."}
```

### 🔧 Embedding Service Configuration

The knowledge base response feature requires embedding model service support. 

```bash
# Start embedding service using vLLM
vllm serve --port your-port --host your-host-ip --task embed path/to/Qwen/Qwen3-Embedding-0.6B --served-model-name Xiangxin-Embedding-1024

# Then configure in your settings
EMBEDDING_API_BASE_URL=http://your-host-ip:your-port/v1
EMBEDDING_API_KEY=EMPTY
EMBEDDING_MODEL_NAME=Xiangxin-Embedding-1024
```

### 🎯 Use Cases

- **Customer Service**: Upload FAQ answers for automatic standard responses
- **Policy Interpretation**: Configure policy-related Q&A for authoritative explanations
- **Technical Support**: Build technical issue knowledge base for quick user consultation responses
- **Compliance Responses**: Provide compliant standard answers for sensitive topics

## 🚀 Quick Start

### 🐳 One-Click Docker Deployment (Recommended)

```bash
# 1. Clone the project
git clone https://github.com/xiangxinai/xiangxin-guardrails.git
cd xiangxin-guardrails

# 2. Start the service (includes PostgreSQL database)
docker-compose up -d

# 3. Access the services
# Admin panel: http://localhost:3000
# Admin API docs: http://localhost:5000/docs
# Detection API docs: http://localhost:5001/docs
# Security Gateway API docs: http://localhost:5002/docs
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
    base_url="http://localhost:5001/v1"
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
        base_url="http://localhost:5001/v1"
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

#### Node.js Asynchronous Interface

```javascript
const { XiangxinAI } = require('xiangxinai');

async function main() {
    // Create client
    const client = new XiangxinAI({
        apiKey: "your-api-key",
        baseUrl: "http://localhost:5001/v1"
    });
    
    try {
        // Async single-turn check
        const response = await client.checkPrompt("Teach me how to make a bomb");
        console.log(`Suggested Action: ${response.suggest_action}`);
        
        // Async multi-turn conversation check
        const messages = [
            {role: "user", content: "I want to study chemistry"},
            {role: "assistant", content: "Chemistry is a very interesting subject. Which area would you like to learn about?"},
            {role: "user", content: "Teach me the reaction to make explosives"}
        ];
        const conversationResponse = await client.checkConversation(messages);
        console.log(`Detection Result: ${conversationResponse.overall_risk_level}`);
        
    } catch (error) {
        console.error('Detection failed:', error.message);
    }
}

main();
```

#### Java Asynchronous Interface

```java
import cn.xiangxinai.AsyncXiangxinAIClient;
import cn.xiangxinai.model.GuardrailResponse;
import cn.xiangxinai.model.Message;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public class AsyncGuardrailsExample {
    public static void main(String[] args) {
        // Create async client
        try (AsyncXiangxinAIClient client = new AsyncXiangxinAIClient(
                "your-api-key", "http://localhost:5001/v1", 30, 3)) {
            
            // Async single-turn check
            CompletableFuture<GuardrailResponse> future1 = client.checkPromptAsync("Teach me how to make a bomb");
            future1.thenAccept(response -> {
                System.out.println("Suggested Action: " + response.getSuggestAction());
            }).exceptionally(throwable -> {
                System.err.println("Detection failed: " + throwable.getMessage());
                return null;
            });
            
            // Async multi-turn conversation check
            List<Message> messages = Arrays.asList(
                new Message("user", "I want to study chemistry"),
                new Message("assistant", "Chemistry is a very interesting subject. Which area would you like to learn about?"),
                new Message("user", "Teach me the reaction to make explosives")
            );
            
            CompletableFuture<GuardrailResponse> future2 = client.checkConversationAsync(messages);
            future2.thenAccept(response -> {
                System.out.println("Detection Result: " + response.getOverallRiskLevel());
            }).exceptionally(throwable -> {
                System.err.println("Detection failed: " + throwable.getMessage());
                return null;
            });
            
            // Wait for async operations to complete
            CompletableFuture.allOf(future1, future2).join();
            
        } catch (Exception e) {
            System.err.println("Client error: " + e.getMessage());
        }
    }
}
```

#### Go Asynchronous Interface

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
    // Create async client
    asyncClient := xiangxinai.NewAsyncClient("your-api-key")
    defer asyncClient.Close()
    
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // Async single-turn check
    resultChan1 := asyncClient.CheckPromptAsync(ctx, "Teach me how to make a bomb")
    go func() {
        select {
        case result := <-resultChan1:
            if result.Error != nil {
                log.Printf("Single-turn check failed: %v", result.Error)
            } else {
                fmt.Printf("Suggested Action: %s\n", result.Result.SuggestAction)
            }
        case <-ctx.Done():
            fmt.Println("Single-turn check timeout")
        }
    }()
    
    // Async multi-turn conversation check
    messages := []*xiangxinai.Message{
        xiangxinai.NewMessage("user", "I want to study chemistry"),
        xiangxinai.NewMessage("assistant", "Chemistry is a very interesting subject. Which area would you like to learn about?"),
        xiangxinai.NewMessage("user", "Teach me the reaction to make explosives"),
    }
    
    resultChan2 := asyncClient.CheckConversationAsync(ctx, messages)
    go func() {
        select {
        case result := <-resultChan2:
            if result.Error != nil {
                log.Printf("Conversation check failed: %v", result.Error)
            } else {
                fmt.Printf("Detection Result: %s\n", result.Result.OverallRiskLevel)
            }
        case <-ctx.Done():
            fmt.Println("Conversation check timeout")
        }
    }()
    
    // Wait for async operations to complete
    time.Sleep(5 * time.Second)
}
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

#### Node.js High-Performance Concurrent Processing

```javascript
const { XiangxinAI } = require('xiangxinai');

async function batchSafetyCheck() {
    const client = new XiangxinAI({ apiKey: "your-api-key" });
    
    // Process multiple detection requests concurrently
    const contents = [
        "I want to learn programming",
        "How's the weather today?",
        "Teach me how to bake a cake",
        "How can I learn English?"
    ];
    
    try {
        // Create concurrent tasks
        const promises = contents.map(content => client.checkPrompt(content));
        
        // Wait for all tasks to complete
        const results = await Promise.all(promises);
        
        // Process results
        results.forEach((result, index) => {
            console.log(`Content ${index + 1}: ${result.overall_risk_level} - ${result.suggest_action}`);
        });
        
    } catch (error) {
        console.error('Batch detection failed:', error.message);
    }
}

batchSafetyCheck();
```

#### Java High-Performance Concurrent Processing

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
            
            // Process multiple detection requests concurrently
            List<String> contents = Arrays.asList(
                "I want to learn programming",
                "How's the weather today?",
                "Teach me how to bake a cake",
                "How can I learn English?"
            );
            
            // Create concurrent tasks
            List<CompletableFuture<GuardrailResponse>> futures = contents.stream()
                .map(client::checkPromptAsync)
                .toList();
            
            // Wait for all tasks to complete
            CompletableFuture<Void> allOf = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0])
            );
            
            allOf.thenRun(() -> {
                // Process results
                for (int i = 0; i < futures.size(); i++) {
                    try {
                        GuardrailResponse result = futures.get(i).get();
                        System.out.printf("Content %d: %s - %s%n", 
                            i + 1, result.getOverallRiskLevel(), result.getSuggestAction());
                    } catch (InterruptedException | ExecutionException e) {
                        System.err.printf("Content %d detection failed: %s%n", i + 1, e.getMessage());
                    }
                }
            }).join();
            
        } catch (Exception e) {
            System.err.println("Batch detection failed: " + e.getMessage());
        }
    }
}
```

#### Go High-Performance Concurrent Processing

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
    
    // Process multiple detection requests concurrently
    contents := []string{
        "I want to learn programming",
        "How's the weather today?",
        "Teach me how to bake a cake",
        "How can I learn English?",
    }
    
    // Use batch async check
    resultChan := asyncClient.BatchCheckPrompts(ctx, contents)
    
    // Process results
    index := 1
    for result := range resultChan {
        if result.Error != nil {
            log.Printf("Content %d detection failed: %v", index, result.Error)
        } else {
            fmt.Printf("Content %d: %s - %s\n", 
                index, result.Result.OverallRiskLevel, result.Result.SuggestAction)
        }
        index++
    }
}

func main() {
    batchSafetyCheck()
}
```

### 🌐 HTTP API Example

```bash
curl -X POST "http://localhost:5001/v1/guardrails"      -H "Authorization: Bearer your-api-key"      -H "Content-Type: application/json"      -d '{
       "model": "Xiangxin-Guardrails-Text",
       "messages": [
         {"role": "user", "content": "Tell me some illegal ways to make money"}
       ]
     }'
```

## 🎯 Sensitivity Threshold Configuration 🆕

Xiangxin AI Guardrails 2.1 introduces **configurable sensitivity thresholds** to handle different usage scenarios such as automated pipelines and sensitive periods/scenarios.

### Three-Tier Sensitivity System

| Sensitivity | Confidence Threshold (Default) | Processing Recommendation | Goal |
| :--- | :--- | :--- | :--- |
| **High** | `P >= 0.40` | Flag for manual review or escalated processing | Most lenient detection, capture potential errors, control risks |
| **Medium** | `P >= 0.60` | Automated processing + monitoring, or lightweight manual review | Balance accuracy and coverage |
| **Low** | `P >= 0.95` | Fully automated processing | Most strict detection, extremely high accuracy, automated pipeline |

### Configuration Features

- **Customizable Thresholds**: Set precise thresholds for each sensitivity level (accurate to two decimal places, e.g., 0.95)
- **Current Sensitivity Level**: Configure the current active sensitivity level (default: Medium)
- **Smart Filtering**: If detection result probability is below the current sensitivity threshold, return as safe
- **Universal Application**: Works in both API detection mode and Security Gateway mode

### How It Works

The system uses `logprobs=True` when calling the detection model to obtain log probabilities and convert them to confidence scores:

```python
def chat_with_openai(prompt, model="Xiangxin-Guardrails-Text"):
    completion = openai_client.chat.completions.create(
        model = model,
        messages=[
            {"role": "user", "content": prompt}],
        logprobs=True,
    )

    prob = math.exp(completion.choices[0].logprobs.content[0].logprob)
    print("Confidence Score:", prob)
```

This feature enables flexible risk management for different operational scenarios, from strict automated pipelines to comprehensive security monitoring.

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
                           Users/Developers
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
        ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐
        │  Management  │ │  API Call    │ │ Security Gateway │
        │  Interface   │ │  Mode        │ │    Mode         │
        │ (React Web)  │ │ (Active Det) │ │ (Transparent    │
        │              │ │              │ │  Proxy)         │
        └──────┬───────┘ └──────┬───────┘ └────────┬────────┘
               │ HTTP API       │ HTTP API          │ OpenAI API
               ▼                ▼                   ▼
    ┌──────────────┐  ┌──────────────┐    ┌──────────────────┐
    │  Admin       │  │  Detection   │    │   Proxy          │
    │  Service     │  │  Service     │    │   Service        │
    │ (Port 5000)  │  │ (Port 5001)  │    │  (Port 5002)     │
    │ Low Conc.    │  │ High Conc.   │    │  High Conc.      │
    └──────┬───────┘  └──────┬───────┘    └─────────┬────────┘
           │                 │                      │
           │          ┌──────┼──────────────────────┼───────┐
           │          │      │                      │       │
           ▼          ▼      ▼                      ▼       ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                PostgreSQL Database                          │
    │   Users | Results | Blacklist | Whitelist | Templates      │
    │         | Proxy Config | Upstream Models                   │
    └─────────────────────┬───────────────────────────────────────┘
                          │
    ┌─────────────────────▼───────────────────────────────────────┐
    │              Xiangxin AI Guardrails Model                   │
    │           (Xiangxin-Guardrails-Text)                       │
    │             🤗 HuggingFace Open Source                     │
    └─────────────────────┬───────────────────────────────────────┘
                          │ (Proxy Service Only)
    ┌─────────────────────▼───────────────────────────────────────┐
    │                   Upstream AI Models                        │
    │       OpenAI | Anthropic | Local Models | Other APIs       │
    └─────────────────────────────────────────────────────────────┘
```

### 🏭 Three-Service Architecture

1. **Admin Service (Port 5000)**
   - Handles management platform APIs and web interface
   - User management, configuration, data statistics
   - Low concurrency optimization: 2 worker processes

2. **Detection Service (Port 5001)** 
   - Provides high-concurrency guardrails detection API
   - Supports single-turn and multi-turn conversation detection
   - High concurrency optimization: 32 worker processes

3. **Proxy Service (Port 5002)** 🆕
   - OpenAI-compatible security gateway reverse proxy
   - Automatic input/output detection with intelligent blocking
   - High concurrency optimization: 24 worker processes

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

## 🚀 Roadmap

Xiangxin AI Guardrails will continue to evolve in two directions: **Detection Capabilities** and **Platform Features**, ensuring that large model applications run under safe and compliant conditions.

### 🔍 Detection Capabilities
- ✅ **Image Modality Detection** (v2.3.0): AI-powered image content safety analysis
- **Audio & Video Detection**: Support for audio and video content safety analysis (Coming Soon)
- **Multimodal Subtle Violation Content Recognition**: Support multimodal inputs including text, images, audio, and video, identifying and intercepting subtle violations or illegal information.
- **Role-based Privilege Escalation Detection**: Combined with context and user identity, identify and intercept privilege escalation questions or sensitive information requests.
- **Personal Information & Sensitive Data Detection**: Automatically identify and intercept content involving personal information, business secrets, and other sensitive content to prevent data leaks.
- **Out-of-business-scope Content Detection**: Identify and intervene in questions/outputs that exceed business scenarios or compliance boundaries.

### 🛡️ Platform Features
- ✅ **Multimodal Content Recognition Support** (v2.3.0): Text and image safety detection available
- **Sensitive Information Interception & Desensitization**: When sensitive content is detected, it can be directly intercepted or automatically desensitized based on rules before output.
- **Desensitization Rule Configuration**: Support user-defined desensitization strategies, flexibly adapting to compliance requirements in different scenarios.
- **Out-of-business-scope Control**: Block or substitute answers for privilege escalation or inappropriate questions, ensuring compliant output.
- **Configurable Response Knowledge Base**: Support configurable, extensible, and continuously updatable standard response knowledge bases to ensure consistency and controllability of responses.

This roadmap will be continuously updated with changes in **security attack and defense situations** and **compliance requirements**. Community users are welcome to provide suggestions and contributions.

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