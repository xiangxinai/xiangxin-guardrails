import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, Space, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { configApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import type { Whitelist } from '../../types';

const { TextArea } = Input;

const WhitelistManagement: React.FC = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<Whitelist[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<Whitelist | null>(null);
  const [form] = Form.useForm();
  const { onUserSwitch } = useAuth();

  useEffect(() => {
    fetchData();
  }, []);

  // 监听用户切换事件，自动刷新数据
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      fetchData();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const result = await configApi.whitelist.list();
      setData(result);
    } catch (error) {
      console.error('Error fetching whitelist:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: Whitelist) => {
    setEditingItem(record);
    form.setFieldsValue({
      ...record,
      keywords: record.keywords.join('\n'),
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        keywords: values.keywords.split('\n').filter((k: string) => k.trim()),
      };

      if (editingItem) {
        await configApi.whitelist.update(editingItem.id, submitData);
        message.success(t('common.updateSuccess'));
      } else {
        await configApi.whitelist.create(submitData);
        message.success(t('common.createSuccess'));
      }

      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Error saving whitelist:', error);
      message.error(t('common.saveFailed'));
    }
  };

  const handleDelete = async (record: Whitelist) => {
    try {
      await configApi.whitelist.delete(record.id);
      message.success(t('common.deleteSuccess'));
      fetchData();
    } catch (error) {
      console.error('Error deleting whitelist:', error);
      message.error(t('common.deleteFailed'));
    }
  };

  const handleToggleStatus = async (record: Whitelist) => {
    try {
      await configApi.whitelist.update(record.id, {
        name: record.name,
        keywords: record.keywords,
        description: record.description,
        is_active: !record.is_active
      });
      message.success(t(!record.is_active ? 'common.enableSuccess' : 'common.disableSuccess'));
      fetchData();
    } catch (error) {
      console.error('Error toggling whitelist status:', error);
      message.error(t('common.operationFailed'));
    }
  };

  const columns = [
    {
      title: t('config.whitelist.name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('config.whitelist.keywordCount'),
      dataIndex: 'keywords',
      key: 'keywords',
      render: (keywords: string[]) => keywords?.length || 0,
    },
    {
      title: t('config.whitelist.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: t('common.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean, record: Whitelist) => (
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
      render: (_: any, record: Whitelist) => (
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
            onClick={() => {
              if (confirm(t('config.whitelist.confirmDeleteContent', { name: record.name }))) {
                handleDelete(record);
              }
            }}
          >
            {t('common.delete')}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
        >
          {t('config.whitelist.addWhitelist')}
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingItem ? t('config.whitelist.editWhitelist') : t('config.whitelist.addWhitelist')}
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
            label={t('config.whitelist.name')}
            rules={[{ required: true, message: t('config.whitelist.nameRequired') }]}
          >
            <Input placeholder={t('config.whitelist.namePlaceholder')} />
          </Form.Item>

          <Form.Item
            name="keywords"
            label={t('config.whitelist.keywords')}
            rules={[{ required: true, message: t('config.whitelist.keywordsRequired') }]}
            extra={t('config.whitelist.keywordsExtra')}
          >
            <TextArea
              rows={6}
              placeholder={t('config.whitelist.keywordsPlaceholder')}
            />
          </Form.Item>

          <Form.Item
            name="description"
            label={t('config.whitelist.description')}
          >
            <TextArea
              rows={3}
              placeholder={t('config.whitelist.descriptionPlaceholder')}
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

export default WhitelistManagement;