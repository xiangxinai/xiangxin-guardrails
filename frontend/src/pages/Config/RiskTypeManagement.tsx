import React, { useState, useEffect } from 'react';
import { Card, Switch, message, Spin, Typography, Divider, Space, Row, Col } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { getRiskConfig, updateRiskConfig } from '../../services/api';

const { Title, Text } = Typography;

interface RiskTypeConfig {
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
}

// 风险类型定义 - 按风险等级排序（高风险 > 中风险 > 低风险）
const RISK_TYPES = [
  // 高风险
  { key: 's2_enabled', label: 'S2 - 敏感政治话题', level: '高风险', color: '#f5222d', priority: 1 },
  { key: 's3_enabled', label: 'S3 - 损害国家形象', level: '高风险', color: '#f5222d', priority: 1 },
  { key: 's5_enabled', label: 'S5 - 暴力犯罪', level: '高风险', color: '#f5222d', priority: 1 },
  { key: 's9_enabled', label: 'S9 - 提示词攻击', level: '高风险', color: '#f5222d', priority: 1 },
  // 中风险
  { key: 's1_enabled', label: 'S1 - 一般政治话题', level: '中风险', color: '#fa8c16', priority: 2 },
  { key: 's4_enabled', label: 'S4 - 伤害未成年人', level: '中风险', color: '#fa8c16', priority: 2 },
  { key: 's6_enabled', label: 'S6 - 违法犯罪', level: '中风险', color: '#fa8c16', priority: 2 },
  { key: 's7_enabled', label: 'S7 - 色情', level: '中风险', color: '#fa8c16', priority: 2 },
  // 低风险
  { key: 's8_enabled', label: 'S8 - 歧视内容', level: '低风险', color: '#52c41a', priority: 3 },
  { key: 's10_enabled', label: 'S10 - 辱骂', level: '低风险', color: '#52c41a', priority: 3 },
  { key: 's11_enabled', label: 'S11 - 侵犯个人隐私', level: '低风险', color: '#52c41a', priority: 3 },
  { key: 's12_enabled', label: 'S12 - 商业违法违规', level: '低风险', color: '#52c41a', priority: 3 },
];

const RiskTypeManagement: React.FC = () => {
  const [config, setConfig] = useState<RiskTypeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadRiskConfig();
  }, []);

  const loadRiskConfig = async () => {
    try {
      setLoading(true);
      const data = await getRiskConfig();
      setConfig(data);
    } catch (error) {
      message.error('加载风险类型配置失败');
      console.error('Failed to load risk config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (key: keyof RiskTypeConfig, checked: boolean) => {
    if (!config) return;

    try {
      setSaving(true);
      const newConfig = { ...config, [key]: checked };
      
      await updateRiskConfig(newConfig);
      setConfig(newConfig);
      
      const riskType = RISK_TYPES.find(type => type.key === key);
      message.success(`${riskType?.label} ${checked ? '已启用' : '已禁用'}`);
    } catch (error) {
      message.error('更新配置失败');
      console.error('Failed to update risk config:', error);
    } finally {
      setSaving(false);
    }
  };

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

  const enabledCount = Object.values(config).filter(Boolean).length;
  const totalCount = Object.keys(config).length;

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>
              <InfoCircleOutlined style={{ marginRight: 8 }} />
              风险类型开关配置
            </Title>
            <Text type="secondary">
              控制各类风险检测的启用状态。关闭某个风险类型后，模型检测到该类型时将被视为安全通过。
              <br />
              当前启用: {enabledCount}/{totalCount} 个风险类型
            </Text>
          </div>

          <Divider />

          {/* 按风险等级分组显示 */}
          {[
            { level: '高风险', priority: 1, bgColor: '#fff2f0', borderColor: '#ffccc7' },
            { level: '中风险', priority: 2, bgColor: '#fff7e6', borderColor: '#ffd591' },
            { level: '低风险', priority: 3, bgColor: '#f6ffed', borderColor: '#d9f7be' }
          ].map((group) => {
            const groupRiskTypes = RISK_TYPES.filter(type => type.priority === group.priority);
            return (
              <div key={group.level} style={{ marginBottom: '24px' }}>
                <div 
                  style={{ 
                    padding: '12px 16px',
                    backgroundColor: group.bgColor,
                    border: `1px solid ${group.borderColor}`,
                    borderRadius: '8px',
                    marginBottom: '16px'
                  }}
                >
                  <Text strong style={{ fontSize: '16px', color: '#262626' }}>
                    {group.level} ({groupRiskTypes.length}项)
                  </Text>
                </div>
                <Row gutter={[16, 16]}>
                  {groupRiskTypes.map((riskType) => (
                    <Col xs={24} sm={12} md={8} lg={6} key={riskType.key}>
                      <Card 
                        size="small" 
                        style={{ 
                          borderColor: config[riskType.key as keyof RiskTypeConfig] ? riskType.color : '#d9d9d9',
                          backgroundColor: config[riskType.key as keyof RiskTypeConfig] ? '#fafafa' : '#f5f5f5'
                        }}
                      >
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text strong style={{ fontSize: '14px' }}>
                              {riskType.label.split(' - ')[1]}
                            </Text>
                            <Switch
                              checked={config[riskType.key as keyof RiskTypeConfig]}
                              onChange={(checked) => handleToggle(riskType.key as keyof RiskTypeConfig, checked)}
                              loading={saving}
                              size="small"
                            />
                          </div>
                          <Text style={{ fontSize: '12px', color: '#666' }}>
                            {riskType.label.split(' - ')[0]}
                          </Text>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text 
                              style={{ 
                                fontSize: '11px', 
                                color: riskType.color, 
                                fontWeight: 'bold' 
                              }}
                            >
                              {riskType.level}
                            </Text>
                            <Text 
                              style={{ 
                                fontSize: '11px', 
                                color: config[riskType.key as keyof RiskTypeConfig] ? '#52c41a' : '#ff4d4f' 
                              }}
                            >
                              {config[riskType.key as keyof RiskTypeConfig] ? '启用' : '禁用'}
                            </Text>
                          </div>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>
            );
          })}

          <Divider />

          <Card size="small" style={{ backgroundColor: '#f6ffed', borderColor: '#b7eb8f' }}>
            <Space direction="vertical" size="small">
              <Text style={{ fontSize: '13px', fontWeight: 'bold', color: '#389e0d' }}>
                ⚠️ 重要提示
              </Text>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                • 禁用风险类型后，相应的内容将不再被拦截，请谨慎操作
              </Text>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                • 建议保持高风险类型（S2、S3、S5、S9）始终启用
              </Text>
              <Text style={{ fontSize: '12px', color: '#666' }}>
                • 配置更改会立即生效，影响后续的检测请求
              </Text>
            </Space>
          </Card>
        </Space>
      </Card>
    </div>
  );
};

export default RiskTypeManagement;