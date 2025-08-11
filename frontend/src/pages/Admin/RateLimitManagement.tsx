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
  InputNumber,
  Switch,
  Select,
  Tooltip,
  Popconfirm,
  Statistic,
  Row,
  Col
} from 'antd';
import {
  ThunderboltOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  UserOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { adminApi } from '../../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_super_admin: boolean;
}

interface RateLimit {
  user_id: string;
  email: string;
  requests_per_second: number;
  is_active: boolean;
}

const RateLimitManagement: React.FC = () => {
  const [rateLimits, setRateLimits] = useState<RateLimit[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRateLimit, setEditingRateLimit] = useState<RateLimit | null>(null);
  const [form] = Form.useForm();

  const loadRateLimits = async () => {
    setLoading(true);
    try {
      const response = await adminApi.getRateLimits();
      setRateLimits(response.data || []);
    } catch (error) {
      console.error('Failed to load rate limits:', error);
      message.error('加载限速配置失败');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await adminApi.getUsers();
      setUsers(response.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  useEffect(() => {
    loadRateLimits();
    loadUsers();
  }, []);

  const handleEdit = (rateLimit: RateLimit) => {
    setEditingRateLimit(rateLimit);
    form.setFieldsValue({
      user_id: rateLimit.user_id,
      requests_per_second: rateLimit.requests_per_second,
      is_active: rateLimit.is_active,
    });
    setModalVisible(true);
  };

  const handleAdd = () => {
    setEditingRateLimit(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleSave = async (values: any) => {
    try {
      if (editingRateLimit) {
        // 更新限速配置
        await adminApi.setUserRateLimit({
          user_id: editingRateLimit.user_id,
          requests_per_second: values.requests_per_second
        });
        message.success('限速配置更新成功');
      } else {
        // 创建新限速配置
        await adminApi.setUserRateLimit({
          user_id: values.user_id,
          requests_per_second: values.requests_per_second
        });
        message.success('限速配置创建成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      loadRateLimits();
    } catch (error: any) {
      console.error('Save rate limit failed:', error);
      message.error(error.response?.data?.detail || '保存失败');
    }
  };

  const handleDelete = async (userId: string) => {
    try {
      await adminApi.removeUserRateLimit(userId);
      message.success('限速配置删除成功');
      loadRateLimits();
    } catch (error: any) {
      console.error('Delete rate limit failed:', error);
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const getAvailableUsers = () => {
    // 过滤掉已有限速配置的用户
    const configuredUserIds = rateLimits.map(rl => rl.user_id);
    return users.filter(user => !configuredUserIds.includes(user.id));
  };

  const getRpsDisplay = (rps: number) => {
    if (rps === 0) {
      return <Tag color="green">无限制</Tag>;
    }
    return <Tag color={rps > 10 ? 'blue' : rps > 5 ? 'orange' : 'red'}>{rps} 请求/秒</Tag>;
  };

  const getStatistics = () => {
    const totalUsers = rateLimits.length;
    const unlimitedUsers = rateLimits.filter(rl => rl.requests_per_second === 0).length;
    const avgRps = rateLimits.length > 0 
      ? rateLimits.filter(rl => rl.requests_per_second > 0)
                  .reduce((sum, rl) => sum + rl.requests_per_second, 0) / 
        rateLimits.filter(rl => rl.requests_per_second > 0).length || 0
      : 0;

    return { totalUsers, unlimitedUsers, avgRps };
  };

  const stats = getStatistics();

  const columns = [
    {
      title: '用户',
      key: 'user',
      render: (_: any, record: RateLimit) => (
        <Space>
          <UserOutlined />
          <Text>{record.email}</Text>
        </Space>
      ),
    },
    {
      title: '限速配置',
      key: 'rps',
      render: (_: any, record: RateLimit) => getRpsDisplay(record.requests_per_second),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '说明',
      key: 'description',
      render: (_: any, record: RateLimit) => {
        if (record.requests_per_second === 0) {
          return <Text type="secondary">允许无限制调用</Text>;
        }
        const dailyMax = record.requests_per_second * 86400;
        return <Text type="secondary">每日最多 {dailyMax.toLocaleString()} 次调用</Text>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: RateLimit) => (
        <Space>
          <Tooltip title="编辑配置">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个限速配置吗？"
            description="删除后该用户将使用默认限速（1 请求/秒）"
            onConfirm={() => handleDelete(record.user_id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除配置">
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总配置数量"
              value={stats.totalUsers}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="无限制用户"
              value={stats.unlimitedUsers}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均限速"
              value={stats.avgRps}
              precision={1}
              suffix="RPS"
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="受限用户"
              value={stats.totalUsers - stats.unlimitedUsers}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              <ThunderboltOutlined style={{ marginRight: 8 }} />
              用户限速配置
            </Title>
            <Text type="secondary">
              配置用户的API调用频率限制
              <Tooltip title="限速配置说明：0表示无限制，其他数值表示每秒允许的最大请求数。未配置的用户默认为1请求/秒。">
                <InfoCircleOutlined style={{ marginLeft: 4 }} />
              </Tooltip>
            </Text>
          </div>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadRateLimits}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
              disabled={getAvailableUsers().length === 0}
            >
              添加配置
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={rateLimits}
          rowKey="user_id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个配置`,
          }}
        />
      </Card>

      <Modal
        title={editingRateLimit ? '编辑限速配置' : '添加限速配置'}
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
          {!editingRateLimit && (
            <Form.Item
              name="user_id"
              label="选择用户"
              rules={[{ required: true, message: '请选择用户' }]}
            >
              <Select
                placeholder="请选择要配置限速的用户"
                showSearch
                optionFilterProp="children"
              >
                {getAvailableUsers().map(user => (
                  <Option key={user.id} value={user.id}>
                    {user.email}
                    {user.is_super_admin && <Tag color="red" size="small" style={{ marginLeft: 8 }}>管理员</Tag>}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          <Form.Item
            name="requests_per_second"
            label="请求频率限制"
            rules={[{ required: true, message: '请设置请求频率' }]}
            extra="设置为 0 表示无限制；建议值：1-50 请求/秒"
            initialValue={1}
          >
            <InputNumber
              min={0}
              max={1000}
              style={{ width: '100%' }}
              addonAfter="请求/秒"
              placeholder="请求频率"
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch
              checkedChildren="启用"
              unCheckedChildren="禁用"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RateLimitManagement;