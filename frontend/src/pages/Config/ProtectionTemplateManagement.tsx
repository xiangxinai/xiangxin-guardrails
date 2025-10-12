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
  Typography,
  Divider,
  Row,
  Col,
  InputNumber,
  Select,
  Alert
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  InfoCircleOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;

interface ProtectionTemplate {
  id: number;
  name: string;
  description?: string;
  tenant_id: string;
  is_default: boolean;
  // Risk type switches
  s1_enabled: boolean;
  s2_enabled: boolean;
  s3_enabled: boolean;
  s4_enabled: boolean;
  s5_enabled: boolean;
  s6_enabled: boolean;
  s7_enabled: boolean;
  s8_enabled: boolean;
  s9_enabled: boolean;
  s10_enabled: boolean;
  s11_enabled: boolean;
  s12_enabled: boolean;
  // Sensitivity thresholds
  high_sensitivity_threshold: number;
  medium_sensitivity_threshold: number;
  low_sensitivity_threshold: number;
  sensitivity_trigger_level: string;
  created_at: string;
  updated_at: string;
}

const ProtectionTemplateManagement: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [templates, setTemplates] = useState<ProtectionTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ProtectionTemplate | null>(null);
  const { onUserSwitch } = useAuth();

  // Risk types definition
  const RISK_TYPES = [
    { key: 's1_enabled', code: 'S1', name: t('config.riskTypes.s1') },
    { key: 's2_enabled', code: 'S2', name: t('config.riskTypes.s2') },
    { key: 's3_enabled', code: 'S3', name: t('config.riskTypes.s3') },
    { key: 's4_enabled', code: 'S4', name: t('config.riskTypes.s4') },
    { key: 's5_enabled', code: 'S5', name: t('config.riskTypes.s5') },
    { key: 's6_enabled', code: 'S6', name: t('config.riskTypes.s6') },
    { key: 's7_enabled', code: 'S7', name: t('config.riskTypes.s7') },
    { key: 's8_enabled', code: 'S8', name: t('config.riskTypes.s8') },
    { key: 's9_enabled', code: 'S9', name: t('config.riskTypes.s9') },
    { key: 's10_enabled', code: 'S10', name: t('config.riskTypes.s10') },
    { key: 's11_enabled', code: 'S11', name: t('config.riskTypes.s11') },
    { key: 's12_enabled', code: 'S12', name: t('config.riskTypes.s12') },
  ];

  useEffect(() => {
    loadTemplates();
  }, []);

  // Listen for user switch events
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      loadTemplates();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/config/risk-configs');
      setTemplates(response.data || []);
    } catch (error: any) {
      message.error(t('protectionTemplate.loadError') || 'Failed to load protection templates');
      console.error('Load templates error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    form.resetFields();
    // Set default values
    form.setFieldsValue({
      name: '',
      is_default: false,
      s1_enabled: true,
      s2_enabled: true,
      s3_enabled: true,
      s4_enabled: true,
      s5_enabled: true,
      s6_enabled: true,
      s7_enabled: true,
      s8_enabled: true,
      s9_enabled: true,
      s10_enabled: true,
      s11_enabled: true,
      s12_enabled: true,
      high_sensitivity_threshold: 0.40,
      medium_sensitivity_threshold: 0.60,
      low_sensitivity_threshold: 0.95,
      sensitivity_trigger_level: 'medium'
    });
    setModalVisible(true);
  };

  const handleEdit = (template: ProtectionTemplate) => {
    setEditingTemplate(template);
    form.setFieldsValue(template);
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingTemplate) {
        // Update existing template
        await api.put(`/api/v1/config/risk-configs/${editingTemplate.id}`, {
          name: values.name,
          ...values
        });
        message.success(t('protectionTemplate.updateSuccess') || 'Template updated successfully');
      } else {
        // Create new template
        await api.post('/api/v1/config/risk-configs', values);
        message.success(t('protectionTemplate.createSuccess') || 'Template created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingTemplate(null);
      loadTemplates();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('protectionTemplate.saveError') ||
        'Failed to save template'
      );
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/api/v1/config/risk-configs/${id}`);
      message.success(t('protectionTemplate.deleteSuccess') || 'Template deleted successfully');
      loadTemplates();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('protectionTemplate.deleteError') ||
        'Failed to delete template'
      );
    }
  };

  const handleClone = async (template: ProtectionTemplate) => {
    try {
      // Use backend clone API
      await api.post(`/api/v1/config/risk-configs/${template.id}/clone`, {
        new_name: `${template.name} (Copy)`
      });
      message.success(t('protectionTemplate.cloneSuccess') || 'Template cloned successfully');
      loadTemplates();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('protectionTemplate.cloneError') ||
        'Failed to clone template'
      );
    }
  };

  const getEnabledRiskCount = (template: ProtectionTemplate): number => {
    return RISK_TYPES.filter(rt => template[rt.key as keyof ProtectionTemplate] === true).length;
  };

  const columns: ColumnsType<ProtectionTemplate> = [
    {
      title: t('protectionTemplate.name'),
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          {record.is_default && (
            <Tag color="blue">{t('protectionTemplate.default')}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: t('protectionTemplate.riskTypes'),
      key: 'risk_types',
      render: (_, record) => (
        <Text>{`${getEnabledRiskCount(record)}/12 ${t('protectionTemplate.enabled')}`}</Text>
      ),
    },
    {
      title: t('protectionTemplate.sensitivity'),
      dataIndex: 'sensitivity_trigger_level',
      key: 'sensitivity',
      render: (level) => {
        const colors: any = { high: 'red', medium: 'orange', low: 'green' };
        return <Tag color={colors[level]}>{t(`sensitivity.${level}`)}</Tag>;
      },
    },
    {
      title: t('protectionTemplate.thresholds'),
      key: 'thresholds',
      render: (_, record) => (
        <Text type="secondary">
          {`H: ${(record.high_sensitivity_threshold * 100).toFixed(0)}% / `}
          {`M: ${(record.medium_sensitivity_threshold * 100).toFixed(0)}% / `}
          {`L: ${(record.low_sensitivity_threshold * 100).toFixed(0)}%`}
        </Text>
      ),
    },
    {
      title: t('common.actions'),
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/config/config-set/${record.id}`)}
          >
            {t('common.view')}
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            {t('common.edit')}
          </Button>
          <Button
            type="link"
            icon={<CopyOutlined />}
            onClick={() => handleClone(record)}
          >
            {t('common.clone')}
          </Button>
          {!record.is_default && (
            <Popconfirm
              title={t('protectionTemplate.deleteConfirm')}
              onConfirm={() => handleDelete(record.id)}
              okText={t('common.yes')}
              cancelText={t('common.no')}
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                {t('common.delete')}
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Alert
        message={t('protectionTemplate.description')}
        description={t('protectionTemplate.hint')}
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: 16 }}
      />

      <Card
        title={<Title level={4}>{t('protectionTemplate.title')}</Title>}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            {t('protectionTemplate.create')}
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={templates}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingTemplate ? t('protectionTemplate.editTitle') : t('protectionTemplate.createTitle')}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingTemplate(null);
        }}
        onOk={() => form.submit()}
        width={800}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label={t('protectionTemplate.name')}
            name="name"
            rules={[{ required: true, message: t('protectionTemplate.nameRequired') }]}
          >
            <Input placeholder={t('protectionTemplate.namePlaceholder')} />
          </Form.Item>

          <Form.Item
            label={t('protectionTemplate.description')}
            name="description"
          >
            <Input.TextArea
              rows={3}
              placeholder={t('protectionTemplate.descriptionPlaceholder') || 'Enter a description for this config set'}
            />
          </Form.Item>

          <Form.Item
            label={t('protectionTemplate.isDefault')}
            name="is_default"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Divider orientation="left">{t('protectionTemplate.riskTypesConfig')}</Divider>

          <Row gutter={16}>
            {RISK_TYPES.map((rt) => (
              <Col span={6} key={rt.key}>
                <Form.Item
                  label={`${rt.code}: ${rt.name}`}
                  name={rt.key}
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            ))}
          </Row>

          <Divider orientation="left">{t('protectionTemplate.sensitivityConfig')}</Divider>

          <Form.Item
            label={t('protectionTemplate.triggerLevel')}
            name="sensitivity_trigger_level"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="high">{t('sensitivity.high')}</Option>
              <Option value="medium">{t('sensitivity.medium')}</Option>
              <Option value="low">{t('sensitivity.low')}</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label={t('protectionTemplate.highThreshold')}
                name="high_sensitivity_threshold"
                rules={[{ required: true }]}
              >
                <InputNumber
                  min={0}
                  max={1}
                  step={0.01}
                  style={{ width: '100%' }}
                  placeholder="0.40"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label={t('protectionTemplate.mediumThreshold')}
                name="medium_sensitivity_threshold"
                rules={[{ required: true }]}
              >
                <InputNumber
                  min={0}
                  max={1}
                  step={0.01}
                  style={{ width: '100%' }}
                  placeholder="0.60"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label={t('protectionTemplate.lowThreshold')}
                name="low_sensitivity_threshold"
                rules={[{ required: true }]}
              >
                <InputNumber
                  min={0}
                  max={1}
                  step={0.01}
                  style={{ width: '100%' }}
                  placeholder="0.95"
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default ProtectionTemplateManagement;
