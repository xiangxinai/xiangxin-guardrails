import React from 'react';
import { Card, Alert, Typography, Space, Tag, Collapse } from 'antd';
import { SafetyOutlined, InfoCircleOutlined } from '@ant-design/icons';
import EntityTypeManagement from './EntityTypeManagement';

const { Paragraph, Text } = Typography;

const DataSecurity: React.FC = () => {

  return (
    <div>
      <Card
        title={
          <Space>
            <SafetyOutlined />
            <span>敏感数据防泄漏</span>
          </Space>
        }
        bordered={false}
      >
        <Alert
          message={
            <Space>
              <InfoCircleOutlined />
              <Text>通过<Tag color="blue">正则表达式</Tag>识别并脱敏敏感信息，防止个人/企业敏感数据在使用大模型时的泄露风险。</Text>
            </Space>
          }
          type="info"
          showIcon={false}
          style={{ marginBottom: 16 }}
        />

        <Collapse
          ghost
          style={{ marginBottom: 24, background: '#fafafa' }}
          items={[
            {
              key: '1',
              label: <Text strong style={{ fontSize: 14 }}>💡 功能说明与使用指南</Text>,
              children: (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Text strong style={{ fontSize: 13 }}>📥 输入数据防泄漏</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      防止用户提供的敏感数据泄漏给大模型
                    </Paragraph>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>企业内部部署：保护企业内部数据不泄露给外部大模型</li>
                      <li>公共服务：保护用户敏感数据不泄露给服务提供方</li>
                    </ul>
                  </div>

                  <div>
                    <Text strong style={{ fontSize: 13 }}>📤 输出数据防泄漏</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      防止模型输出泄漏敏感数据给用户
                    </Paragraph>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>企业内部部署：防止企业数据泄露给内部用户（越权访问等）</li>
                      <li>公共服务：防止服务方敏感数据泄露给外部用户</li>
                    </ul>
                  </div>

                  <div>
                    <Text strong style={{ fontSize: 13 }}>📋 使用步骤</Text>
                    <ol style={{ marginTop: 4, marginBottom: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li><Text strong>配置实体类型</Text>：定义需要识别的敏感数据类型（如身份证、手机号等）</li>
                      <li><Text strong>设置识别规则</Text>：使用正则表达式定义识别模式</li>
                      <li><Text strong>选择脱敏方法</Text>：选择合适的脱敏方式（替换、掩码、加密等）</li>
                      <li><Text strong>配置检测范围</Text>：选择输入/输出检测</li>
                    </ol>
                  </div>
                </Space>
              ),
            },
          ]}
        />

        <EntityTypeManagement />
      </Card>
    </div>
  );
};

export default DataSecurity;
