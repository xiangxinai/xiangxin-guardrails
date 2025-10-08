import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Space,
  Tag,
  Popconfirm,
  Tooltip,
  Card,
  Typography,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, GlobalOutlined, UserOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { dataSecurityApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const { Option } = Select;
const { TextArea } = Input;
const { Text } = Typography;

interface EntityType {
  id: string;
  entity_type: string;
  display_name: string;
  risk_level: string;
  pattern: string;
  anonymization_method: string;
  anonymization_config: any;
  check_input: boolean;
  check_output: boolean;
  is_active: boolean;
  is_global: boolean;
  created_at: string;
  updated_at: string;
}

const EntityTypeManagement: React.FC = () => {
  const { t } = useTranslation();
  
  const RISK_LEVELS = [
    { value: '低', label: t('entityType.lowRisk'), color: 'green' },
    { value: '中', label: t('entityType.mediumRisk'), color: 'orange' },
    { value: '高', label: t('entityType.highRisk'), color: 'red' },
  ];

  const ANONYMIZATION_METHODS = [
    { value: 'replace', label: t('entityType.replace') },
    { value: 'mask', label: t('entityType.mask') },
    { value: 'hash', label: t('entityType.hash') },
    { value: 'encrypt', label: t('entityType.encrypt') },
    { value: 'shuffle', label: t('entityType.shuffle') },
    { value: 'random', label: t('entityType.randomReplace') },
  ];
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEntity, setEditingEntity] = useState<EntityType | null>(null);
  const [searchText, setSearchText] = useState('');
  const [riskLevelFilter, setRiskLevelFilter] = useState<string | undefined>(undefined);
  const [form] = Form.useForm();
  const { user } = useAuth();

  useEffect(() => {
    loadEntityTypes();
  }, []);

  const loadEntityTypes = async () => {
    setLoading(true);
    try {
      const response = await dataSecurityApi.getEntityTypes();
      setEntityTypes(response.items || []);
    } catch (error) {
      message.error(t('entityType.loadEntityTypesFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingEntity(null);
    form.resetFields();
    form.setFieldsValue({
      is_active: true,
      check_input: true,
      check_output: true,
      anonymization_method: 'replace',
      is_global: false, // Default to custom configuration
    });
    setModalVisible(true);
  };

  const handleEdit = (record: EntityType) => {
    setEditingEntity(record);
    form.setFieldsValue({
      ...record,
      anonymization_config_text: JSON.stringify(record.anonymization_config || {}, null, 2),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await dataSecurityApi.deleteEntityType(id);
      message.success(t('common.deleteSuccess'));
      loadEntityTypes();
    } catch (error) {
      message.error(t('common.deleteFailed'));
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      // Parse JSON config
      let anonymization_config = {};

      try {
        anonymization_config = JSON.parse(values.anonymization_config_text || '{}');
      } catch (e) {
        message.error(t('entityType.invalidJsonConfig'));
        return;
      }

      const data = {
        entity_type: values.entity_type,
        display_name: values.display_name,
        risk_level: values.risk_level,
        pattern: values.pattern,
        anonymization_method: values.anonymization_method,
        anonymization_config,
        check_input: values.check_input !== undefined ? values.check_input : true,
        check_output: values.check_output !== undefined ? values.check_output : true,
        is_active: values.is_active !== undefined ? values.is_active : true,
      };

      if (editingEntity) {
        await dataSecurityApi.updateEntityType(editingEntity.id, data);
        message.success(t('common.updateSuccess'));
      } else {
        // Determine which API to call based on is_global field
        if (values.is_global && user?.is_super_admin) {
          await dataSecurityApi.createGlobalEntityType(data);
          message.success(t('entityType.createGlobalSuccess'));
        } else {
          await dataSecurityApi.createEntityType(data);
          message.success(t('common.createSuccess'));
        }
      }

      setModalVisible(false);
      loadEntityTypes();
    } catch (error) {
      console.error('Submit error:', error);
    }
  };

  const columns = [
    {
      title: t('entityType.entityTypeColumn'),
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 150,
    },
    {
      title: t('entityType.displayNameColumn'),
      dataIndex: 'display_name',
      key: 'display_name',
      width: 120,
    },
    {
      title: t('entityType.riskLevelColumn'),
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 100,
      render: (risk_level: string) => {
        const level = RISK_LEVELS.find((l) => l.value === risk_level);
        return <Tag color={level?.color}>{level?.label || risk_level}</Tag>;
      },
    },
    {
      title: t('entityType.recognitionRulesColumn'),
      dataIndex: 'pattern',
      key: 'pattern',
      width: 200,
      ellipsis: true,
      render: (pattern: string) => (
        <Tooltip title={pattern}>
          <code style={{ fontSize: '12px' }}>{pattern}</code>
        </Tooltip>
      ),
    },
    {
      title: t('entityType.desensitizationMethodColumn'),
      dataIndex: 'anonymization_method',
      key: 'anonymization_method',
      width: 100,
      render: (method: string) => {
        const m = ANONYMIZATION_METHODS.find((a) => a.value === method);
        return m?.label;
      },
    },
    {
      title: t('entityType.detectionScopeColumn'),
      key: 'check_scope',
      width: 100,
      render: (_: any, record: EntityType) => (
        <Space size={4}>
          {record.check_input && <Tag color="blue" style={{ margin: 0 }}>{t('entityType.input')}</Tag>}
          {record.check_output && <Tag color="green" style={{ margin: 0 }}>{t('entityType.output')}</Tag>}
        </Space>
      ),
    },
    {
      title: t('entityType.statusColumn'),
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (is_active: boolean) => (
        <Tag color={is_active ? 'green' : 'default'}>{is_active ? t('common.enabled') : t('common.disabled')}</Tag>
      ),
    },
    {
      title: t('entityType.sourceColumn'),
      dataIndex: 'is_global',
      key: 'is_global',
      width: 80,
      render: (is_global: boolean) => (
        <Tag icon={is_global ? <GlobalOutlined /> : <UserOutlined />} color={is_global ? 'blue' : 'default'}>
          {is_global ? t('entityType.system') : t('entityType.custom')}
        </Tag>
      ),
    },
    {
      title: t('entityType.operationColumn'),
      key: 'action',
      width: 120,
      render: (_: any, record: EntityType) => (
        <Space size="small">
          <Tooltip title={t('common.edit')}>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              disabled={record.is_global && !user?.is_super_admin}
            />
          </Tooltip>
          <Popconfirm title={t('common.confirmDelete')} onConfirm={() => handleDelete(record.id)}>
            <Tooltip title={t('common.delete')}>
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_global && !user?.is_super_admin}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Filter data
  const filteredEntityTypes = entityTypes.filter(item => {
    const matchesSearch = !searchText ||
      item.entity_type.toLowerCase().includes(searchText.toLowerCase()) ||
      item.display_name.toLowerCase().includes(searchText.toLowerCase()) ||
      item.pattern.toLowerCase().includes(searchText.toLowerCase());

    const matchesRiskLevel = !riskLevelFilter || item.risk_level === riskLevelFilter;

    return matchesSearch && matchesRiskLevel;
  });

  return (
    <div>
      <Card
        title={t('entityType.entityTypeConfig')}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            {t('entityType.addEntityTypeConfig')}
          </Button>
        }
        bordered={false}
      >
        <Space style={{ marginBottom: 16, width: '100%' }} direction="vertical">
          <Space>
            <Input.Search
              placeholder={t('entityType.searchPlaceholder')}
              allowClear
              style={{ width: 300 }}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <Select
              placeholder={t('entityType.filterRiskLevel')}
              allowClear
              style={{ width: 150 }}
              onChange={(value) => setRiskLevelFilter(value)}
            >
              {RISK_LEVELS.map((level) => (
                <Option key={level.value} value={level.value}>
                  {level.label}
                </Option>
              ))}
            </Select>
          </Space>
        </Space>

        <Table
          columns={columns}
          dataSource={filteredEntityTypes}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => t('banPolicy.totalRecords', { total }),
          }}
        />
      </Card>

      <Modal
        title={editingEntity ? t('entityType.editEntityType') : t('entityType.addEntityType')}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        okText={t('common.confirm')}
        cancelText={t('common.cancel')}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="entity_type"
            label="Entity type code"
            rules={[{ required: true, message: 'Please enter entity type code' }]}
          >
            <Input placeholder="E.g. ID_CARD_NUMBER, PHONE_NUMBER, EMAIL" disabled={!!editingEntity} />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="Display name"
            rules={[{ required: true, message: 'Please enter display name' }]}
          >
            <Input placeholder="E.g. ID Card Number, Phone Number, Email" />
          </Form.Item>

          <Form.Item name="risk_level" label="Risk level" rules={[{ required: true, message: 'Please select risk level' }]}>
            <Select placeholder="Please select risk level">
              {RISK_LEVELS.map((level) => (
                <Option key={level.value} value={level.value}>
                  {level.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="pattern"
            label="Recognition rule (regex)"
            rules={[{ required: true, message: 'Please enter regex' }]}
            tooltip="Use regex to define the recognition rule for sensitive data"
          >
            <TextArea
              rows={3}
              placeholder='E.g. 1[3-9]\d{9} (Phone Number)'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item
            name="anonymization_method"
            label="Anonymization method"
            rules={[{ required: true, message: 'Please select anonymization method' }]}
          >
            <Select placeholder="Please select anonymization method">
              {ANONYMIZATION_METHODS.map((method) => (
                <Option key={method.value} value={method.value}>
                  {method.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="anonymization_config_text"
            label="Anonymization config (JSON)"
          >
            <TextArea
              rows={4}
              placeholder='E.g. {"mask_char": "*", "keep_prefix": 3, "keep_suffix": 4}'
              style={{ fontFamily: 'monospace' }}
            />
            <Card size="small" style={{ marginTop: 8, backgroundColor: '#f5f5f5' }}>
              <Text strong style={{ fontSize: 12 }}>Anonymization method config description:</Text>
              <ul style={{ margin: '8px 0', paddingLeft: 20, fontSize: 11 }}>
                <li><Text code>replace</Text> - Replace with placeholder
                  <br /><Text type="secondary">{"{"}"replacement": "&lt;PHONE_NUMBER&gt;"{"}"}  → 13912345678 变为 &lt;PHONE_NUMBER&gt;</Text>
                </li>
                <li><Text code>mask</Text> - Partial masking display
                  <br /><Text type="secondary">{"{"}"mask_char": "*", "keep_prefix": 3, "keep_suffix": 4{"}"}</Text>
                  <br /><Text type="secondary">→ 13912345678 becomes 139****5678</Text>
                </li>
                <li><Text code>hash</Text> - SHA256 hash (no config)
                  <br /><Text type="secondary">{"{}"} → 13912345678 becomes sha256_abc123...</Text>
                </li>
                <li><Text code>encrypt</Text> - Encryption (no config)
                  <br /><Text type="secondary">{"{}"} → 13912345678 becomes &lt;ENCRYPTED_a1b2c3d4&gt;</Text>
                </li>
                <li><Text code>shuffle</Text> - Character reordering (no config)
                  <br /><Text type="secondary">{"{}"} → 13912345678 becomes 87654321913</Text>
                </li>
                <li><Text code>random</Text> - Random character replacement (no config)
                  <br /><Text type="secondary">{"{}"} → 13912345678 becomes 48273569102</Text>
                </li>
              </ul>
            </Card>
          </Form.Item>

          <Form.Item label="Detection scope">
            <Space>
              <Form.Item name="check_input" valuePropName="checked" noStyle>
                <Switch checkedChildren="Input" unCheckedChildren="Input" />
              </Form.Item>
              <Form.Item name="check_output" valuePropName="checked" noStyle>
                <Switch checkedChildren="Output" unCheckedChildren="Output" />
              </Form.Item>
            </Space>
          </Form.Item>

          <Form.Item name="is_active" label="Enable status" valuePropName="checked">
            <Switch />
          </Form.Item>

          {user?.is_super_admin && (
            <Form.Item
              name="is_global"
              label={
                <span>
                  System configuration
                  <Tooltip title="System configuration will take effect for all users, only administrators can set and modify">
                    <InfoCircleOutlined style={{ marginLeft: 4 }} />
                  </Tooltip>
                </span>
              }
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default EntityTypeManagement;
