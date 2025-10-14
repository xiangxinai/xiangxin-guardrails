import React, { useEffect, useState } from 'react';
import { Card, Typography, Space, Button, message, Divider, Collapse, Tag, Alert } from 'antd';
import { CopyOutlined, ReloadOutlined, SafetyCertificateOutlined, ContactsOutlined, CodeOutlined, ApiOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchMe = async () => {
    try {
      const me = await authService.getCurrentUser();
      setUser(me);
    } catch (e) {
      message.error(t('account.fetchUserInfoFailed'));
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const info = await configApi.getSystemInfo();
      setSystemInfo(info);
    } catch (e) {
      console.error('Fetch system info failed', e);
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
      message.success(t('account.copied'));
    } catch {
      message.error(t('account.copyFailed'));
    }
  };

  const handleRegenerate = async () => {
    try {
      setLoading(true);
      const data = await authService.regenerateApiKey();
      message.success(t('account.apiKeyUpdated'));
      setUser((prev: UserInfo | null) => prev ? { ...prev, api_key: data.api_key } : prev);
    } catch (e: any) {
      message.error(e.message || t('account.operationFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space align="center">
          <SafetyCertificateOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>{t('account.title')}</Title>
        </Space>

        <div>
          <Text type="secondary">{t('account.email')}</Text>
          <div style={{ fontSize: 16 }}>{user?.email || '-'}</div>
        </div>

        <div>
          <Text type="secondary">{t('account.tenantUuid')}</Text>
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
                  message.success(t('account.uuidCopied'));
                }
              }}
            >
              {t('account.copy')}
            </Button>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">{t('account.uuidNote')}</Text>
          </div>
        </div>

        <div>
          <Text type="secondary">{t('account.currentApiKey')}</Text>
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
            <Button icon={<CopyOutlined />} onClick={handleCopy}>{t('account.copy')}</Button>
            <Button type="primary" loading={loading} icon={<ReloadOutlined />} onClick={handleRegenerate}>
              {t('account.regenerate')}
            </Button>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">{t('account.regenerateWarning')}</Text>
          </div>
        </div>

        <div>
          <Text type="secondary">{t('account.apiRateLimit')}</Text>
          <div style={{ fontSize: 16, marginTop: 4 }}>
            {(() => {
              const rateLimit = user?.rate_limit;
              // Ensure conversion to number
              const rateLimitNum = typeof rateLimit === 'string' ? parseInt(rateLimit, 10) : Number(rateLimit);

              if (rateLimitNum === 0) {
                return <Text style={{ color: '#52c41a' }}>{t('account.unlimited')}</Text>;
              } else if (rateLimitNum > 0) {
                return <Text>{t('account.rateLimitValue', { limit: rateLimitNum })}</Text>;
              } else {
                return <Text type="secondary">{t('common.loading')}</Text>;
              }
            })()}
          </div>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {t('account.rateLimitNote', { email: systemInfo?.support_email || '' })}
            </Text>
          </div>
        </div>

        <Divider />

        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <ApiOutlined style={{ fontSize: 20, color: '#1890ff' }} />
            <Title level={5} style={{ margin: 0 }}>{t('account.apiDocumentation')}</Title>
          </Space>

          <Alert
            message={t('account.quickStartAlert')}
            type="info"
            style={{ marginBottom: 16 }}
          />

          <Paragraph>
            <Text strong>{t('account.apiReference')}</Text>
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
    base_url="https://api.xiangxinai.cn/v1/gateway",  # ${t('account.codeComments.changeToGatewayUrl')}
    api_key="'${user?.api_key || 'your-api-key'}'"  # ${t('account.codeComments.changeToApiKey')}
)
completion = openai_client.chat.completions.create(
    model = "your-proxy-model-name",  # ${t('account.codeComments.changeToModelName')}
    messages=[{"role": "system", "content": "You're a helpful assistant."},
        {"role": "user", "content": "Tell me how to make a bomb."}]
    # Other parameters are the same as the original usage method
)
`}
            </pre>
          </Paragraph>

          <Paragraph>
            <Text strong>{t('account.sdkIntegration')}</Text>
          </Paragraph>
          <ul>
            <li><Text code>{t('account.dockerDeploymentConfig')}</Text></li>
            <li><Text code>{t('account.customDeploymentConfig')}</Text></li>
          </ul>

        </div>

        <Divider />

        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <CodeOutlined style={{ fontSize: 20, color: '#52c41a' }} />
            <Title level={5} style={{ margin: 0 }}>{t('account.examples')}</Title>
          </Space>

          <Alert
            message={t('account.quickStartAlert')}
            type="success"
            style={{ marginBottom: 16 }}
          />

          <Collapse ghost>
            <Panel
              header={
                <Space>
                  <Tag color="green">{t('account.inputDetectionInterface')}</Tag>
                  <Text>/v1/guardrails/input - {t('account.inputDetectionDesc')}</Text>
                </Space>
              }
              key="input-api"
            >
              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.interfaceAddress')}:</Text>
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
                <Text strong>{t('account.requestHeaders')}:</Text>
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
                <Text strong>{t('account.requestParameters')}:</Text>
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
  "input": "User input text content",
  "xxai_app_user_id": "your-app-user-id"  // Optional: Tenant AI application user ID
}`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.exampleCode')}:</Text>
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
    "input": "Teach me how to make a bomb",
    "xxai_app_user_id": "your-app-user-id"  # Optional: Tenant AI application user ID
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

# Recommend using result['suggest_action'] to determine safety.
if result['suggest_action'] == "pass":
    print("Safe")
else:
    print(f"Unsafe")
    print(f"Risk level: {result['overall_risk_level']}")
    print(f"Suggested action: {result['suggest_action']}")
    print(f"Risk categories: {result['all_categories']}")
    print(f"Suggested answer: {result['suggest_answer']}")`}
                </pre>
              </div>

              <div>
                <Text strong>{t('account.difyPluginConfig')}:</Text>
                <ul style={{ marginTop: 8 }}>
                  <li>{t('account.pluginType')}: {t('account.selectHttpApi')}</li>
                  <li>{t('account.requestMethod')}: POST</li>
                  <li>URL: <Text code>https://api.xiangxinai.cn/v1/guardrails/input</Text></li>
                  <li>{t('account.requestHeaders')}: <Text code>Authorization: Bearer {user?.api_key || 'your-api-key'}</Text></li>
                  <li>{t('account.requestBody')}: <Text code>{`{"input": "{{input}}"}`}</Text></li>
                </ul>
              </div>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="blue">{t('account.outputDetectionInterface')}</Tag>
                  <Text>/v1/guardrails/output - {t('account.outputDetectionDesc')}</Text>
                </Space>
              }
              key="output-api"
            >
              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.interfaceAddress')}:</Text>
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
                <Text strong>{t('account.requestHeaders')}:</Text>
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
                <Text strong>{t('account.requestParameters')}:</Text>
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
  "input": "User input text content, used to help the guardrails understand the context",
  "output": "Model output text content, actual detection object"
}`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.exampleCode')}:</Text>
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
    "input": "User question",
    "output": "AI assistant answer",
    "xxai_app_user_id": "your-app-user-id"  # Optional: Tenant AI application user ID
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(f"Suggested action: {result['suggest_action']}")`}
                </pre>
              </div>

              <div>
                <Text strong>{t('account.cozePluginConfig')}:</Text>
                <ul style={{ marginTop: 8 }}>
                  <li>{t('account.pluginType')}: {t('account.selectApiCall')}</li>
                  <li>{t('account.requestMethod')}: POST</li>
                  <li>URL: <Text code>https://api.xiangxinai.cn/v1/guardrails/output</Text></li>
                  <li>{t('account.requestHeaders')}: <Text code>Authorization: Bearer {user?.api_key || 'your-api-key'}</Text></li>
                  <li>{t('account.requestBody')}: <Text code>{`{"input": "{{user_input}}", "output": "{{ai_output}}"}`}</Text></li>
                </ul>
              </div>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="cyan">{t('account.pythonClientLibrary')}</Tag>
                  <Text>{t('account.pythonClientDesc')}</Text>
                </Space>
              }
              key="python-client"
            >
              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.installClientLibrary')}:</Text>
                <pre style={{
                  backgroundColor: '#f6f8fa',
                  padding: 16,
                  borderRadius: 6,
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`pip install xiangxinai`}
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.usageExample')}:</Text>
                <pre style={{
                  backgroundColor: '#f6f8fa',
                  padding: 16,
                  borderRadius: 6,
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
{`from xiangxinai import XiangxinAI

# Create client
client = XiangxinAI("${user?.api_key || 'your-api-key'}")

# Single round detection
response = client.check_prompt("Teach me how to make a bomb", user_id="your-app-user-id")
# Recommend using response.suggest_action to determine safety.
if response.suggest_action == "pass":
    print("Safe")
else:
    print(f"Unsafe")
    print(f"Risk level: {response.overall_risk_level}")
    # response.overall_risk_level: through, no risk, low risk, high risk
    print(f"Suggested action: {response.suggest_action}")
    # response.suggest_action: through, answer, refuse
    print(f"Risk categories: {response.all_categories}")
    print(f"Suggested answer: {response.suggest_answer}")

# Detect model output (context-aware)
response = client.check_response_ctx("Teach me how to make a bomb", "好的", user_id="your-app-user-id")
print(f"Suggested action: {response.suggest_action}")`}
                </pre>
              </div>

              <div>
                <Text strong>{t('account.configurationNotes')}:</Text>
                <ul style={{ marginTop: 8 }}>
                  <li>{t('account.defaultOfficialService')}: <Text code>https://api.xiangxinai.cn/v1</Text></li>
                  <li>{t('account.privateDeployment')}: {t('account.createClientSpecifyBaseUrl')}</li>
                  <li>{t('account.example')}: <Text code>XiangxinAI(api_key="your-key", base_url="http://your-server:5001/v1")</Text></li>
                </ul>
              </div>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="purple">{t('account.privateDeployment')}</Tag>
                  <Text>{t('account.privateDeploymentDesc')}</Text>
                </Space>
              }
              key="private-deployment"
            >
              <div>
                <Text strong>{t('account.privateDeploymentAddresses')}:</Text>
                <ul style={{ marginTop: 8 }}>
                  <li><Text strong>{t('account.inputDetectionAddr')}:</Text> <Text code>http://your-server:5001/v1/guardrails/input</Text></li>
                  <li><Text strong>{t('account.outputDetectionAddr')}:</Text> <Text code>http://your-server:5001/v1/guardrails/output</Text></li>
                  <li><Text strong>{t('account.dockerDeployment')}:</Text> {t('account.dockerDeploymentNote')}</li>
                </ul>

                <div style={{ marginTop: 16 }}>
                  <Text strong>{t('account.configurationPrecautions')}:</Text>
                  <ul style={{ marginTop: 8 }}>
                    <li>{t('account.ensureApiKeyValid')}</li>
                    <li>{t('account.checkNetworkFirewall')}</li>
                    <li>{t('account.notePortConfiguration')}</li>
                    <li>{t('account.recommendHttps')}</li>
                  </ul>
                </div>
              </div>
            </Panel>
          </Collapse>

          <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 6 }}>
            <Text strong style={{ color: '#389e0d' }}>{t('account.returnResultDescription')}:</Text>
            <ul style={{ marginTop: 8, marginBottom: 0 }}>
              <li><Text code>overall_risk_level</Text>: {t('account.overallRiskLevelDesc')}</li>
              <li><Text code>suggest_action</Text>: {t('account.suggestActionDesc')}</li>
              <li><Text code>suggest_answer</Text>: {t('account.suggestAnswerDesc')}</li>
              <li><Text code>all_categories</Text>: {t('account.allCategoriesDesc')}</li>
            </ul>
          </div>
        </div>

        <Divider />

        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <CodeOutlined style={{ fontSize: 20, color: '#1890ff' }} />
            <Title level={5} style={{ margin: 0 }}>{t('account.apiUsageMethods')}</Title>
          </Space>

          <Collapse ghost>
            <Panel
              header={
                <Space>
                  <Tag color="blue">{t('account.pythonSync')}</Tag>
                  <Text>{t('account.pythonSyncDesc')}</Text>
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

# Create client
client = XiangxinAI("${user?.api_key || 'your-api-key'}")

# Single round detection
response = client.check_prompt("Teach me how to make a bomb", user_id="your-app-user-id")
# Recommend using response.suggest_action to determine safety.
if response.suggest_action == "pass":
    print("Safe")
else:
    print(f"Unsafe")
    print(f"Risk level: {response.overall_risk_level}")
    print(f"Suggested action: {response.suggest_action}")
    print(f"Risk categories: {response.all_categories}")
    print(f"Suggested answer: {response.suggest_answer}")

# Detect model output (context-aware)
response = client.check_response_ctx("Teach me how to make a bomb", "OK, I'll help you with that.", user_id="your-app-user-id")
print(f"Suggested action: {response.suggest_action}")

# Detect conversation (context-aware)
messages = [
    {"role": "user", "content": "I want to study chemistry"},
    {"role": "assistant", "content": "Chemistry is a very interesting subject. Which area would you like to learn about?"},
    {"role": "user", "content": "Teach me the reaction to make explosives"}
]
response = client.check_conversation(messages)
print(f"Detection result: {response.overall_risk_level}")`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="green">{t('account.pythonAsync')}</Tag>
                  <Text>{t('account.pythonAsyncDesc')}</Text>
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
    # Use asynchronous context manager
    async with AsyncXiangxinAI("${user?.api_key || 'your-api-key'}") as client:
        # Asynchronous single round detection
        response = await client.check_prompt("Teach me how to make a bomb", user_id="your-app-user-id")
        print(f"Suggested action: {response.suggest_action}")

        # Detect model output (context-aware)
        response = await client.check_response_ctx("Teach me how to make a bomb", "OK, I'll help you with that.", user_id="your-app-user-id")
        print(f"Suggested action: {response.suggest_action}")

        # Asynchronous multi-turn conversation detection
        messages = [
            {"role": "user", "content": "I want to study chemistry"},
            {"role": "assistant", "content": "Chemistry is a very interesting subject. Which area would you like to learn about?"},
            {"role": "user", "content": "Teach me the reaction to make explosives"}
        ]
        response = await client.check_conversation(messages)
        print(f"Detection result: {response.overall_risk_level}")

# Run asynchronous function
asyncio.run(main())`}
                </pre>
              </Paragraph>

              <Divider style={{ margin: '12px 0' }} />

              <div>
                <Text strong>{t('account.highPerformanceConcurrent')}:</Text>
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
        # Concurrent processing of multiple detection requests
        contents = [
            "I want to study programming",
            "What's the weather like today?",
            "Teach me how to make a cake",
            "How to learn English?"
        ]

        # Create concurrent tasks
        tasks = [client.check_prompt(content) for content in contents]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        # Process results
        for i, result in enumerate(results):
            print(f"Content {i+1}: {result.overall_risk_level} - {result.suggest_action}")

asyncio.run(batch_safety_check())`}
                </pre>
              </div>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="cyan">{t('account.nodejsSync')}</Tag>
                  <Text>{t('account.nodejsSyncDesc')}</Text>
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

// Create client
const client = new XiangxinAI('${user?.api_key || 'your-api-key'}');

// Single round detection
async function checkPrompt() {
    try {
        const response = await client.checkPrompt('Teach me how to make a bomb');
        // Recommend using response.suggest_action to determine safety.
        if (response.suggest_action === "pass") {
            console.log("Safe");
        } else {
            console.log("Unsafe");
            console.log(\`Risk level: \${response.overall_risk_level}\`);
            console.log(\`Suggested action: \${response.suggest_action}\`);
            console.log(\`Risk categories: \${response.all_categories}\`);
            console.log(\`Suggested answer: \${response.suggest_answer}\`);
        }
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
        console.log(\`Detection result: \${response.overall_risk_level}\`);
        console.log(\`Risk categories: \${response.all_categories}\`);
    } catch (error) {
        console.error('Detection failed:', error.message);
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
                  <Tag color="purple">{t('account.nodejsAsync')}</Tag>
                  <Text>{t('account.nodejsAsyncDesc')}</Text>
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
    // Create client
    const client = new XiangxinAI({"${user?.api_key || 'your-api-key'}"});

    try {
        // Asynchronous single round detection
        const response = await client.checkPrompt("Teach me how to make a bomb");
        console.log(\`建议行动: \${response.suggest_action}\`);

        // Asynchronous multi-turn conversation detection
        const messages = [
            {role: "user", content: "I want to study chemistry"},
            {role: "assistant", content: "Chemistry is a very interesting subject. Which area would you like to learn about?"},
            {role: "user", content: "Teach me the reaction to make explosives"}
        ];
        const conversationResponse = await client.checkConversation(messages);
        console.log(\`Detection result: \${conversationResponse.overall_risk_level}\`);

    } catch (error) {
        console.error('Detection failed:', error.message);
    }
}

main();`}
                </pre>
              </Paragraph>

              <Divider style={{ margin: '12px 0' }} />

              <div>
                <Text strong>{t('account.highPerformanceConcurrent')}:</Text>
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

    // Concurrent processing of multiple detection requests
    const contents = [
        "I want to study programming",
        "What's the weather like today?",
        "Teach me how to make a cake",
        "How to learn English?"
    ];

    try {
        // Create concurrent tasks
        const promises = contents.map(content => client.checkPrompt(content));

        // Wait for all tasks to complete
        const results = await Promise.all(promises);

        // Process results
        results.forEach((result, index) => {
            console.log(\`Content \${index + 1}: \${result.overall_risk_level} - \${result.suggest_action}\`);
        });

    } catch (error) {
        console.error('Batch detection failed:', error.message);
    }
}

batchSafetyCheck();`}
                </pre>
              </div>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="volcano">{t('account.javaSync')}</Tag>
                  <Text>{t('account.javaSyncDesc')}</Text>
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
        // Create client
        XiangxinAI client = new XiangxinAI("${user?.api_key || 'your-api-key'}");

        try {
            // Single round detection
            CheckResponse response = client.checkPrompt("Teach me how to make a bomb");
            // Recommend using response.getSuggestAction() to determine safety.
            if ("通过".equals(response.getSuggestAction())) {
                System.out.println("Safe");
            } else {
                System.out.println("Unsafe");
                System.out.println("Risk level: " + response.getOverallRiskLevel());
                System.out.println("Suggested action: " + response.getSuggestAction());
                System.out.println("Risk categories: " + response.getAllCategories());
                System.out.println("Suggested answer: " + response.getSuggestAnswer());
            }

            // Multi-turn conversation detection (context-aware)
            List<Message> messages = Arrays.asList(
                new Message("user", "I want to study chemistry"),
                new Message("assistant", "Chemistry is a very interesting subject. Which area would you like to learn about?"),
                new Message("user", "Teach me the reaction to make explosives")
            );

            CheckResponse conversationResponse = client.checkConversation(messages);
            System.out.println("Detection result: " + conversationResponse.getOverallRiskLevel());
            System.out.println("Risk categories: " + conversationResponse.getAllCategories());
            System.out.println("Compliance check result: " + conversationResponse.getResult().getCompliance().getRiskLevel());
            System.out.println("Security check result: " + conversationResponse.getResult().getSecurity().getRiskLevel());

        } catch (Exception e) {
            System.err.println("Detection failed: " + e.getMessage());
        }
    }
}`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="gold">{t('account.javaAsync')}</Tag>
                  <Text>{t('account.javaAsyncDesc')}</Text>
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
        // Create asynchronous client
        try (AsyncXiangxinAIClient client = new AsyncXiangxinAIClient(
                "${user?.api_key || 'your-api-key'}", "https://api.xiangxinai.cn/v1", 30, 3)) {

            // Asynchronous single round detection
            CompletableFuture<GuardrailResponse> future1 = client.checkPromptAsync("Teach me how to make a bomb");
            future1.thenAccept(response -> {
                System.out.println("Suggested action: " + response.getSuggestAction());
            }).exceptionally(throwable -> {
                System.err.println("Detection failed: " + throwable.getMessage());
                return null;
            });

            // Asynchronous multi-turn conversation detection
            List<Message> messages = Arrays.asList(
                new Message("user", "I want to study chemistry"),
                new Message("assistant", "Chemistry is a very interesting subject. Which area would you like to learn about?"),
                new Message("user", "Teach me the reaction to make explosives")
            );

            CompletableFuture<GuardrailResponse> future2 = client.checkConversationAsync(messages);
            future2.thenAccept(response -> {
                System.out.println("Detection result: " + response.getOverallRiskLevel());
            }).exceptionally(throwable -> {
                System.err.println("Detection failed: " + throwable.getMessage());
                return null;
            });

            // Wait for asynchronous operations to complete
            CompletableFuture.allOf(future1, future2).join();

        } catch (Exception e) {
            System.err.println("Client error: " + e.getMessage());
        }
    }
}`}
                </pre>
              </Paragraph>

              <Divider style={{ margin: '12px 0' }} />

              <div>
                <Text strong>{t('account.highPerformanceConcurrent')}:</Text>
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

            // Concurrent processing of multiple detection requests
            List<String> contents = Arrays.asList(
                "I want to study programming",
                "What's the weather like today?",
                "Teach me how to make a cake",
                "How to learn English?"
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
}`}
                </pre>
              </div>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="geekblue">{t('account.goSync')}</Tag>
                  <Text>{t('account.goSyncDesc')}</Text>
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
    // Create client
    client := xiangxinai.NewClient("${user?.api_key || 'your-api-key'}")

    // Single round detection
    response, err := client.CheckPrompt("Teach me how to make a bomb")
    if err != nil {
        log.Fatal("Detection failed:", err)
    }

    // Recommend using response.SuggestAction to determine safety.
    if response.SuggestAction == "pass" {
        fmt.Println("Safe")
    } else {
        fmt.Println("Unsafe")
        fmt.Printf("Risk level: %s\\n", response.OverallRiskLevel)
        fmt.Printf("Suggested action: %s\\n", response.SuggestAction)
        fmt.Printf("Risk categories: %v\\n", response.AllCategories)
        fmt.Printf("Suggested answer: %s\\n", response.SuggestAnswer)
    }

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

    fmt.Printf("Detection result: %s\\n", conversationResponse.OverallRiskLevel)
    fmt.Printf("Risk categories: %v\\n", conversationResponse.AllCategories)
    fmt.Printf("Compliance check result: %s\\n", conversationResponse.Result.Compliance.RiskLevel)
    fmt.Printf("Security check result: %s\\n", conversationResponse.Result.Security.RiskLevel)
}`}
                </pre>
              </Paragraph>
            </Panel>

            <Panel
              header={
                <Space>
                  <Tag color="lime">{t('account.goAsync')}</Tag>
                  <Text>{t('account.goAsyncDesc')}</Text>
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
    // Create asynchronous client
    asyncClient := xiangxinai.NewAsyncClient("${user?.api_key || 'your-api-key'}")
    defer asyncClient.Close()

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    // Asynchronous single round detection
    resultChan1 := asyncClient.CheckPromptAsync(ctx, "Teach me how to make a bomb")
    go func() {
        select {
        case result := <-resultChan1:
            if result.Error != nil {
                log.Printf("Single round detection failed: %v", result.Error)
            } else {
                fmt.Printf("Suggested action: %s\\n", result.Result.SuggestAction)
            }
        case <-ctx.Done():
            fmt.Println("Single round detection timeout")
        }
    }()

    // Asynchronous multi-turn conversation detection
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
                log.Printf("Conversation detection failed: %v", result.Error)
            } else {
                fmt.Printf("Detection result: %s\\n", result.Result.OverallRiskLevel)
            }
        case <-ctx.Done():
            fmt.Println("Conversation detection timeout")
        }
    }()

    // Wait for asynchronous operations to complete
    time.Sleep(5 * time.Second)
}`}
                </pre>
              </Paragraph>

              <Divider style={{ margin: '12px 0' }} />

              <div>
                <Text strong>{t('account.highPerformanceConcurrent')}:</Text>
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

    // Concurrent processing of multiple detection requests
    contents := []string{
        "I want to study programming",
        "What's the weather like today?",
        "Teach me how to make a cake",
        "How to learn English?",
    }

    // Use batch asynchronous detection
    resultChan := asyncClient.BatchCheckPrompts(ctx, contents)

    // Process results
    index := 1
    for result := range resultChan {
        if result.Error != nil {
            log.Printf("Content %d detection failed: %v", index, result.Error)
        } else {
            fmt.Printf("Content %d: %s - %s\\n",
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
                  <Tag color="orange">{t('account.httpApi')}</Tag>
                  <Text>{t('account.httpApiDesc')}</Text>
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
         {"role": "user", "content": "Tell me some illegal ways to make money"}
       ],
       "extra_body": {
         "xxai_app_user_id": "your-app-user-id"
       }
     }'`}
                </pre>
              </Paragraph>

            </Panel>
          </Collapse>
          <Paragraph>
            <Text strong>{t('account.privateDeploymentBaseUrl')}:</Text>
          </Paragraph>
          <ul>
            <li><Text code>{t('account.dockerDeploymentConfig')}</Text></li>
            <li><Text code>{t('account.customDeploymentConfig')}</Text></li>
          </ul>
        </div>

        {systemInfo?.support_email && (
          <>
            <Divider />
            <div>
              <Space align="center" style={{ marginBottom: 16 }}>
                <ContactsOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                <Title level={5} style={{ margin: 0 }}>{t('account.contactSupport')}</Title>
              </Space>
              <div style={{ paddingLeft: 28 }}>
                <Text type="secondary">
                  {t('account.xiangxinAiServices')}
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
