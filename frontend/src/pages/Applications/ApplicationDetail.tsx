import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Descriptions,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  message,
  Switch,
  Spin,
  Typography,
  Divider,
  Alert,
} from 'antd';
import {
  EditOutlined,
  ArrowLeftOutlined,
  KeyOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { applicationApi } from '../../services/api';
import type { ApplicationDetail, UpdateApplicationRequest } from '../../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

const ApplicationDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (id) {
      fetchApplicationDetail();
    }
  }, [id]);

  const fetchApplicationDetail = async () => {
    if (!id) return;

    setLoading(true);
    try {
      const data = await applicationApi.get(id);
      setApplication(data);
      form.setFieldsValue({
        name: data.name,
        description: data.description,
        is_active: data.is_active,
      });
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('applications.fetchError'));
      navigate('/applications');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateApplication = async (values: UpdateApplicationRequest) => {
    if (!id) return;

    try {
      await applicationApi.update(id, values);
      message.success(t('applications.updateSuccess'));
      setEditModalVisible(false);
      fetchApplicationDetail();
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('applications.updateError'));
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!application) {
    return null;
  }

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/applications')}
            style={{ marginBottom: 16 }}
          >
            {t('common.back')}
          </Button>
          <Card
            title={<Title level={4}>{application.name}</Title>}
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<KeyOutlined />}
                  onClick={() => navigate(`/applications/${id}/api-keys`)}
                >
                  {t('applications.manageApiKeys')}
                </Button>
                <Button
                  icon={<EditOutlined />}
                  onClick={() => setEditModalVisible(true)}
                >
                  {t('common.edit')}
                </Button>
              </Space>
            }
          >
            <Descriptions bordered column={2}>
              <Descriptions.Item label={t('applications.id')} span={2}>
                <Text copyable>{application.id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.name')}>
                {application.name}
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.status')}>
                <Tag color={application.is_active ? 'green' : 'red'}>
                  {application.is_active ? t('common.active') : t('common.inactive')}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.description')} span={2}>
                {application.description || '-'}
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.apiKeyCount')}>
                {application.api_key_count || 0}
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.activeApiKeyCount')}>
                {application.active_api_key_count || 0}
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.createdAt')}>
                {new Date(application.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label={t('applications.updatedAt')}>
                {new Date(application.updated_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </div>

        <Card title={<Title level={5}>{t('applications.configurationSummary')}</Title>}>
          <Alert
            message={t('applications.configInfo')}
            description={t('applications.configInfoDesc')}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Descriptions bordered column={2}>
            <Descriptions.Item label={t('applications.riskTypeConfigs')}>
              {application.risk_type_config_count || 0}
            </Descriptions.Item>
            <Descriptions.Item label={t('applications.blacklistRules')}>
              {application.blacklist_count || 0}
            </Descriptions.Item>
            <Descriptions.Item label={t('applications.whitelistRules')}>
              {application.whitelist_count || 0}
            </Descriptions.Item>
            <Descriptions.Item label={t('applications.responseTemplates')}>
              {application.response_template_count || 0}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </Space>

      {/* Edit Application Modal */}
      <Modal
        title={t('applications.edit')}
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdateApplication}
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
            name="is_active"
            label={t('applications.status')}
            valuePropName="checked"
          >
            <Switch
              checkedChildren={t('common.active')}
              unCheckedChildren={t('common.inactive')}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApplicationDetailPage;
