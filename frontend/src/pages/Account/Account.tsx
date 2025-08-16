import React, { useEffect, useState } from 'react';
import { Card, Typography, Space, Input, Button, message, Divider, Collapse, Tag } from 'antd';
import { CopyOutlined, ReloadOutlined, SafetyCertificateOutlined, ContactsOutlined, CodeOutlined } from '@ant-design/icons';
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
              该限制仅适用于 /v1/guardrails 接口，如需调整请联系管理员: {systemInfo?.support_email || ''}
            </Text>
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
client = XiangxinAI(
    api_key="your-api-key"
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
    async with AsyncXiangxinAI(
        api_key="your-api-key"
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

asyncio.run(batch_safety_check())`}
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
     -H "Authorization: Bearer your-api-key" \\
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
