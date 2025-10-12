import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, Space, message, Tag, Select, Alert, Card } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, FilterOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { configApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import type { Blacklist } from '../../types';
import api from '../../services/api';
import ConfigSetSelector from '../../components/ConfigSetSelector';

const { TextArea } = Input;
const { Option } = Select;

interface ConfigTemplate {
  id: number;
  name: string;
  is_default: boolean;
}

const BlacklistManagement: React.FC = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<Blacklist[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<Blacklist | null>(null);
  const [configTemplates, setConfigTemplates] = useState<ConfigTemplate[]>([]);
  const [selectedConfigSet, setSelectedConfigSet] = useState<number | undefined>();
  const [form] = Form.useForm();
  const { onUserSwitch } = useAuth();

  useEffect(() => {
    fetchData();
    fetchConfigTemplates();
  }, []);

  useEffect(() => {
    if (selectedConfigSet) {
      fetchData();
    }
  }, [selectedConfigSet]);

  // Listen to user switch event, automatically refresh data
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      fetchData();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Filter by selected config set if one is selected
      const params = selectedConfigSet ? { template_id: selectedConfigSet } : {};
      const result = await configApi.blacklist.list(params);
      setData(result);
    } catch (error) {
      console.error('Error fetching blacklist:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfigTemplates = async () => {
    try {
      const response = await api.get('/api/v1/config/risk-configs');
      setConfigTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching config templates:', error);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    // Pre-fill template_id with currently selected config set
    if (selectedConfigSet) {
      form.setFieldsValue({ template_id: selectedConfigSet });
    }
    setModalVisible(true);
  };

  const handleEdit = (record: Blacklist) => {
    setEditingItem(record);
    form.setFieldsValue({
      ...record,
      keywords: record.keywords.join('\n'),
    });
    setModalVisible(true);
  };

  const handleDelete = (record: Blacklist) => {
    Modal.confirm({
      title: t('config.blacklist.confirmDelete'),
      content: t('config.blacklist.confirmDeleteContent', { name: record.name }),
      okText: t('common.confirm'),
      cancelText: t('common.cancel'),
      onOk: async () => {
        try {
          await configApi.blacklist.delete(record.id);
          message.success(t('common.deleteSuccess'));
          fetchData();
        } catch (error) {
          console.error('Error deleting blacklist:', error);
        }
      },
    });
  };

  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        keywords: values.keywords.split('\n').filter((k: string) => k.trim()),
      };

      if (editingItem) {
        await configApi.blacklist.update(editingItem.id, submitData);
        message.success(t('common.updateSuccess'));
      } else {
        await configApi.blacklist.create(submitData);
        message.success(t('common.createSuccess'));
      }

      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Error saving blacklist:', error);
      message.error(t('common.saveFailed'));
    }
  };

  const handleToggleStatus = async (record: Blacklist) => {
    try {
      await configApi.blacklist.update(record.id, {
        name: record.name,
        keywords: record.keywords,
        description: record.description,
        is_active: !record.is_active
      });
      message.success(t(!record.is_active ? 'common.enableSuccess' : 'common.disableSuccess'));
      fetchData();
    } catch (error) {
      console.error('Error toggling blacklist status:', error);
      message.error(t('common.operationFailed'));
    }
  };

  const getTemplateName = (templateId: number | null) => {
    if (!templateId) return t('common.none');
    const template = configTemplates.find(t => t.id === templateId);
    return template ? template.name : t('common.none');
  };

  const columns = [
    {
      title: t('blacklist.name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('blacklist.configTemplate'),
      dataIndex: 'template_id',
      key: 'template_id',
      render: (templateId: number | null) => (
        <Tag color={templateId ? 'blue' : 'default'}>
          {getTemplateName(templateId)}
        </Tag>
      ),
    },
    {
      title: t('blacklist.keywordCount'),
      dataIndex: 'keywords',
      key: 'keywords',
      render: (keywords: string[]) => keywords?.length || 0,
    },
    {
      title: t('blacklist.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: t('common.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean, record: Blacklist) => (
        <Space>
          <Tag color={active ? 'green' : 'red'}>
            {active ? t('common.enabled') : t('common.disabled')}
          </Tag>
          <Button
            type="link"
            size="small"
            onClick={() => handleToggleStatus(record)}
          >
            {active ? t('common.disable') : t('common.enable')}
          </Button>
        </Space>
      ),
    },
    {
      title: t('common.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: t('common.action'),
      key: 'action',
      render: (_: any, record: Blacklist) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            {t('common.edit')}
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            {t('common.delete')}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Config Set Filter */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            message={t('configSet.filterInfo') || 'Select a config set to view and manage its blacklists'}
            description={
              t('configSet.filterDescription') ||
              'You can filter blacklists by config set. Only blacklists belonging to the selected config set will be displayed.'
            }
            type="info"
            showIcon
            icon={<FilterOutlined />}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 120 }}>{t('configSet.selectConfigSet') || 'Config Set:'}  </span>
            <ConfigSetSelector
              value={selectedConfigSet}
              onChange={setSelectedConfigSet}
              allowCreate={true}
              style={{ flex: 1 }}
            />
          </div>
        </Space>
      </Card>

      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
          disabled={!selectedConfigSet}
        >
          {t('blacklist.addBlacklist')}
        </Button>
        {!selectedConfigSet && (
          <span style={{ marginLeft: 8, color: '#999' }}>
            {t('configSet.pleaseSelectFirst') || 'Please select a config set first'}
          </span>
        )}
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingItem ? t('blacklist.editBlacklist') : t('blacklist.addBlacklist')}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label={t('blacklist.name')}
            rules={[{ required: true, message: t('blacklist.nameRequired') }]}
          >
            <Input placeholder={t('blacklist.namePlaceholder')} />
          </Form.Item>

          <Form.Item
            name="template_id"
            label={t('blacklist.configTemplate')}
            extra={t('blacklist.configTemplateExtra')}
          >
            <Select
              placeholder={t('blacklist.selectConfigTemplate')}
              allowClear
            >
              {configTemplates.map(template => (
                <Option key={template.id} value={template.id}>
                  {template.name}
                  {template.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>{t('protectionTemplate.default')}</Tag>}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="keywords"
            label={t('blacklist.keywords')}
            rules={[{ required: true, message: t('blacklist.keywordsRequired') }]}
            extra={t('blacklist.keywordsExtra')}
          >
            <TextArea
              rows={6}
              placeholder={t('blacklist.keywordsPlaceholder')}
            />
          </Form.Item>

          <Form.Item
            name="description"
            label={t('blacklist.description')}
          >
            <TextArea
              rows={3}
              placeholder={t('blacklist.descriptionPlaceholder')}
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label={t('common.enableStatus')}
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default BlacklistManagement;