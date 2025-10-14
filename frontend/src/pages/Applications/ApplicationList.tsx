import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Select,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  KeyOutlined,
  EyeOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { applicationApi, apiKeyApi } from '../../services/api';
import type { Application, CreateApplicationRequest, CreateAPIKeyResponse } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const ApplicationList: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [apiKeyModalVisible, setApiKeyModalVisible] = useState(false);
  const [newApiKey, setNewApiKey] = useState<CreateAPIKeyResponse | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await applicationApi.list();
      setApplications(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('applications.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApplication = async (values: CreateApplicationRequest) => {
    try {
      const response = await applicationApi.create(values);
      message.success(t('applications.createSuccess'));
      setCreateModalVisible(false);
      form.resetFields();

      // Show the first API key
      if (response.first_api_key) {
        setNewApiKey(response.first_api_key);
        setApiKeyModalVisible(true);
      }

      fetchApplications();
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('applications.createError'));
    }
  };

  const handleDeleteApplication = async (id: string) => {
    try {
      await applicationApi.delete(id);
      message.success(t('applications.deleteSuccess'));
      fetchApplications();
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('applications.deleteError'));
    }
  };

  const handleCopyApiKey = () => {
    if (newApiKey?.api_key) {
      navigator.clipboard.writeText(newApiKey.api_key);
      message.success(t('applications.apiKeyCopied'));
    }
  };

  const columns = [
    {
      title: t('applications.name'),
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Application) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          {record.description && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.description}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: t('applications.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? t('common.active') : t('common.inactive')}
        </Tag>
      ),
    },
    {
      title: t('applications.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 250,
      render: (_: any, record: Application) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/applications/${record.id}`)}
          >
            {t('common.view')}
          </Button>
          <Button
            type="link"
            icon={<KeyOutlined />}
            onClick={() => navigate(`/applications/${record.id}/api-keys`)}
          >
            {t('applications.apiKeys')}
          </Button>
          <Popconfirm
            title={t('applications.deleteConfirm')}
            description={t('applications.deleteWarning')}
            onConfirm={() => handleDeleteApplication(record.id)}
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
      <Card
        title={<Title level={4}>{t('applications.title')}</Title>}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            {t('applications.createNew')}
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={applications}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => t('common.totalItems', { total }),
          }}
        />
      </Card>

      {/* Create Application Modal */}
      <Modal
        title={t('applications.createNew')}
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText={t('common.create')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateApplication}
        >
          <Form.Item
            name="name"
            label={t('applications.name')}
            rules={[
              { required: true, message: t('applications.nameRequired') },
              { max: 100, message: t('applications.nameTooLong') },
            ]}
          >
            <Input placeholder={t('applications.namePlaceholder')} />
          </Form.Item>

          <Form.Item
            name="description"
            label={t('applications.description')}
          >
            <TextArea
              rows={3}
              placeholder={t('applications.descriptionPlaceholder')}
            />
          </Form.Item>

          <Form.Item
            name="copy_from_application_id"
            label={t('applications.copyFromApp')}
            tooltip={t('applications.copyFromAppTooltip')}
          >
            <Select
              allowClear
              placeholder={t('applications.copyFromAppPlaceholder')}
              options={applications
                .filter((app) => app.is_active)
                .map((app) => ({
                  label: app.name,
                  value: app.id,
                }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* API Key Display Modal */}
      <Modal
        title={t('applications.firstApiKey')}
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
          message={t('applications.apiKeyWarning')}
          description={t('applications.apiKeyWarningDesc')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Paragraph>
          <Text strong>{t('applications.apiKey')}:</Text>
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

export default ApplicationList;
