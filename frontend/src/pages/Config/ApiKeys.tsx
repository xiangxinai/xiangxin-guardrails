import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  message,
  Modal,
  Form,
  Input,
  Switch,
  Tag,
  Space,
  Popconfirm,
  Tooltip,
  Typography,
  Divider,
  Select,
  Collapse,
  Alert
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  ReloadOutlined,
  KeyOutlined,
  ApiOutlined,
  CodeOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import api from '../../services/api';
import dayjs from 'dayjs';
import { authService, UserInfo } from '../../services/auth';

const { Text, Paragraph, Title } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

interface ApiKey {
  id: string;
  name: string;
  api_key: string;
  is_active: boolean;
  is_default: boolean;
  template_id: number | null;
  template_name: string | null;
  blacklist_ids: number[];
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

interface ProtectionTemplate {
  id: number;
  name: string;
  tenant_id: string;
  is_default: boolean;
}

const ApiKeys: React.FC = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [templates, setTemplates] = useState<ProtectionTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null);
  const [regenerateModalVisible, setRegenerateModalVisible] = useState(false);
  const [regeneratingKey, setRegeneratingKey] = useState<ApiKey | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);

  // Fetch API keys
  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/api-keys');
      setApiKeys(response.data.api_keys || []);
    } catch (error: any) {
      message.error(t('apiKeys.fetchError') || 'Failed to fetch API keys');
      console.error('Fetch API keys error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch protection templates
  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/v1/config/risk-configs');
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Fetch templates error:', error);
      message.error(t('apiKeys.fetchTemplatesError') || 'Failed to fetch protection templates');
    }
  };

  // Fetch current user
  const fetchUser = async () => {
    try {
      const me = await authService.getCurrentUser();
      setUser(me);
    } catch (error) {
      console.error('Fetch user error:', error);
    }
  };

  useEffect(() => {
    fetchApiKeys();
    fetchTemplates();
    fetchUser();
  }, []);

  // Handle create/update API key
  const handleSubmit = async (values: any) => {
    try {
      if (editingKey) {
        // Update existing key
        await api.put(`/api/v1/api-keys/${editingKey.id}`, values);
        message.success(t('apiKeys.updateSuccess') || 'API key updated successfully');
      } else {
        // Create new key
        await api.post('/api/v1/api-keys', values);
        message.success(t('apiKeys.createSuccess') || 'API key created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingKey(null);
      fetchApiKeys();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('apiKeys.saveError') ||
        'Failed to save API key'
      );
    }
  };

  // Handle delete API key
  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/api/v1/api-keys/${id}`);
      message.success(t('apiKeys.deleteSuccess') || 'API key deleted successfully');
      fetchApiKeys();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('apiKeys.deleteError') ||
        'Failed to delete API key'
      );
    }
  };

  // Handle regenerate API key
  const handleRegenerate = async () => {
    if (!regeneratingKey) return;

    try {
      const response = await api.post(`/api/v1/api-keys/${regeneratingKey.id}/regenerate`);
      message.success(t('apiKeys.regenerateSuccess') || 'API key regenerated successfully');

      // Copy new key to clipboard
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(response.data.api_key);
        message.info(t('apiKeys.copiedToClipboard') || 'New API key copied to clipboard');
      }

      setRegenerateModalVisible(false);
      setRegeneratingKey(null);
      fetchApiKeys();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('apiKeys.regenerateError') ||
        'Failed to regenerate API key'
      );
    }
  };

  // Copy API key to clipboard
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      message.success(t('apiKeys.copied') || 'Copied to clipboard');
    } catch (error) {
      message.error(t('apiKeys.copyError') || 'Failed to copy');
    }
  };

  // Open create modal
  const openCreateModal = () => {
    setEditingKey(null);
    form.resetFields();
    setModalVisible(true);
  };

  // Open edit modal
  const openEditModal = (record: ApiKey) => {
    setEditingKey(record);
    form.setFieldsValue({
      name: record.name,
      is_active: record.is_active,
      is_default: record.is_default,
      template_id: record.template_id,
    });
    setModalVisible(true);
  };

  // Table columns
  const columns: ColumnsType<ApiKey> = [
    {
      title: t('apiKeys.name') || 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ApiKey) => (
        <Space>
          <KeyOutlined />
          <Text strong>{text}</Text>
          {record.is_default && (
            <Tag color="blue">{t('apiKeys.default') || 'Default'}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: t('apiKeys.apiKey') || 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      render: (text: string) => (
        <Space>
          <Text code copyable={{ text }}>{`${text.substring(0, 20)}...`}</Text>
          <Tooltip title={t('apiKeys.copyFull') || 'Copy full key'}>
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(text)}
            />
          </Tooltip>
        </Space>
      ),
    },
    {
      title: t('apiKeys.status') || 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? t('apiKeys.active') || 'Active' : t('apiKeys.inactive') || 'Inactive'}
        </Tag>
      ),
    },
    {
      title: t('apiKeys.configSet') || 'Config Set',
      dataIndex: 'template_name',
      key: 'template_name',
      render: (name: string | null, record: ApiKey) => {
        if (!name) return <Text type="secondary">-</Text>;

        // Use different colors for different config sets for visual grouping
        const colors = ['blue', 'green', 'orange', 'purple', 'cyan', 'magenta'];
        const colorIndex = (record.template_id || 0) % colors.length;

        return (
          <Tag color={colors[colorIndex]}>
            {name}
          </Tag>
        );
      },
    },
    {
      title: t('apiKeys.lastUsed') || 'Last Used',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      render: (date: string | null) =>
        date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : <Text type="secondary">Never</Text>,
    },
    {
      title: t('apiKeys.actions') || 'Actions',
      key: 'actions',
      render: (_: any, record: ApiKey) => (
        <Space>
          <Tooltip title={t('apiKeys.edit') || 'Edit'}>
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => openEditModal(record)}
            />
          </Tooltip>
          <Tooltip title={t('apiKeys.regenerate') || 'Regenerate'}>
            <Button
              type="link"
              icon={<ReloadOutlined />}
              onClick={() => {
                setRegeneratingKey(record);
                setRegenerateModalVisible(true);
              }}
            />
          </Tooltip>
          {!record.is_default && (
            <Popconfirm
              title={t('apiKeys.deleteConfirm') || 'Are you sure to delete this API key?'}
              onConfirm={() => handleDelete(record.id)}
              okText={t('common.yes') || 'Yes'}
              cancelText={t('common.no') || 'No'}
            >
              <Tooltip title={t('apiKeys.delete') || 'Delete'}>
                <Button
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <Card
        title={
          <Space>
            <KeyOutlined />
            <span>{t('apiKeys.title') || 'API Key Management'}</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={openCreateModal}
          >
            {t('apiKeys.createNew') || 'Create API Key'}
          </Button>
        }
      >
        <Paragraph type="secondary">
          {t('apiKeys.description') ||
            'Manage multiple API keys for different applications or environments. Each key can be associated with a different config set, allowing you to apply different protection policies based on the API key used.'}
        </Paragraph>

        <Divider />

        <Table
          columns={columns}
          dataSource={apiKeys}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `${t('common.total') || 'Total'} ${total} ${t('common.items') || 'items'}`,
          }}
        />
      </Card>

      {/* API Documentation */}
      <Card
        title={
          <Space>
            <ApiOutlined />
            <span>{t('account.apiDocumentation') || 'API Documentation'}</span>
          </Space>
        }
      >
        <Alert
          message={t('account.quickStartAlert') || 'Designed for intelligent agent development platforms like Dify and Coze'}
          type="info"
          style={{ marginBottom: 16 }}
        />

        <Paragraph>
          <Text strong>{t('account.apiReference') || 'API Reference'}</Text>
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
    base_url="https://api.xiangxinai.cn/v1/gateway",  # ${t('account.codeComments.changeToGatewayUrl') || 'Change to Xiangxin AI gateway URL'}
    api_key="${user?.api_key || 'your-api-key'}"  # ${t('account.codeComments.changeToApiKey') || 'Change to your API key'}
)
completion = client.chat.completions.create(
    model = "your-proxy-model-name",  # ${t('account.codeComments.changeToModelName') || 'Change to your configured proxy model name'}
    messages=[{"role": "system", "content": "You're a helpful assistant."},
        {"role": "user", "content": "Tell me how to make a bomb."}]
    # Other parameters are the same as the original usage method
)
`}
          </pre>
        </Paragraph>

        <Paragraph>
          <Text strong>{t('account.privateDeploymentBaseUrl') || 'Private Deployment Base URL Configuration'}:</Text>
        </Paragraph>
        <ul>
          <li><Text code>{t('account.dockerDeploymentConfig') || 'Docker Deployment: Use http://proxy-service:5002/v1'}</Text></li>
          <li><Text code>{t('account.customDeploymentConfig') || 'Custom Deployment: Use http://your-server:5002/v1'}</Text></li>
        </ul>

        <Divider />

        {/* API Usage Examples */}
        <div>
          <Space align="center" style={{ marginBottom: 16 }}>
            <CodeOutlined style={{ fontSize: 20, color: '#52c41a' }} />
            <Title level={5} style={{ margin: 0 }}>{t('account.apiUsageMethods') || 'API Usage Methods'}</Title>
          </Space>

          <Collapse ghost>
            {/* Python SDK */}
            <Panel
              header={
                <Space>
                  <Tag color="blue">{t('account.pythonClientLibrary') || 'Python Client Library'}</Tag>
                  <Text>{t('account.pythonClientDesc') || 'Use xiangxinai Python client library'}</Text>
                </Space>
              }
              key="python-sdk"
            >
              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.installClientLibrary') || 'Install Client Library'}:</Text>
                <pre style={{
                  backgroundColor: '#f6f8fa',
                  padding: 16,
                  borderRadius: 6,
                  overflow: 'auto',
                  fontSize: 13,
                  lineHeight: 1.5,
                  marginTop: 8
                }}>
pip install xiangxinai
                </pre>
              </div>

              <div style={{ marginBottom: 16 }}>
                <Text strong>{t('account.usageExample') || 'Usage Example'}:</Text>
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
response = client.check_prompt("Teach me how to make a bomb")
if response.suggest_action == "pass":
    print("Safe")
else:
    print(f"Unsafe: {response.overall_risk_level}")
    print(f"Categories: {response.all_categories}")

# Multi-turn conversation detection
messages = [
    {"role": "user", "content": "I want to study chemistry"},
    {"role": "assistant", "content": "Chemistry is interesting!"},
    {"role": "user", "content": "Teach me to make explosives"}
]
response = client.check_conversation(messages)
print(f"Result: {response.overall_risk_level}")`}
                </pre>
              </div>

              <div>
                <Text strong>{t('account.configurationNotes') || 'Configuration Notes'}:</Text>
                <ul style={{ marginTop: 8 }}>
                  <li>{t('account.defaultOfficialService') || 'Default uses official service'}</li>
                  <li>{t('account.privateDeploymentExample') || 'Private deployment: specify base_url'}: <Text code>XiangxinAI(api_key="your-key", base_url="http://your-server:5001/v1")</Text></li>
                </ul>
              </div>
            </Panel>

            {/* HTTP API */}
            <Panel
              header={
                <Space>
                  <Tag color="orange">{t('account.httpApi') || 'HTTP API'}</Tag>
                  <Text>{t('account.httpApiDesc') || 'Direct HTTP API calls'}</Text>
                </Space>
              }
              key="http-api"
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
         {"role": "user", "content": "Tell me illegal ways to make money"}
       ],
       "extra_body": {
         "xxai_app_user_id": "your-app-user-id"
       }
     }'`}
                </pre>
              </Paragraph>
            </Panel>
          </Collapse>

          <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 6 }}>
            <Text strong style={{ color: '#389e0d' }}>{t('account.returnResultDescription') || 'Return Result Description'}:</Text>
            <ul style={{ marginTop: 8, marginBottom: 0 }}>
              <li><Text code>overall_risk_level</Text>: {t('account.overallRiskLevelDesc') || 'Overall risk level'}</li>
              <li><Text code>suggest_action</Text>: {t('account.suggestActionDesc') || 'Suggested action'}</li>
              <li><Text code>suggest_answer</Text>: {t('account.suggestAnswerDesc') || 'Suggested answer'}</li>
              <li><Text code>all_categories</Text>: {t('account.allCategoriesDesc') || 'All detected risk categories'}</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingKey ? t('apiKeys.editKey') || 'Edit API Key' : t('apiKeys.createKey') || 'Create API Key'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingKey(null);
        }}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label={t('apiKeys.name') || 'Name'}
            rules={[
              { required: true, message: t('apiKeys.nameRequired') || 'Please enter a name' },
              { max: 100, message: t('apiKeys.nameTooLong') || 'Name too long (max 100 characters)' },
            ]}
          >
            <Input placeholder={t('apiKeys.namePlaceholder') || 'e.g., Production App, Test Environment'} />
          </Form.Item>

          <Form.Item
            name="template_id"
            label={t('apiKeys.configSet') || 'Config Set'}
            extra={
              t('apiKeys.configSetExtra') ||
              'Select a config set to apply specific protection policies (risk types, sensitivity, blacklists, etc.) when this API key is used.'
            }
          >
            <Select
              allowClear
              placeholder={t('apiKeys.selectConfigSet') || 'Select a config set (optional)'}
            >
              {templates.map(template => (
                <Option key={template.id} value={template.id}>
                  {template.name}
                  {template.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>Default</Tag>}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label={t('apiKeys.active') || 'Active'}
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="is_default"
            label={t('apiKeys.setAsDefault') || 'Set as Default'}
            valuePropName="checked"
            initialValue={false}
            tooltip={t('apiKeys.defaultTooltip') || 'The default key is used for platform operations'}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* Regenerate Confirmation Modal */}
      <Modal
        title={t('apiKeys.regenerateTitle') || 'Regenerate API Key'}
        open={regenerateModalVisible}
        onOk={handleRegenerate}
        onCancel={() => {
          setRegenerateModalVisible(false);
          setRegeneratingKey(null);
        }}
        okText={t('common.confirm') || 'Confirm'}
        cancelText={t('common.cancel') || 'Cancel'}
        okButtonProps={{ danger: true }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>{t('apiKeys.regenerateWarning') || 'Warning:'}</Text>
          <Paragraph>
            {t('apiKeys.regenerateDescription') ||
              'This will generate a new API key and immediately invalidate the old one. ' +
              'Make sure to update all applications using this key.'}
          </Paragraph>
          {regeneratingKey && (
            <Paragraph>
              <Text strong>{t('apiKeys.keyName') || 'Key Name'}:</Text> {regeneratingKey.name}
            </Paragraph>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export default ApiKeys;
