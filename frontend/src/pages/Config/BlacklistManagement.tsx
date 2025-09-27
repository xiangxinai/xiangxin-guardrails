import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, Space, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { configApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import type { Blacklist } from '../../types';

const { TextArea } = Input;

const BlacklistManagement: React.FC = () => {
  const [data, setData] = useState<Blacklist[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<Blacklist | null>(null);
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
      const result = await configApi.blacklist.list();
      setData(result);
    } catch (error) {
      console.error('Error fetching blacklist:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
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
      title: '确认删除',
      content: `确定要删除黑名单 "${record.name}" 吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await configApi.blacklist.delete(record.id);
          message.success('删除成功');
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
        message.success('更新成功');
      } else {
        await configApi.blacklist.create(submitData);
        message.success('创建成功');
      }

      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Error saving blacklist:', error);
      message.error('保存失败，请重试');
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
      message.success(`${!record.is_active ? '启用' : '禁用'}成功`);
      fetchData();
    } catch (error) {
      console.error('Error toggling blacklist status:', error);
      message.error('操作失败，请重试');
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '关键词数量',
      dataIndex: 'keywords',
      key: 'keywords',
      render: (keywords: string[]) => keywords?.length || 0,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean, record: Blacklist) => (
        <Space>
          <Tag color={active ? 'green' : 'red'}>
            {active ? '启用' : '禁用'}
          </Tag>
          <Button
            type="link"
            size="small"
            onClick={() => handleToggleStatus(record)}
          >
            {active ? '禁用' : '启用'}
          </Button>
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Blacklist) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
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
          添加黑名单
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingItem ? '编辑黑名单' : '添加黑名单'}
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
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入黑名单名称" />
          </Form.Item>

          <Form.Item
            name="keywords"
            label="关键词"
            rules={[{ required: true, message: '请输入关键词' }]}
            extra="每行一个关键词"
          >
            <TextArea
              rows={6}
              placeholder="请输入关键词，每行一个"
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入描述"
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="启用状态"
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