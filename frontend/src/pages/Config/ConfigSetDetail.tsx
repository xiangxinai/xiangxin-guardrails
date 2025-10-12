import React, { useState, useEffect } from 'react';
import {
  Card,
  Collapse,
  Descriptions,
  Tag,
  Table,
  message,
  Spin,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Modal,
  Transfer,
  Checkbox,
} from 'antd';
import type { TransferDirection } from 'antd/es/transfer';
import {
  SettingOutlined,
  SafetyOutlined,
  LockOutlined,
  StopOutlined,
  FileTextOutlined,
  BookOutlined,
  KeyOutlined,
  PlusOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../services/api';

const { Panel } = Collapse;
const { Title, Text } = Typography;

interface ConfigSet {
  id: number;
  name: string;
  description?: string;
  tenant_id: string;
  is_default: boolean;
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
  high_sensitivity_threshold: number;
  medium_sensitivity_threshold: number;
  low_sensitivity_threshold: number;
  sensitivity_trigger_level: string;
}

interface Associations {
  blacklists: Array<{ id: number; name: string; is_active: boolean }>;
  whitelists: Array<{ id: number; name: string; is_active: boolean }>;
  response_templates: Array<{ id: number; category: string; is_active: boolean }>;
  knowledge_bases: Array<{ id: number; name: string; is_active: boolean }>;
  data_security_entities: Array<{ id: string; entity_type: string; is_active: boolean }>;
  ban_policies: Array<{ id: string; enabled: boolean }>;
  api_keys: Array<{ id: string; name: string; is_active: boolean }>;
}

const ConfigSetDetail: React.FC = () => {
  const { configId } = useParams<{ configId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [configSet, setConfigSet] = useState<ConfigSet | null>(null);
  const [associations, setAssociations] = useState<Associations | null>(null);

  // Management modal states
  const [manageModalVisible, setManageModalVisible] = useState(false);
  const [managingType, setManagingType] = useState<string>('');
  const [availableItems, setAvailableItems] = useState<any[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [transferLoading, setTransferLoading] = useState(false);

  useEffect(() => {
    if (configId) {
      loadConfigSet();
      loadAssociations();
    }
  }, [configId]);

  const loadConfigSet = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/config/risk-configs/${configId}`);
      setConfigSet(response.data);
    } catch (error: any) {
      message.error(t('configSet.loadError') || 'Failed to load config set');
      console.error('Load config set error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAssociations = async () => {
    try {
      const response = await api.get(`/api/v1/config/risk-configs/${configId}/associations`);
      setAssociations(response.data);
    } catch (error: any) {
      message.error(t('configSet.loadAssociationsError') || 'Failed to load associations');
      console.error('Load associations error:', error);
    }
  };

  const getRiskTypesList = () => {
    if (!configSet) return [];
    const riskTypes = [
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

    return riskTypes.filter(rt => configSet[rt.key as keyof ConfigSet] === true);
  };

  // Open management modal for a specific type
  const openManageModal = async (type: string) => {
    setManagingType(type);
    setTransferLoading(true);
    setManageModalVisible(true);

    try {
      let endpoint = '';
      let currentIds: (string | number)[] = [];

      switch (type) {
        case 'blacklist':
          endpoint = '/api/v1/config/blacklists';
          currentIds = (associations?.blacklists || []).map(item => item.id);
          break;
        case 'whitelist':
          endpoint = '/api/v1/config/whitelists';
          currentIds = (associations?.whitelists || []).map(item => item.id);
          break;
        case 'response_template':
          endpoint = '/api/v1/config/response-templates';
          currentIds = (associations?.response_templates || []).map(item => item.id);
          break;
        case 'knowledge_base':
          endpoint = '/api/v1/config/knowledge-bases';
          currentIds = (associations?.knowledge_bases || []).map(item => item.id);
          break;
        case 'data_security':
          endpoint = '/api/v1/config/data-security-entities';
          currentIds = (associations?.data_security_entities || []).map(item => item.id);
          break;
        default:
          return;
      }

      const response = await api.get(endpoint);
      setAvailableItems(response.data || []);
      setSelectedKeys(currentIds.map(String));
    } catch (error: any) {
      message.error(t('configSet.loadItemsError') || 'Failed to load items');
      console.error('Load items error:', error);
    } finally {
      setTransferLoading(false);
    }
  };

  // Save associations
  const handleSaveAssociations = async () => {
    setTransferLoading(true);
    try {
      let endpoint = '';
      let payload: any = {};

      switch (managingType) {
        case 'blacklist':
          endpoint = `/api/v1/config/risk-configs/${configId}/blacklists`;
          payload = { blacklist_ids: selectedKeys.map(Number) };
          break;
        case 'whitelist':
          endpoint = `/api/v1/config/risk-configs/${configId}/whitelists`;
          payload = { whitelist_ids: selectedKeys.map(Number) };
          break;
        case 'response_template':
          endpoint = `/api/v1/config/risk-configs/${configId}/response-templates`;
          payload = { template_ids: selectedKeys.map(Number) };
          break;
        case 'knowledge_base':
          endpoint = `/api/v1/config/risk-configs/${configId}/knowledge-bases`;
          payload = { knowledge_base_ids: selectedKeys.map(Number) };
          break;
        case 'data_security':
          endpoint = `/api/v1/config/risk-configs/${configId}/data-security-entities`;
          payload = { entity_ids: selectedKeys };
          break;
        default:
          return;
      }

      await api.put(endpoint, payload);
      message.success(t('configSet.updateSuccess') || 'Updated successfully');
      setManageModalVisible(false);
      loadAssociations();
    } catch (error: any) {
      message.error(
        error.response?.data?.detail ||
        t('configSet.updateError') ||
        'Failed to update associations'
      );
    } finally {
      setTransferLoading(false);
    }
  };

  if (loading || !configSet) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  const blacklistColumns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    { title: t('common.status'), dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => (
      <Tag color={active ? 'green' : 'red'}>{active ? t('common.active') : t('common.inactive')}</Tag>
    )},
  ];

  const whitelistColumns = blacklistColumns;

  const responseTemplateColumns = [
    { title: t('common.category'), dataIndex: 'category', key: 'category' },
    { title: t('common.status'), dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => (
      <Tag color={active ? 'green' : 'red'}>{active ? t('common.active') : t('common.inactive')}</Tag>
    )},
  ];

  const knowledgeBaseColumns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    { title: t('common.status'), dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => (
      <Tag color={active ? 'green' : 'red'}>{active ? t('common.active') : t('common.inactive')}</Tag>
    )},
  ];

  const dataSecurityColumns = [
    { title: t('common.entityType'), dataIndex: 'entity_type', key: 'entity_type' },
    { title: t('common.status'), dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => (
      <Tag color={active ? 'green' : 'red'}>{active ? t('common.active') : t('common.inactive')}</Tag>
    )},
  ];

  const banPolicyColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: t('common.enabled'), dataIndex: 'enabled', key: 'enabled', render: (enabled: boolean) => (
      <Tag color={enabled ? 'green' : 'red'}>{enabled ? t('common.yes') : t('common.no')}</Tag>
    )},
  ];

  const apiKeyColumns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    { title: t('common.status'), dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => (
      <Tag color={active ? 'green' : 'red'}>{active ? t('common.active') : t('common.inactive')}</Tag>
    )},
  ];

  const enabledRiskTypes = getRiskTypesList();

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Title level={3}>
                  {configSet.name}
                  {configSet.is_default && (
                    <Tag color="blue" style={{ marginLeft: 8 }}>{t('protectionTemplate.default')}</Tag>
                  )}
                </Title>
                {configSet.description && (
                  <Text type="secondary">{configSet.description}</Text>
                )}
              </div>
              <Button onClick={() => navigate('/config/protection-templates')}>
                {t('common.back')}
              </Button>
            </div>
          </Space>
        </Card>

        {/* Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('configSet.enabledRiskTypes')}
                value={enabledRiskTypes.length}
                suffix={`/ 12`}
                prefix={<SafetyOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('configSet.blacklists')}
                value={associations?.blacklists.length || 0}
                prefix={<StopOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('configSet.whitelists')}
                value={associations?.whitelists.length || 0}
                prefix={<SafetyOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={t('configSet.apiKeys')}
                value={associations?.api_keys.length || 0}
                prefix={<KeyOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Collapsible Modules */}
        <Collapse
          defaultActiveKey={['basic', 'risk']}
          expandIconPosition="end"
        >
          {/* Basic Information */}
          <Panel
            header={
              <Space>
                <SettingOutlined />
                <Text strong>{t('configSet.basicInfo')}</Text>
              </Space>
            }
            key="basic"
          >
            <Descriptions bordered column={2}>
              <Descriptions.Item label={t('common.name')}>{configSet.name}</Descriptions.Item>
              <Descriptions.Item label={t('common.description')}>
                {configSet.description || t('common.none')}
              </Descriptions.Item>
              <Descriptions.Item label={t('configSet.isDefault')}>
                {configSet.is_default ? t('common.yes') : t('common.no')}
              </Descriptions.Item>
            </Descriptions>
          </Panel>

          {/* Risk Detection Config */}
          <Panel
            header={
              <Space>
                <SafetyOutlined />
                <Text strong>{t('configSet.riskDetection')}</Text>
              </Space>
            }
            key="risk"
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Text strong>{t('configSet.enabledRiskTypes')}:</Text>
                <div style={{ marginTop: 8 }}>
                  {enabledRiskTypes.map(rt => (
                    <Tag key={rt.code} color="blue" style={{ marginBottom: 8 }}>
                      {rt.code}: {rt.name}
                    </Tag>
                  ))}
                </div>
              </div>
              <Descriptions bordered column={2}>
                <Descriptions.Item label={t('protectionTemplate.triggerLevel')}>
                  <Tag color={
                    configSet.sensitivity_trigger_level === 'high' ? 'red' :
                    configSet.sensitivity_trigger_level === 'medium' ? 'orange' : 'green'
                  }>
                    {t(`sensitivity.${configSet.sensitivity_trigger_level}`)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label={t('protectionTemplate.highThreshold')}>
                  {(configSet.high_sensitivity_threshold * 100).toFixed(0)}%
                </Descriptions.Item>
                <Descriptions.Item label={t('protectionTemplate.mediumThreshold')}>
                  {(configSet.medium_sensitivity_threshold * 100).toFixed(0)}%
                </Descriptions.Item>
                <Descriptions.Item label={t('protectionTemplate.lowThreshold')}>
                  {(configSet.low_sensitivity_threshold * 100).toFixed(0)}%
                </Descriptions.Item>
              </Descriptions>
            </Space>
          </Panel>

          {/* Data Security (DLP) */}
          <Panel
            header={
              <Space>
                <LockOutlined />
                <Text strong>{t('configSet.dataSecurity')}</Text>
                <Tag>{associations?.data_security_entities.length || 0}</Tag>
              </Space>
            }
            key="data-security"
            extra={
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  openManageModal('data_security');
                }}
              >
                {t('common.manage')}
              </Button>
            }
          >
            <Table
              columns={dataSecurityColumns}
              dataSource={associations?.data_security_entities || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>

          {/* Ban Policies */}
          <Panel
            header={
              <Space>
                <StopOutlined />
                <Text strong>{t('configSet.banPolicies')}</Text>
                <Tag>{associations?.ban_policies.length || 0}</Tag>
              </Space>
            }
            key="ban-policy"
          >
            <Table
              columns={banPolicyColumns}
              dataSource={associations?.ban_policies || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>

          {/* Blacklists */}
          <Panel
            header={
              <Space>
                <StopOutlined />
                <Text strong>{t('config.blacklist')}</Text>
                <Tag>{associations?.blacklists.length || 0}</Tag>
              </Space>
            }
            key="blacklist"
            extra={
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  openManageModal('blacklist');
                }}
              >
                {t('common.manage')}
              </Button>
            }
          >
            <Table
              columns={blacklistColumns}
              dataSource={associations?.blacklists || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>

          {/* Whitelists */}
          <Panel
            header={
              <Space>
                <SafetyOutlined />
                <Text strong>{t('config.whitelist')}</Text>
                <Tag>{associations?.whitelists.length || 0}</Tag>
              </Space>
            }
            key="whitelist"
            extra={
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  openManageModal('whitelist');
                }}
              >
                {t('common.manage')}
              </Button>
            }
          >
            <Table
              columns={whitelistColumns}
              dataSource={associations?.whitelists || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>

          {/* Response Templates */}
          <Panel
            header={
              <Space>
                <FileTextOutlined />
                <Text strong>{t('config.rejectAnswers')}</Text>
                <Tag>{associations?.response_templates.length || 0}</Tag>
              </Space>
            }
            key="responses"
            extra={
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  openManageModal('response_template');
                }}
              >
                {t('common.manage')}
              </Button>
            }
          >
            <Table
              columns={responseTemplateColumns}
              dataSource={associations?.response_templates || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>

          {/* Knowledge Bases */}
          <Panel
            header={
              <Space>
                <BookOutlined />
                <Text strong>{t('config.knowledge')}</Text>
                <Tag>{associations?.knowledge_bases.length || 0}</Tag>
              </Space>
            }
            key="knowledge"
            extra={
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  openManageModal('knowledge_base');
                }}
              >
                {t('common.manage')}
              </Button>
            }
          >
            <Table
              columns={knowledgeBaseColumns}
              dataSource={associations?.knowledge_bases || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>

          {/* API Keys */}
          <Panel
            header={
              <Space>
                <KeyOutlined />
                <Text strong>{t('configSet.apiKeys')}</Text>
                <Tag>{associations?.api_keys.length || 0}</Tag>
              </Space>
            }
            key="api-keys"
          >
            <Table
              columns={apiKeyColumns}
              dataSource={associations?.api_keys || []}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: t('common.noData') }}
            />
          </Panel>
        </Collapse>
      </Space>

      {/* Management Modal */}
      <Modal
        title={
          managingType === 'blacklist' ? t('configSet.manageBlacklists') :
          managingType === 'whitelist' ? t('configSet.manageWhitelists') :
          managingType === 'response_template' ? t('configSet.manageResponseTemplates') :
          managingType === 'knowledge_base' ? t('configSet.manageKnowledgeBases') :
          managingType === 'data_security' ? t('configSet.manageDataSecurity') :
          t('common.manage')
        }
        open={manageModalVisible}
        onCancel={() => setManageModalVisible(false)}
        onOk={handleSaveAssociations}
        width={800}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        confirmLoading={transferLoading}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Text type="secondary">
            {t('configSet.manageDescription') || 'Select items to associate with this config set. You can select multiple items.'}
          </Text>

          {transferLoading ? (
            <Spin />
          ) : (
            <Checkbox.Group
              value={selectedKeys}
              onChange={(values) => setSelectedKeys(values as string[])}
              style={{ width: '100%' }}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {availableItems.map((item: any) => (
                  <Checkbox key={String(item.id)} value={String(item.id)}>
                    <Space>
                      <Text strong>
                        {item.name || item.category || item.entity_type || item.id}
                      </Text>
                      {item.is_active !== undefined && (
                        <Tag color={item.is_active ? 'green' : 'red'}>
                          {item.is_active ? t('common.active') : t('common.inactive')}
                        </Tag>
                      )}
                    </Space>
                  </Checkbox>
                ))}
              </Space>
            </Checkbox.Group>
          )}

          {availableItems.length === 0 && !transferLoading && (
            <Text type="secondary">
              {t('configSet.noItemsAvailable') || 'No items available. Please create some items first.'}
            </Text>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export default ConfigSetDetail;
