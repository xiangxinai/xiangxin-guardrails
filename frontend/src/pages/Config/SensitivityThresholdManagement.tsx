import React, { useState, useEffect } from 'react';
import {
  Card,
  InputNumber,
  message,
  Spin,
  Typography,
  Space,
  Button,
  Table,
  Tag,
  Alert,
  Modal,
  Select,
  Divider
} from 'antd';
import {
  InfoCircleOutlined,
  EditOutlined,
  CheckOutlined
} from '@ant-design/icons';
import { sensitivityThresholdApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;

interface SensitivityThresholdConfig {
  high_sensitivity_threshold: number;
  medium_sensitivity_threshold: number;
  low_sensitivity_threshold: number;
  sensitivity_trigger_level: string;
}

interface SensitivityLevel {
  key: string;
  name: string;
  threshold: number;
  description: string;
  target: string;
}

const SensitivityThresholdManagement: React.FC = () => {
  const [config, setConfig] = useState<SensitivityThresholdConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingLevels, setEditingLevels] = useState<SensitivityLevel[]>([]);
  const [saving, setSaving] = useState(false);
  const { onUserSwitch } = useAuth();

  useEffect(() => {
    loadConfig();
  }, []);

  // 监听用户切换事件，自动刷新配置
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      loadConfig();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await sensitivityThresholdApi.get();
      setConfig(data);
    } catch (error) {
      message.error('加载敏感度阈值配置失败');
      console.error('Failed to load sensitivity threshold config:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取敏感度等级数据
  const getSensitivityLevels = (): SensitivityLevel[] => {
    if (!config) return [];

    return [
      {
        key: 'high',
        name: '高',
        threshold: config.high_sensitivity_threshold,
        description: '检测最严格，稍有可疑就触发告警',
        target: '特定敏感时期或敏感场景专用。最高覆盖率，可能有误报'
      },
      {
        key: 'medium',
        name: '中',
        threshold: config.medium_sensitivity_threshold,
        description: '平衡检测，适度敏感',
        target: '默认配置。平衡准确率与覆盖率'
      },
      {
        key: 'low',
        name: '低',
        threshold: config.low_sensitivity_threshold,
        description: '检测最宽松，只在非常确定时告警',
        target: '自动化流水线。最高准确率，可能漏报'
      }
    ];
  };

  // 打开编辑模态框
  const handleEdit = () => {
    const levels = getSensitivityLevels();
    setEditingLevels(levels);
    setEditModalVisible(true);
  };

  // 验证阈值设置
  const validateThresholds = (levels: SensitivityLevel[]): boolean => {
    const sortedLevels = [...levels].sort((a, b) => b.threshold - a.threshold);
    // 阈值必须是0-1之间
    if (sortedLevels[0].threshold < 0 || sortedLevels[0].threshold > 1) {
      message.error('敏感度阈值必须在0.0-1.0之间');
      return false;
    }

    // 检查是否从高到低排序
    if (sortedLevels[0].key !== 'low' || sortedLevels[1].key !== 'medium' || sortedLevels[2].key !== 'high') {
      message.error('敏感度阈值必须按照低→中→高的顺序设置');
      return false;
    }

    // 检查是否有重叠
    for (let i = 0; i < sortedLevels.length - 1; i++) {
      if (sortedLevels[i].threshold <= sortedLevels[i + 1].threshold) {
        message.error('敏感度阈值不能重叠或相等');
        return false;
      }
    }

    return true;
  };

  // 保存配置
  const handleSave = async () => {
    if (!validateThresholds(editingLevels)) return;

    try {
      setSaving(true);

      const newConfig: SensitivityThresholdConfig = {
        high_sensitivity_threshold: editingLevels.find(l => l.key === 'high')!.threshold,
        medium_sensitivity_threshold: editingLevels.find(l => l.key === 'medium')!.threshold,
        low_sensitivity_threshold: editingLevels.find(l => l.key === 'low')!.threshold,
        sensitivity_trigger_level: config?.sensitivity_trigger_level || 'medium'
      };

      await sensitivityThresholdApi.update(newConfig);
      setConfig(newConfig);
      setEditModalVisible(false);
      message.success('敏感度阈值配置已更新');
    } catch (error) {
      message.error('更新敏感度阈值配置失败');
      console.error('Failed to update sensitivity threshold config:', error);
    } finally {
      setSaving(false);
    }
  };

  // 处理当前敏感度等级的变更
  const handleTriggerLevelChange = async (value: string) => {
    if (!config) return;

    try {
      setSaving(true);
      const newConfig = { ...config, sensitivity_trigger_level: value };

      await sensitivityThresholdApi.update(newConfig);
      setConfig(newConfig);

      const levelNames = { low: '低', medium: '中', high: '高' };
      message.success(`当前敏感度等级已设置为 ${levelNames[value as keyof typeof levelNames]}敏感度`);
    } catch (error) {
      message.error('更新当前敏感度等级失败');
      console.error('Failed to update sensitivity trigger level:', error);
    } finally {
      setSaving(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '敏感度等级',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => {
        const colors = { '高': '#f5222d', '中': '#fa8c16', '低': '#52c41a' };
        return <Tag color={colors[text as keyof typeof colors]}>{text}敏感度</Tag>;
      }
    },
    {
      title: '概率阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (value: number) => <Text code>{value.toFixed(2)}</Text>
    },
    {
      title: '检测特性',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '使用场景',
      dataIndex: 'target',
      key: 'target',
    }
  ];

  // 编辑模态框的表格列
  const editColumns = [
    {
      title: '敏感度等级',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => {
        const colors = { '高': '#f5222d', '中': '#fa8c16', '低': '#52c41a' };
        return <Tag color={colors[text as keyof typeof colors]}>{text}敏感度</Tag>;
      }
    },
    {
      title: '概率阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (value: number, _: SensitivityLevel, index: number) => (
        <InputNumber
          value={value}
          min={0}
          max={1}
          step={0.01}
          precision={2}
          style={{ width: '100%' }}
          onChange={(newValue) => {
            if (newValue !== null) {
              const newLevels = [...editingLevels];
              newLevels[index] = { ...newLevels[index], threshold: newValue };
              setEditingLevels(newLevels);
            }
          }}
        />
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!config) {
    return <div>加载配置失败</div>;
  }

  const sensitivityLevels = getSensitivityLevels();

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>
              <InfoCircleOutlined style={{ marginRight: 8 }} />
              敏感度阈值配置
            </Title>
            <Paragraph type="secondary">
              配置检测结果的敏感度阈值和当前敏感度等级。敏感度等级分为高、中、低三个级别。如果检测结果的置信概率大于等于当前敏感度等级阈值，则将触发风险检测。
            </Paragraph>
          </div>

          {/* 当前配置表格 */}
          <Card
            title="当前敏感度阈值配置"
            extra={
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={handleEdit}
              >
                编辑阈值
              </Button>
            }
          >
            <Table
              columns={columns}
              dataSource={sensitivityLevels}
              rowKey="key"
              pagination={false}
              size="small"
            />
          </Card>

          {/* 当前敏感度等级配置 */}
          <Card title="当前敏感度等级配置">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Alert
                message="配置说明"
                description={
                  <Space direction="vertical" size="small">
                    <Text style={{ fontSize: '12px' }}>
                      • <strong>选择"高敏感度"</strong>：检测分数≥{config.high_sensitivity_threshold}时触发告警，检测最严格，覆盖率最高
                    </Text>
                    <Text style={{ fontSize: '12px' }}>
                      • <strong>选择"中敏感度"</strong>：检测分数≥{config.medium_sensitivity_threshold}时触发告警，平衡准确性和覆盖率
                    </Text>
                    <Text style={{ fontSize: '12px' }}>
                      • <strong>选择"低敏感度"</strong>：检测分数≥{config.low_sensitivity_threshold}时触发告警，准确率最高但可能漏报
                    </Text>
                  </Space>
                }
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Text strong>当前敏感度等级：</Text>
                <Select
                  value={config?.sensitivity_trigger_level}
                  onChange={handleTriggerLevelChange}
                  disabled={saving}
                  style={{ width: 200 }}
                  options={[
                    {
                      value: 'high',
                      label: (
                        <span>
                          <Tag color="#f5222d" style={{ border: 'none', margin: 0 }}>高</Tag>
                          <span style={{ marginLeft: '4px' }}>敏感度</span>
                        </span>
                      )
                    },
                    {
                      value: 'medium',
                      label: (
                        <span>
                          <Tag color="#fa8c16" style={{ border: 'none', margin: 0 }}>中</Tag>
                          <span style={{ marginLeft: '4px' }}>敏感度</span>
                        </span>
                      )
                    },
                    {
                      value: 'low',
                      label: (
                        <span>
                          <Tag color="#52c41a" style={{ border: 'none', margin: 0 }}>低</Tag>
                          <span style={{ marginLeft: '4px' }}>敏感度</span>
                        </span>
                      )
                    }
                  ]}
                />
              </div>

              <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px', border: '1px dashed #d9d9d9' }}>
                <Text style={{ fontSize: '12px', color: '#666' }}>
                  <strong>当前检测规则：</strong>
                  {config?.sensitivity_trigger_level === 'high' && `检测结果的置信概率≥${config.high_sensitivity_threshold}时触发告警，检测最严格`}
                  {config?.sensitivity_trigger_level === 'medium' && `检测结果的置信概率≥${config.medium_sensitivity_threshold}时触发告警，平衡检测`}
                  {config?.sensitivity_trigger_level === 'low' && `检测结果的置信概率≥${config.low_sensitivity_threshold}时触发告警，检测最宽松`}
                </Text>
              </div>
            </Space>
          </Card>

          {/* 编辑模态框 */}
          <Modal
            title="编辑敏感度阈值配置"
            open={editModalVisible}
            onCancel={() => setEditModalVisible(false)}
            footer={[
              <Button key="cancel" onClick={() => setEditModalVisible(false)}>
                取消
              </Button>,
              <Button
                key="save"
                type="primary"
                loading={saving}
                onClick={handleSave}
                icon={<CheckOutlined />}
              >
                保存
              </Button>
            ]}
            width={800}
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Alert
                message="编辑说明"
                description={
                  <Space direction="vertical" size="small">
                    <Text style={{ fontSize: '12px' }}>
                      • 概率阈值不能重叠，必须按照低→中→高的顺序设置
                    </Text>
                    <Text style={{ fontSize: '12px' }}>
                      • 高敏感度阈值必须小于中敏感度阈值，中敏感度阈值必须小于低敏感度阈值
                    </Text>
                  </Space>
                }
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Table
                columns={editColumns}
                dataSource={editingLevels}
                rowKey="key"
                pagination={false}
                size="small"
              />
            </Space>
          </Modal>
        </Space>
      </Card>
    </div>
  );
};

export default SensitivityThresholdManagement;