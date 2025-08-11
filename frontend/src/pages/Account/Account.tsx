import React, { useEffect, useState } from 'react';
import { Card, Typography, Space, Input, Button, message, Divider } from 'antd';
import { CopyOutlined, ReloadOutlined, SafetyCertificateOutlined, ContactsOutlined } from '@ant-design/icons';
import { authService, UserInfo } from '../../services/auth';
import { configApi } from '../../services/api';

const { Title, Text } = Typography;

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
      setUser(me);
    } catch (e) {
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
      setUser(prev => prev ? { ...prev, api_key: data.api_key } : prev);
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
          <Text type="secondary">当前 API Key</Text>
          <Space style={{ width: '100%', marginTop: 8 }}>
            <Input value={user?.api_key || ''} readOnly size="large" />
            <Button icon={<CopyOutlined />} onClick={handleCopy}>复制</Button>
            <Button type="primary" loading={loading} icon={<ReloadOutlined />} onClick={handleRegenerate}>
              重新生成
            </Button>
          </Space>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">提示：重新生成后旧的 API Key 立即失效。</Text>
          </div>
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
