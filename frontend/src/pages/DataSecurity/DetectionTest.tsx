import React, { useState } from 'react';
import { Card, Input, Button, Space, Tag, Table, message, Select, Switch, Row, Col } from 'antd';
import { SendOutlined, ClearOutlined } from '@ant-design/icons';
import { dataSecurityApi } from '../../services/api';

const { TextArea } = Input;
const { Option } = Select;

const DetectionTest: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [language, setLanguage] = useState('zh');
  const [anonymize, setAnonymize] = useState(true);

  const handleDetect = async () => {
    if (!inputText.trim()) {
      message.warning('请输入待检测的文本');
      return;
    }

    setLoading(true);
    try {
      const response = await dataSecurityApi.detectSensitiveData({
        text: inputText,
        language,
        anonymize,
      });
      setResult(response);
      message.success('检测完成');
    } catch (error) {
      message.error('检测失败');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setResult(null);
  };

  const entityColumns = [
    {
      title: '实体类型',
      dataIndex: 'entity_type',
      key: 'entity_type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: '识别文本',
      key: 'text',
      render: (_: any, record: any) => {
        if (result?.original_text) {
          return result.original_text.substring(record.start, record.end);
        }
        return '-';
      },
    },
    {
      title: '位置',
      key: 'position',
      render: (_: any, record: any) => `${record.start} - ${record.end}`,
    },
    {
      title: '置信度',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => {
        const percentage = (score * 100).toFixed(1);
        return <Tag color={score > 0.8 ? 'green' : score > 0.5 ? 'orange' : 'red'}>{percentage}%</Tag>;
      },
    },
  ];

  return (
    <div>
      <Row gutter={16}>
        <Col span={24}>
          <Card title="在线检测" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <div style={{ marginBottom: 8 }}>待检测文本：</div>
                <TextArea
                  rows={6}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="请输入待检测的文本，例如：我的手机号是13800138000，邮箱是test@example.com"
                />
              </div>

              <Row gutter={16}>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>语言：</div>
                  <Select value={language} onChange={setLanguage} style={{ width: '100%' }}>
                    <Option value="zh">中文</Option>
                    <Option value="en">英文</Option>
                  </Select>
                </Col>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>是否脱敏：</div>
                  <Switch checked={anonymize} onChange={setAnonymize} checkedChildren="是" unCheckedChildren="否" />
                </Col>
              </Row>

              <Space>
                <Button type="primary" icon={<SendOutlined />} onClick={handleDetect} loading={loading}>
                  开始检测
                </Button>
                <Button icon={<ClearOutlined />} onClick={handleClear}>
                  清空
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      {result && (
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card
              title={
                <span>
                  检测结果
                  <Tag color="green" style={{ marginLeft: 8 }}>
                    检测到 {result.entity_count} 个敏感实体
                  </Tag>
                </span>
              }
              bordered={false}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <div style={{ marginBottom: 8, fontWeight: 'bold' }}>原始文本：</div>
                  <div
                    style={{
                      padding: 12,
                      backgroundColor: '#f5f5f5',
                      borderRadius: 4,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {result.original_text}
                  </div>
                </div>

                {anonymize && (
                  <div>
                    <div style={{ marginBottom: 8, fontWeight: 'bold' }}>脱敏后文本：</div>
                    <div
                      style={{
                        padding: 12,
                        backgroundColor: '#e6f7ff',
                        borderRadius: 4,
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {result.anonymized_text}
                    </div>
                  </div>
                )}

                {result.categories_detected && result.categories_detected.length > 0 && (
                  <div>
                    <div style={{ marginBottom: 8, fontWeight: 'bold' }}>检测到的类别：</div>
                    <Space wrap>
                      {result.categories_detected.map((cat: string) => (
                        <Tag key={cat} color="blue">
                          {cat}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                )}

                {result.entities && result.entities.length > 0 && (
                  <div>
                    <div style={{ marginBottom: 8, fontWeight: 'bold' }}>检测到的实体：</div>
                    <Table
                      columns={entityColumns}
                      dataSource={result.entities}
                      rowKey={(record, index) => `${record.entity_type}-${index}`}
                      pagination={false}
                      size="small"
                    />
                  </div>
                )}
              </Space>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default DetectionTest;
