import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  message,
  Typography,
  Modal,
  Form,
  Input,
  Switch,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  MailOutlined,
  KeyOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { adminApi } from '../../services/api';

const { Title, Text } = Typography;

interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_super_admin: boolean;
  api_key: string;
  detection_count: number;
  created_at: string;
  updated_at: string;
}

interface AdminStats {
  total_users: number;
  total_detections: number;
  user_detection_counts: Array<{
    user_id: string;
    email: string;
    detection_count: number;
  }>;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchText, setSearchText] = useState('');
  const [sortBy, setSortBy] = useState<'created_at' | 'detection_count'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [form] = Form.useForm();
  const { user: currentUser } = useAuth();

  const loadAdminStats = async () => {
    try {
      const response = await adminApi.getAdminStats();
      setAdminStats(response.data);
    } catch (error) {
      console.error('Failed to load admin stats:', error);
      message.error('加载统计信息失败');
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await adminApi.getUsers();
      setUsers(response.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadData = async () => {
    await Promise.all([loadUsers(), loadAdminStats()]);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      email: user.email,
      is_active: user.is_active,
      is_verified: user.is_verified,
      is_super_admin: user.is_super_admin,
    });
    setModalVisible(true);
  };

  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleSave = async (values: any) => {
    try {
      if (editingUser) {
        // 更新用户
        await adminApi.updateUser(editingUser.id, values);
        message.success('用户更新成功');
      } else {
        // 创建新用户
        await adminApi.createUser(values);
        message.success('用户创建成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      loadUsers();
    } catch (error: any) {
      console.error('Save user failed:', error);
      message.error(error.response?.data?.detail || '保存失败');
    }
  };

  const handleDelete = async (userId: string) => {
    try {
      await adminApi.deleteUser(userId);
      message.success('用户删除成功');
      loadUsers();
    } catch (error: any) {
      console.error('Delete user failed:', error);
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleResetApiKey = async (userId: string) => {
    try {
      await adminApi.resetUserApiKey(userId);
      message.success('API Key重置成功');
      loadUsers();
    } catch (error: any) {
      console.error('Reset API key failed:', error);
      message.error(error.response?.data?.detail || 'API Key重置失败');
    }
  };

  const columns = [
    {
      title: '用户邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email: string, record: User) => (
        <Space>
          <UserOutlined />
          <Text>{email}</Text>
          {record.id === currentUser?.id && <Tag color="blue">当前用户</Tag>}
        </Space>
      ),
    },
    {
      title: '状态',
      key: 'status',
      width: 160,
      render: (_: any, record: User) => (
        <Space size={4} direction="vertical" style={{ display: 'flex' }}>
          <Tag color={record.is_active ? 'green' : 'red'} size="small">
            {record.is_active ? '已激活' : '已禁用'}
          </Tag>
          <Tag color={record.is_verified ? 'green' : 'orange'} size="small">
            {record.is_verified ? '已验证' : '未验证'}
          </Tag>
          {record.is_super_admin && (
            <Tag color="red" size="small">超级管理员</Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      render: (apiKey: string, record: User) => (
        <Space>
          <Text code copyable={{ text: apiKey }}>
            {apiKey ? `${apiKey.substring(0, 20)}...` : '未生成'}
          </Text>
          <Tooltip title="重置API Key">
            <Button
              type="link"
              size="small"
              icon={<KeyOutlined />}
              onClick={() => handleResetApiKey(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
    {
      title: 'UUID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Text code copyable={{ text: id }}>
          {id.substring(0, 8)}...
        </Text>
      ),
    },
    {
      title: '检测次数',
      dataIndex: 'detection_count',
      key: 'detection_count',
      sorter: (a: User, b: User) => a.detection_count - b.detection_count,
      render: (count: number) => (
        <Tag color={count > 0 ? 'blue' : 'default'}>
          {count}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a: User, b: User) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space>
          <Tooltip title="编辑用户">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {record.id !== currentUser?.id && (
            <Popconfirm
              title="确定要删除这个用户吗？"
              description="此操作不可恢复"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除用户">
                <Button
                  type="link"
                  size="small"
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
    <div>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              <UserOutlined style={{ marginRight: 8 }} />
              用户管理
            </Title>
            <Text type="secondary">管理系统中的所有用户账号</Text>
            {adminStats && (
              <div style={{ marginTop: 8 }}>
                <Space split={<Text type="secondary">|</Text>}>
                  <Text>
                    <strong>{adminStats.total_users}</strong> 个用户
                  </Text>
                  <Text>
                    总检测次数: <strong>{adminStats.total_detections}</strong>
                  </Text>
                </Space>
              </div>
            )}
          </div>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadData}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              添加用户
            </Button>
          </Space>
        </div>

        {/* 搜索框 */}
        <div style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="按 UUID 搜索用户"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
        </div>

        <Table
          columns={columns}
          dataSource={users.filter(user => 
            !searchText || user.id.toLowerCase().includes(searchText.toLowerCase())
          )}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个用户`,
          }}
        />
      </Card>

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Form.Item
            name="email"
            label="用户邮箱"
            rules={[
              { required: true, message: '请输入用户邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="用户邮箱"
              disabled={!!editingUser}
            />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="初始密码"
              rules={[
                { required: true, message: '请输入初始密码' },
                { min: 6, message: '密码至少6位' }
              ]}
            >
              <Input.Password placeholder="初始密码" />
            </Form.Item>
          )}

          <Form.Item
            name="is_active"
            label="账号状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch
              checkedChildren="激活"
              unCheckedChildren="禁用"
            />
          </Form.Item>

          <Form.Item
            name="is_verified"
            label="邮箱验证"
            valuePropName="checked"
            initialValue={false}
          >
            <Switch
              checkedChildren="已验证"
              unCheckedChildren="未验证"
            />
          </Form.Item>

          {/* 超级管理员由 .env 决定，此处仅展示状态，不可修改 */}
          <Form.Item label="超级管理员">
            <Switch
              checked={!!editingUser?.is_super_admin}
              checkedChildren="是"
              unCheckedChildren="否"
              disabled
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;