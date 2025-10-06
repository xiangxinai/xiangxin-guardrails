import React, { useState, useEffect } from 'react';
import { Card, Form, Switch, Select, InputNumber, Button, Table, message, Modal, Tag, Space, Descriptions } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { configApi } from '../../services/api';

const { Option } = Select;

interface BanPolicy {
  id: string;
  tenant_id: string;
  enabled: boolean;
  risk_level: string;
  trigger_count: number;
  time_window_minutes: number;
  ban_duration_minutes: number;
  created_at: string;
  updated_at: string;
}

interface BannedUser {
  id: string;
  user_id: string;
  banned_at: string;
  ban_until: string;
  trigger_count: number;
  risk_level: string;
  reason: string;
  is_active: boolean;
  status: string;
}

interface RiskTrigger {
  id: string;
  detection_result_id: string | null;
  risk_level: string;
  triggered_at: string;
}

const BanPolicy: React.FC = () => {
  const [form] = Form.useForm();
  const [policy, setPolicy] = useState<BanPolicy | null>(null);
  const [bannedUsers, setBannedUsers] = useState<BannedUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [tableLoading, setTableLoading] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [userHistory, setUserHistory] = useState<RiskTrigger[]>([]);

  // 获取封禁策略
  const fetchPolicy = async () => {
    try {
      setLoading(true);
      const policyData = await configApi.banPolicy.get();
      setPolicy(policyData);
      form.setFieldsValue({
        enabled: policyData.enabled,
        risk_level: policyData.risk_level,
        trigger_count: policyData.trigger_count,
        time_window_minutes: policyData.time_window_minutes,
        ban_duration_minutes: policyData.ban_duration_minutes,
      });
    } catch (error: any) {
      message.error('获取封禁策略失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取封禁用户列表
  const fetchBannedUsers = async () => {
    try {
      setTableLoading(true);
      const data = await configApi.banPolicy.getBannedUsers();
      setBannedUsers(data.users);
    } catch (error: any) {
      message.error('获取封禁用户列表失败');
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicy();
    fetchBannedUsers();
  }, []);

  // 保存策略
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await configApi.banPolicy.update(values);
      message.success('保存成功');
      fetchPolicy();
    } catch (error: any) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  // 应用模板
  const applyTemplate = (template: string) => {
    const templates: { [key: string]: any } = {
      strict: {
        enabled: true,
        risk_level: '高风险',
        trigger_count: 3,
        time_window_minutes: 10,
        ban_duration_minutes: 60,
      },
      standard: {
        enabled: true,
        risk_level: '高风险',
        trigger_count: 5,
        time_window_minutes: 30,
        ban_duration_minutes: 30,
      },
      relaxed: {
        enabled: true,
        risk_level: '高风险',
        trigger_count: 10,
        time_window_minutes: 60,
        ban_duration_minutes: 15,
      },
      disabled: {
        enabled: false,
        risk_level: '高风险',
        trigger_count: 3,
        time_window_minutes: 10,
        ban_duration_minutes: 60,
      },
    };

    form.setFieldsValue(templates[template]);
  };

  // 解封用户
  const handleUnban = async (userId: string) => {
    try {
      await configApi.banPolicy.unbanUser(userId);
      message.success('解封成功');
      fetchBannedUsers();
    } catch (error: any) {
      message.error('解封失败');
    }
  };

  // 查看用户风险历史
  const viewUserHistory = async (userId: string) => {
    try {
      setSelectedUserId(userId);
      const data = await configApi.banPolicy.getUserHistory(userId);
      setUserHistory(data.history);
      setHistoryVisible(true);
    } catch (error: any) {
      message.error('获取用户历史失败');
    }
  };

  const columns: ColumnsType<BannedUser> = [
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 200,
    },
    {
      title: '封禁时间',
      dataIndex: 'banned_at',
      key: 'banned_at',
      width: 180,
      render: (text) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '解封时间',
      dataIndex: 'ban_until',
      key: 'ban_until',
      width: 180,
      render: (text) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '触发次数',
      dataIndex: 'trigger_count',
      key: 'trigger_count',
      width: 100,
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 100,
      render: (level) => {
        const color = level === '高风险' ? 'red' : level === '中风险' ? 'orange' : 'blue';
        return <Tag color={color}>{level}</Tag>;
      },
    },
    {
      title: '封禁原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const color = status === '封禁中' ? 'red' : 'green';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.status === '封禁中' && (
            <Button type="link" size="small" onClick={() => handleUnban(record.user_id)}>
              解封
            </Button>
          )}
          <Button type="link" size="small" onClick={() => viewUserHistory(record.user_id)}>
            查看历史
          </Button>
        </Space>
      ),
    },
  ];

  const historyColumns: ColumnsType<RiskTrigger> = [
    {
      title: '触发时间',
      dataIndex: 'triggered_at',
      key: 'triggered_at',
      render: (text) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level) => {
        const color = level === '高风险' ? 'red' : level === '中风险' ? 'orange' : 'blue';
        return <Tag color={color}>{level}</Tag>;
      },
    },
    {
      title: '检测结果ID',
      dataIndex: 'detection_result_id',
      key: 'detection_result_id',
      render: (id) => id || '-',
    },
  ];

  return (
    <div>
      <Card title="封禁策略配置" style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical">
          <Form.Item
            name="enabled"
            label="启用封禁策略"
            valuePropName="checked"
            extra="启用后，当用户在指定时间窗口内触发指定次数的风险时，将自动封禁"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="risk_level"
            label="触发风险等级"
            extra="达到此等级及以上的风险才会被记录"
          >
            <Select>
              <Option value="高风险">高风险</Option>
              <Option value="中风险">中风险</Option>
              <Option value="低风险">低风险</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="trigger_count"
            label="触发次数阈值"
            extra="在时间窗口内触发多少次后封禁（1-100次）"
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="time_window_minutes"
            label="时间窗口（分钟）"
            extra="统计触发次数的时间范围（1-1440分钟，即1天）"
          >
            <InputNumber min={1} max={1440} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="ban_duration_minutes"
            label="封禁时长（分钟）"
            extra="封禁持续时间（1-10080分钟，即7天）"
          >
            <InputNumber min={1} max={10080} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" onClick={handleSave} loading={loading}>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="预设模板" style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Button onClick={() => applyTemplate('strict')}>严格模式</Button>
          <Button onClick={() => applyTemplate('standard')}>标准模式</Button>
          <Button onClick={() => applyTemplate('relaxed')}>宽松模式</Button>
          <Button onClick={() => applyTemplate('disabled')}>关闭</Button>
        </Space>
        <Descriptions column={1} size="small" style={{ marginTop: 16 }}>
          <Descriptions.Item label="严格模式">高风险 ≥ 3次/10分钟 → 封禁60分钟</Descriptions.Item>
          <Descriptions.Item label="标准模式">高风险 ≥ 5次/30分钟 → 封禁30分钟</Descriptions.Item>
          <Descriptions.Item label="宽松模式">高风险 ≥ 10次/60分钟 → 封禁15分钟</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="封禁用户列表">
        <Table
          columns={columns}
          dataSource={bannedUsers}
          loading={tableLoading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      <Modal
        title={`用户 ${selectedUserId} 的风险历史`}
        open={historyVisible}
        onCancel={() => setHistoryVisible(false)}
        footer={null}
        width={800}
      >
        <Table
          columns={historyColumns}
          dataSource={userHistory}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Modal>
    </div>
  );
};

export default BanPolicy;
