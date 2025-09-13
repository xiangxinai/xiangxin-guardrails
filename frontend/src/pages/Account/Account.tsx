import React, { useEffect, useState } from 'react';
import { Card, Typography, Space, Button, message, Divider, Collapse, Tag, Alert } from 'antd';
import { CopyOutlined, ReloadOutlined, SafetyCertificateOutlined, ContactsOutlined, CodeOutlined, ApiOutlined } from '@ant-design/icons';
import { authService, UserInfo } from '../../services/auth';
import { configApi } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface SystemInfo {
  support_email: string | null;
  app_name: string;
  app_version: string;
}

const Account: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchMe = async () => {
    try {
      const me = await authService.getCurrentUser();
      console.log('用户信息响应:', me);
      console.log('rate_limit字段:', me.rate_limit, '类型:', typeof me.rate_limit);
      setUser(me);
    } catch (e) {
      console.error('获取用户信息失败:', e);
      message.error('获取用户信息失败');
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const info = await configApi.getSystemInfo();
      setSystemInfo(info);
    } catch (e) {
      console.error('获取系统信息失败', e);
    }
  };

  useEffect(() => {
    fetchMe();
    fetchSystemInfo();
  }, []);

  const handleCopy = async () => {
    if (!user?.api_key) return;
    try {
      await navigator.clipboard.writeText(user.api_key);
      message.success('已复制到剪贴板');
    } catch {
      message.error('复制失败');
    }
  };

  const handleRegenerate = async () => {
    try {
      setLoading(true);
      const data = await authService.regenerateApiKey();
      message.success('API Key 已更新');
      setUser((prev: UserInfo | null) => prev ? { ...prev, api_key: data.api_key } : prev);
    } catch (e: any) {
      message.error(e.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space align="center">
          <SafetyCertificateOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>账号管理</Title>
        </Space>

        <div>
          <Text type="secondary">邮箱</Text>
          <div style={{ fontSize: 16 }}>{user?.email || '-'}</div>
        </div>

        <div>
          <Text type="secondary">用户 UUID</Text>
          <Space style={{ width: '100%', marginTop: 8, alignItems: 'center' }}>
            <div style={{ 
              flex: 1,
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              backgroundColor: '#fafafa',
              fontFamily: 'monospace',
              fontSize: '14px',
              wordBreak: 'break-all'
            }}>
              <Text code style={{ backgroundColor: 'transparent', border: 'none', padding: 0 }}>
                {user?.id || '-'}
              </Text>
            </div>
            <Button 
              icon={<CopyOutlined />} 
              onClick={() => {
                if (user?.id) {
                  navigator.clipboard.writeText(user.id);
                  message.success('UUID 已复制到剪贴板');
                }
              }}
            >
              复制
            </Button>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">提示：UUID 是您的唯一用户标识符。</Text>
          </div>
        </div>

        <div>
          <Text type="secondary">当前 API Key</Text>
          <Space style={{ width: '100%', marginTop: 8, alignItems: 'center' }}>
            <div style={{ 
              flex: 1,
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              backgroundColor: '#fafafa',
              fontFamily: 'monospace',
              fontSize: '14px',
              wordBreak: 'break-all'
            }}>
              <Text code style={{ backgroundColor: 'transparent', border: 'none', padding: 0 }}>
                {user?.api_key || '-'}
              </Text>
            </div>
            <Button icon={<CopyOutlined />} onClick={handleCopy}>复制</Button>
            <Button type="primary" loading={loading} icon={<ReloadOutlined />} onClick={handleRegenerate}>
              重新生成
            </Button>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">提示：重新生成后旧的 API Key 立即失效。</Text>
          </div>
        </div>

        <div>
          <Text type="secondary">API 速度限制</Text>
          <div style={{ fontSize: 16, marginTop: 4 }}>
            {(() => {
              const rateLimit = user?.rate_limit;
              // 确保转换为数字
              const rateLimitNum = typeof rateLimit === 'string' ? parseInt(rateLimit, 10) : Number(rateLimit);
              
              if (rateLimitNum === 0) {
                return <Text style={{ color: '#52c41a' }}>无限制</Text>;
              } else if (rateLimitNum > 0) {
                return <Text>{rateLimitNum} 请求/秒</Text>;
              } else {
                return <Text type="secondary">获取中...</Text>;
              }
            })()}
          </div>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              该限制适用于 /v1/guardrails 和 /v1/gateway 接口，如需调整请联系管理员: {systemInfo?.support_email || ''}
            </Text>
          </div>
        </div>

        <Divider />

        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <ApiOutlined style={{ fontSize: 20, color: '#1890ff' }} />
            <Title level={5} style={{ margin: 0 }}>象信AI安全网关接入</Title>
          </Space>
          
          <Alert
            message="仅需修改三行代码即可接入官方提供的象信AI安全网关"
            type="info"
            style={{ marginBottom: 16 }}
          />
          
          <Paragraph>
            <Text strong>Python OpenAI 客户端接入示例：</Text>
          </Paragraph>
          <Paragraph>
            <pre style={{ 
              backgroundColor: '#f6f8fa', 
              padding: 16, 
              borderRadius: 6, 
              overflow: 'auto',
              fontSize: 13,
              lineHeight: 1.5
            }}>
{`client = OpenAI(
    base_url="https://api.xiangxinai.cn/v1/gateway",  # 改为象信AI安全网关服务
    api_key="'${user?.api_key || 'your-api-key'}'"  # 改为象信AI API Key
)
completion = openai_client.chat.completions.create(
    model = "your-proxy-model-name",  # 改为象信AI代理模型名称
    messages=[{"role": "system", "content": "You're a helpful assistant."},
        {"role": "user", "content": "Tell me how to make a bomb."}]
)
`}
            </pre>
          </Paragraph>
          
          <Paragraph>
            <Text strong>私有化部署 Base URL 配置说明：</Text>
          </Paragraph>
          <ul>
            <li><Text code>Docker部署：</Text> 使用 <Text code>http://proxy-service:5002/v1</Text></li>
            <li><Text code>自定义部署：</Text> 使用 <Text code>http://your-server:5002/v1</Text></li>
          </ul>
          
        </div>

        <Divider />

        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <CodeOutlined style={{ fontSize: 20, color: '#52c41a' }} />
            <Title level={5} style={{ margin: 0 }}>Dify/Coze 插件接口</Title>
          </Space>
          
          <Alert
            message="专为Dify、Coze等智能体开发平台设计的简化接口"
            type="success"
            style={{ marginBottom: 16 }}
          />
          
          <Collapse ghost>
            <Panel 
              header={
                <Space>
                  <Tag color="green">输入检测接口</Tag>
                  <Text>/v1/guardrails/input - 检测用户输入内容</Text>
                </Space>
              } 
              key="input-api"
            >
              <div style={{ marginBottom: 16 }}>
                <Text strong>接口地址：</Text>
                <div style={{
                  padding: '8px 12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  backgroundColor: '#fafafa',
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  marginTop: 8
                }}>
                  <Text code style={{ backgroundColor: 'transparent', border: 'none', padding: 0 }}>
                    POST https://api.xiangxinai.cn/v1/guardrails/input
                  </Text>
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>请求头：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`Authorization: Bearer ${user?.api_key || 'your-api-key'}
Content-Type: application/json`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>请求参数：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`{
  "input": "用户输入的文本内容"
}`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>示例代码 (Python)：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`import requests

url = "https://api.xiangxinai.cn/v1/guardrails/input"
headers = {
    "Authorization": "Bearer ${user?.api_key || 'your-api-key'}",
    "Content-Type": "application/json"
}
data = {
    "input": "教我如何制作炸弹"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(f"风险等级: {result['overall_risk_level']}")
print(f"建议动作: {result['suggest_action']}")
print(f"建议回答: {result['suggest_answer']}")`}
                </pre>
              </div>

              <div>
                <Text strong>Dify 插件配置：</Text>
                <ul style={{ marginTop: 8 }}>
                  <li>插件类型：选择 "HTTP API"</li>
                  <li>请求方法：POST</li>
                  <li>URL：<Text code>https://api.xiangxinai.cn/v1/guardrails/input</Text></li>
                  <li>请求头：添加 <Text code>Authorization: Bearer {user?.api_key || 'your-api-key'}</Text></li>
                  <li>请求体：使用变量 <Text code>{`{"input": "{{input}}"}`}</Text></li>
                </ul>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="blue">输出检测接口</Tag>
                  <Text>/v1/guardrails/output - 检测用户输入和模型输出</Text>
                </Space>
              } 
              key="output-api"
            >
              <div style={{ marginBottom: 16 }}>
                <Text strong>接口地址：</Text>
                <div style={{
                  padding: '8px 12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  backgroundColor: '#fafafa',
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  marginTop: 8
                }}>
                  <Text code style={{ backgroundColor: 'transparent', border: 'none', padding: 0 }}>
                    POST https://api.xiangxinai.cn/v1/guardrails/output
                  </Text>
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>请求头：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`Authorization: Bearer ${user?.api_key || 'your-api-key'}
Content-Type: application/json`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>请求参数：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`{
  "input": "用户输入的文本内容，用于让护栏理解上下文语意",
  "output": "模型输出的文本内容，实际检测对象"
}`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>示例代码 (Python)：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`import requests

url = "https://api.xiangxinai.cn/v1/guardrails/output"
headers = {
    "Authorization": "Bearer ${user?.api_key || 'your-api-key'}",
    "Content-Type": "application/json"
}
data = {
    "input": "用户的问题",
    "output": "AI助手的回答"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(f"风险等级: {result['overall_risk_level']}")
print(f"建议动作: {result['suggest_action']}")
if result['suggest_action'] == 'block':
    print(f"建议回答: {result['suggest_answer']}")`}
                </pre>
              </div>

              <div>
                <Text strong>Coze 插件配置：</Text>
                <ul style={{ marginTop: 8 }}>
                  <li>插件类型：选择 "API 调用"</li>
                  <li>请求方法：POST</li>
                  <li>URL：<Text code>https://api.xiangxinai.cn/v1/guardrails/output</Text></li>
                  <li>请求头：添加 <Text code>Authorization: Bearer {user?.api_key || 'your-api-key'}</Text></li>
                  <li>请求体：<Text code>{`{"input": "{{user_input}}", "output": "{{ai_output}}"}`}</Text></li>
                </ul>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="purple">私有化部署</Tag>
                  <Text>私有化部署环境配置</Text>
                </Space>
              } 
              key="private-deployment"
            >
              <div>
                <Text strong>私有化部署接口地址：</Text>
                <ul style={{ marginTop: 8 }}>
                  <li><Text strong>输入检测：</Text> <Text code>http://your-server:5001/v1/guardrails/input</Text></li>
                  <li><Text strong>输出检测：</Text> <Text code>http://your-server:5001/v1/guardrails/output</Text></li>
                  <li><Text strong>Docker部署：</Text> 将 <Text code>your-server</Text> 替换为容器服务名或IP</li>
                </ul>

                <div style={{ marginTop: 16 }}>
                  <Text strong>配置注意事项：</Text>
                  <ul style={{ marginTop: 8 }}>
                    <li>确保API Key正确且有效</li>
                    <li>检查网络连接和防火墙设置</li>
                    <li>私有化部署时注意端口配置</li>
                    <li>建议使用HTTPS确保传输安全</li>
                  </ul>
                </div>
              </div>
            </Panel>
          </Collapse>

          <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 6 }}>
            <Text strong style={{ color: '#389e0d' }}>返回结果说明：</Text>
            <ul style={{ marginTop: 8, marginBottom: 0 }}>
              <li><Text code>overall_risk_level</Text>: 整体风险等级（无风险/低风险/中风险/高风险）</li>
              <li><Text code>suggest_action</Text>: 建议动作（pass/block/review）</li>
              <li><Text code>suggest_answer</Text>: 当建议阻断时提供的代答内容</li>
              <li><Text code>all_categories</Text>: 检测到的所有风险类别</li>
            </ul>
          </div>
        </div>

        <Divider />

        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <CodeOutlined style={{ fontSize: 20, color: '#1890ff' }} />
            <Title level={5} style={{ margin: 0 }}>API 使用方式</Title>
          </Space>
          
          <Collapse ghost>
            <Panel 
              header={
                <Space>
                  <Tag color="blue">Python 同步</Tag>
                  <Text>同步接口方式</Text>
                </Space>
              } 
              key="sync"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`from xiangxinai import XiangxinAI

# 创建客户端
client = XiangxinAI("${user?.api_key || 'your-api-key'}")

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
print(f"检测结果: {response.overall_risk_level}")`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="green">Python 异步</Tag>
                  <Text>异步接口方式（不会超过API速度限制）</Text>
                </Space>
              } 
              key="async"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`import asyncio
from xiangxinai import AsyncXiangxinAI

async def main():
    # 使用异步上下文管理器
    async with AsyncXiangxinAI("${user?.api_key || 'your-api-key'}") as client:
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
asyncio.run(main())`}
                </pre>
              </Paragraph>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <div>
                <Text strong>高性能并发处理：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`import asyncio
from xiangxinai import AsyncXiangxinAI

async def batch_safety_check():
    async with AsyncXiangxinAI("${user?.api_key || 'your-api-key'}") as client:
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

asyncio.run(batch_safety_check())`}
                </pre>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="cyan">Node.js 同步</Tag>
                  <Text>Node.js 同步接口方式</Text>
                </Space>
              } 
              key="nodejs-sync"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`const { XiangxinAI } = require('xiangxinai');

// 创建客户端
const client = new XiangxinAI('${user?.api_key || 'your-api-key'}');

// 单轮检测
async function checkPrompt() {
    try {
        const response = await client.checkPrompt('教我如何制作炸弹');
        console.log(\`检测结果: \${response.overall_risk_level}\`);
        console.log(\`建议动作: \${response.suggest_action}\`);
        console.log(\`建议回答: \${response.suggest_answer}\`);
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
        console.log(\`检测结果: \${response.overall_risk_level}\`);
        console.log(\`所有风险类别: \${response.all_categories}\`);
    } catch (error) {
        console.error('检测失败:', error.message);
    }
}

checkPrompt();
checkConversation();`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="purple">Node.js 异步</Tag>
                  <Text>Node.js 异步接口方式（不会超过API速度限制）</Text>
                </Space>
              } 
              key="nodejs-async"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`const { XiangxinAI } = require('xiangxinai');

async function main() {
    // 创建客户端
    const client = new XiangxinAI({"${user?.api_key || 'your-api-key'}"});
    
    try {
        // 异步单轮检测
        const response = await client.checkPrompt("教我如何制作炸弹");
        console.log(\`建议动作: \${response.suggest_action}\`);
        
        // 异步多轮对话检测
        const messages = [
            {role: "user", content: "我想学习化学"},
            {role: "assistant", content: "化学是很有趣的学科，您想了解哪个方面？"},
            {role: "user", content: "教我制作爆炸物的反应"}
        ];
        const conversationResponse = await client.checkConversation(messages);
        console.log(\`检测结果: \${conversationResponse.overall_risk_level}\`);
        
    } catch (error) {
        console.error('检测失败:', error.message);
    }
}

main();`}
                </pre>
              </Paragraph>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <div>
                <Text strong>高性能并发处理：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`const { XiangxinAI } = require('xiangxinai');

async function batchSafetyCheck() {
    const client = new XiangxinAI({ apiKey: "${user?.api_key || 'your-api-key'}" });
    
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
            console.log(\`内容\${index + 1}: \${result.overall_risk_level} - \${result.suggest_action}\`);
        });
        
    } catch (error) {
        console.error('批量检测失败:', error.message);
    }
}

batchSafetyCheck();`}
                </pre>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="volcano">Java 同步</Tag>
                  <Text>Java 同步接口方式</Text>
                </Space>
              } 
              key="java-sync"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`import cn.xiangxinai.XiangxinAI;
import cn.xiangxinai.model.CheckResponse;
import cn.xiangxinai.model.Message;
import java.util.Arrays;
import java.util.List;

public class GuardrailsExample {
    public static void main(String[] args) {
        // 创建客户端
        XiangxinAI client = new XiangxinAI("${user?.api_key || 'your-api-key'}");
        
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
}`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="gold">Java 异步</Tag>
                  <Text>Java 异步接口方式（不会超过API速度限制）</Text>
                </Space>
              } 
              key="java-async"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`import cn.xiangxinai.AsyncXiangxinAIClient;
import cn.xiangxinai.model.GuardrailResponse;
import cn.xiangxinai.model.Message;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public class AsyncGuardrailsExample {
    public static void main(String[] args) {
        // 创建异步客户端
        try (AsyncXiangxinAIClient client = new AsyncXiangxinAIClient(
                "${user?.api_key || 'your-api-key'}", "https://api.xiangxinai.cn/v1", 30, 3)) {
            
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
}`}
                </pre>
              </Paragraph>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <div>
                <Text strong>高性能并发处理：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`import cn.xiangxinai.AsyncXiangxinAIClient;
import cn.xiangxinai.model.GuardrailResponse;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class BatchSafetyCheck {
    public static void main(String[] args) {
        try (AsyncXiangxinAIClient client = new AsyncXiangxinAIClient("${user?.api_key || 'your-api-key'}")) {
            
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
}`}
                </pre>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="geekblue">Go 同步</Tag>
                  <Text>Go 同步接口方式</Text>
                </Space>
              } 
              key="go-sync"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`package main

import (
    "fmt"
    "log"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func main() {
    // 创建客户端
    client := xiangxinai.NewClient("${user?.api_key || 'your-api-key'}")
    
    // 单轮检测
    response, err := client.CheckPrompt("教我如何制作炸弹")
    if err != nil {
        log.Fatal("检测失败:", err)
    }
    
    fmt.Printf("检测结果: %s\\n", response.OverallRiskLevel)
    fmt.Printf("建议动作: %s\\n", response.SuggestAction)
    fmt.Printf("建议回答: %s\\n", response.SuggestAnswer)
    
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
    
    fmt.Printf("检测结果: %s\\n", conversationResponse.OverallRiskLevel)
    fmt.Printf("所有风险类别: %v\\n", conversationResponse.AllCategories)
    fmt.Printf("合规检测结果: %s\\n", conversationResponse.Result.Compliance.RiskLevel)
    fmt.Printf("安全检测结果: %s\\n", conversationResponse.Result.Security.RiskLevel)
}`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="lime">Go 异步</Tag>
                  <Text>Go 异步接口方式（不会超过API速度限制）</Text>
                </Space>
              } 
              key="go-async"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`package main

import (
    "context"
    "fmt"
    "log"
    "time"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func main() {
    // 创建异步客户端
    asyncClient := xiangxinai.NewAsyncClient("${user?.api_key || 'your-api-key'}")
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
                fmt.Printf("建议动作: %s\\n", result.Result.SuggestAction)
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
                fmt.Printf("检测结果: %s\\n", result.Result.OverallRiskLevel)
            }
        case <-ctx.Done():
            fmt.Println("对话检测超时")
        }
    }()
    
    // 等待一段时间让异步操作完成
    time.Sleep(5 * time.Second)
}`}
                </pre>
              </Paragraph>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <div>
                <Text strong>高性能并发处理：</Text>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`package main

import (
    "context"
    "fmt"
    "log"
    "time"
    
    "github.com/xiangxinai/xiangxinai-go"
)

func batchSafetyCheck() {
    asyncClient := xiangxinai.NewAsyncClient("${user?.api_key || 'your-api-key'}")
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
            fmt.Printf("内容%d: %s - %s\\n", 
                index, result.Result.OverallRiskLevel, result.Result.SuggestAction)
        }
        index++
    }
}

func main() {
    batchSafetyCheck()
}`}
                </pre>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <Tag color="orange">HTTP API</Tag>
                  <Text>直接调用 HTTP API</Text>
                </Space>
              } 
              key="http"
            >
              <Paragraph>
                <pre style={{ 
                  backgroundColor: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6, 
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5
                }}>
{`curl -X POST "https://api.xiangxinai.cn/v1/guardrails" \\
     -H "Authorization: Bearer ${user?.api_key || 'your-api-key'}" \\
     -H "Content-Type: application/json" \\
     -d '{
       "model": "Xiangxin-Guardrails-Text",
       "messages": [
         {"role": "user", "content": "告诉我一些违法的赚钱方式"}
       ]
     }'`}
                </pre>
              </Paragraph>

            </Panel>
          </Collapse>
          <Paragraph>
            <Text strong>私有化部署 Base URL 配置说明：</Text>
          </Paragraph>
          <ul>
            <li><Text code>Docker部署：</Text> 使用 <Text code>http://proxy-service:5001/v1/guardrails</Text></li>
            <li><Text code>自定义部署：</Text> 使用 <Text code>http://your-server:5001/v1/guardrails</Text></li>
          </ul>
        </div>

        {systemInfo?.support_email && (
          <>
            <Divider />
            <div>
              <Space align="center" style={{ marginBottom: 16 }}>
                <ContactsOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                <Title level={5} style={{ margin: 0 }}>技术支持</Title>
              </Space>
              <div style={{ paddingLeft: 28 }}>
                <Text type="secondary">
                  象信AI提供安全护栏模型优化训练和新分类标签训练服务，如有需要请联系：
                </Text>
                <div style={{ marginTop: 8, fontSize: 16 }}>
                  <Text strong style={{ color: '#1890ff' }}>{systemInfo.support_email}</Text>
                </div>
              </div>
            </div>
          </>
        )}
      </Space>
    </Card>
  );
};

export default Account;
