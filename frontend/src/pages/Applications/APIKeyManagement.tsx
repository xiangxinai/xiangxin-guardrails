import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Table,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Typography,
  Alert,
  DatePicker,
  Switch,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowLeftOutlined,
  CopyOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTranslation } from 'react-i18next';
import { apiKeyApi, applicationApi } from '../../services/api';
import type { APIKey, CreateAPIKeyRequest, UpdateAPIKeyRequest, CreateAPIKeyResponse } from '../../types';

const { Title, Text, Paragraph } = Typography;

const APIKeyManagement: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [applicationName, setApplicationName] = useState<string>('');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [apiKeyModalVisible, setApiKeyModalVisible] = useState(false);
  const [newApiKey, setNewApiKey] = useState<CreateAPIKeyResponse | null>(null);
  const [editingKey, setEditingKey] = useState<APIKey | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    if (id) {
      fetchApiKeys();
      fetchApplicationInfo();
    }
  }, [id]);

  const fetchApplicationInfo = async () => {
    if (!id) return;
    try {
      const app = await applicationApi.get(id);
      setApplicationName(app.name);
    } catch (error) {
      // Handle silently
    }
  };

  const fetchApiKeys = async () => {
    if (!id) return;

    setLoading(true);
    try {
      const data = await apiKeyApi.list(id);
      setApiKeys(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('apiKeys.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async (values: CreateAPIKeyRequest) => {
    if (!id) return;

    try {
      const response = await apiKeyApi.create(id, {
        ...values,
        expires_at: values.expires_at ? dayjs(values.expires_at).toISOString() : undefined,
      });
      message.success(t('apiKeys.createSuccess'));
      setCreateModalVisible(false);
      createForm.resetFields();

      // Show the new API key
      setNewApiKey(response);
      setApiKeyModalVisible(true);

      fetchApiKeys();
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('apiKeys.createError'));
    }
  };

  const handleUpdateApiKey = async (values: UpdateAPIKeyRequest) => {
    if (!id || !editingKey) return;

    try {
      await apiKeyApi.update(id, editingKey.id, values);
      message.success(t('apiKeys.updateSuccess'));
      setEditModalVisible(false);
      setEditingKey(null);
      editForm.resetFields();
      fetchApiKeys();
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('apiKeys.updateError'));
    }
  };

  const handleDeleteApiKey = async (keyId: string) => {
    if (!id) return;

    try {
      await apiKeyApi.delete(id, keyId);
      message.success(t('apiKeys.deleteSuccess'));
      fetchApiKeys();
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('apiKeys.deleteError'));
    }
  };

  const handleCopyApiKey = () => {
    if (newApiKey?.api_key) {
      navigator.clipboard.writeText(newApiKey.api_key);
      message.success(t('apiKeys.apiKeyCopied'));
    }
  };

  const handleEdit = (record: APIKey) => {
    setEditingKey(record);
    editForm.setFieldsValue({
      name: record.name,
      is_active: record.is_active,
    });
    setEditModalVisible(true);
  };

  const columns = [
    {
      title: t('apiKeys.name'),
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: APIKey) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text || t('apiKeys.unnamed')}</Text>
          <Text type="secondary" style={{ fontSize: '12px', fontFamily: 'monospace' }}>
            {record.key_prefix}...
          </Text>
        </Space>
      ),
    },
    {
      title: t('apiKeys.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean, record: APIKey) => {
        const isExpired = record.expires_at && new Date(record.expires_at) < new Date();
        if (isExpired) {
          return <Tag color="default">{t('apiKeys.expired')}</Tag>;
        }
        return (
          <Tag color={isActive ? 'green' : 'red'}>
            {isActive ? t('common.active') : t('common.inactive')}
          </Tag>
        );
      },
    },
    {
      title: t('apiKeys.lastUsed'),
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 180,
      render: (date: string) => (date ? new Date(date).toLocaleString() : t('apiKeys.neverUsed')),
    },
    {
      title: t('apiKeys.expiresAt'),
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: 180,
      render: (date: string) => (date ? new Date(date).toLocaleString() : t('apiKeys.noExpiration')),
    },
    {
      title: t('apiKeys.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 150,
      render: (_: any, record: APIKey) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            {t('common.edit')}
          </Button>
          <Popconfirm
            title={t('apiKeys.deleteConfirm')}
            description={t('apiKeys.deleteWarning')}
            onConfirm={() => handleDeleteApiKey(record.id)}
            okText={t('common.confirm')}
            cancelText={t('common.cancel')}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              {t('common.delete')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(`/applications/${id}`)}
        style={{ marginBottom: 16 }}
      >
        {t('common.back')}
      </Button>

      <Card
        title={
          <Title level={4}>
            {t('apiKeys.title')} - {applicationName}
          </Title>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            {t('apiKeys.createNew')}
          </Button>
        }
      >
        <Alert
          message={t('apiKeys.info')}
          description={t('apiKeys.infoDesc')}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={columns}
          dataSource={apiKeys}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => t('common.totalItems', { total }),
          }}
        />
      </Card>

      {/* Create API Key Modal */}
      <Modal
        title={t('apiKeys.createNew')}
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        onOk={() => createForm.submit()}
        okText={t('common.create')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateApiKey}
        >
          <Form.Item
            name="name"
            label={t('apiKeys.name')}
            rules={[{ max: 100, message: t('apiKeys.nameTooLong') }]}
          >
            <Input placeholder={t('apiKeys.namePlaceholder')} />
          </Form.Item>

          <Form.Item
            name="expires_at"
            label={
              <Space>
                {t('apiKeys.expiresAt')}
                <Tooltip title={t('apiKeys.expiresAtTooltip')}>
                  <InfoCircleOutlined />
                </Tooltip>
              </Space>
            }
          >
            <DatePicker
              showTime
              format="YYYY-MM-DD HH:mm:ss"
              style={{ width: '100%' }}
              disabledDate={(current) => current && current < dayjs().startOf('day')}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit API Key Modal */}
      <Modal
        title={t('apiKeys.edit')}
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingKey(null);
          editForm.resetFields();
        }}
        onOk={() => editForm.submit()}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateApiKey}
        >
          <Form.Item
            name="name"
            label={t('apiKeys.name')}
            rules={[{ max: 100, message: t('apiKeys.nameTooLong') }]}
          >
            <Input placeholder={t('apiKeys.namePlaceholder')} />
          </Form.Item>

          <Form.Item
            name="is_active"
            label={t('apiKeys.status')}
            valuePropName="checked"
          >
            <Switch
              checkedChildren={t('common.active')}
              unCheckedChildren={t('common.inactive')}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* API Key Display Modal */}
      <Modal
        title={t('apiKeys.newApiKey')}
        open={apiKeyModalVisible}
        onCancel={() => {
          setApiKeyModalVisible(false);
          setNewApiKey(null);
        }}
        footer={[
          <Button
            key="copy"
            type="primary"
            icon={<CopyOutlined />}
            onClick={handleCopyApiKey}
          >
            {t('common.copy')}
          </Button>,
          <Button
            key="close"
            onClick={() => {
              setApiKeyModalVisible(false);
              setNewApiKey(null);
            }}
          >
            {t('common.close')}
          </Button>,
        ]}
      >
        <Alert
          message={t('apiKeys.apiKeyWarning')}
          description={t('apiKeys.apiKeyWarningDesc')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Paragraph>
          <Text strong>{t('apiKeys.apiKey')}:</Text>
        </Paragraph>
        <Input.TextArea
          value={newApiKey?.api_key}
          readOnly
          autoSize={{ minRows: 3, maxRows: 3 }}
          style={{ fontFamily: 'monospace' }}
        />
      </Modal>
    </div>
  );
};

export default APIKeyManagement;
