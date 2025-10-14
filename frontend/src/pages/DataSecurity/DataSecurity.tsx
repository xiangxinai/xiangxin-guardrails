import React from 'react';
import { Card, Alert, Typography, Space, Tag, Collapse } from 'antd';
import { SafetyOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import EntityTypeManagement from './EntityTypeManagement';

const { Paragraph, Text } = Typography;

const DataSecurity: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Card
        title={
          <Space>
            <SafetyOutlined />
<<<<<<< HEAD
            <span>{t('dataSecurity.dataLeakPrevention')}</span>
=======
            <span>{t('data.title')}</span>
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
          </Space>
        }
        bordered={false}
      >
        <Alert
          message={
            <Space>
              <InfoCircleOutlined />
<<<<<<< HEAD
              <Text>{t('dataSecurity.dataLeakPreventionDesc')}</Text>
=======
              <Text>{t('data.description')} <Tag color="blue">{t('data.descriptionHighlight')}</Tag></Text>
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
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
<<<<<<< HEAD
              label: <Text strong style={{ fontSize: 14 }}>💡 {t('dataSecurity.functionalityGuide')}</Text>,
              children: (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Text strong style={{ fontSize: 13 }}>📥 {t('dataSecurity.inputDataPrevention')}</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      {t('dataSecurity.inputDataPreventionDesc')}
                    </Paragraph>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>{t('dataSecurity.enterpriseDeployment')}</li>
                      <li>{t('dataSecurity.publicService')}</li>
=======
              label: <Text strong style={{ fontSize: 14 }}>💡 {t('data.entityManagementDesc')}</Text>,
              children: (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Text strong style={{ fontSize: 13 }}>📥 {t('data.inputProtectionTitle')}</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      {t('data.inputProtectionDesc')}
                    </Paragraph>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>{t('data.enterpriseScenario')}</li>
                      <li>{t('data.publicServiceScenario')}</li>
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
                    </ul>
                  </div>

                  <div>
<<<<<<< HEAD
                    <Text strong style={{ fontSize: 13 }}>📤 {t('dataSecurity.outputDataPrevention')}</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      {t('dataSecurity.outputDataPreventionDesc')}
                    </Paragraph>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>{t('dataSecurity.enterpriseInternal')}</li>
                      <li>{t('dataSecurity.publicServiceOutput')}</li>
=======
                    <Text strong style={{ fontSize: 13 }}>📤 {t('data.outputProtectionTitle')}</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      {t('data.outputProtectionDesc')}
                    </Paragraph>
                    <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>{t('data.outputEnterpriseScenario')}</li>
                      <li>{t('data.outputPublicServiceScenario')}</li>
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
                    </ul>
                  </div>

                  <div>
<<<<<<< HEAD
                    <Text strong style={{ fontSize: 13 }}>📋 {t('sensitivity.usageSteps')}</Text>
                    <ol style={{ marginTop: 4, marginBottom: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li>{t('sensitivity.configEntityTypes')}</li>
                      <li>{t('sensitivity.setRecognitionRules')}</li>
                      <li>{t('sensitivity.selectDesensitizationMethod')}</li>
                      <li>{t('sensitivity.configDetectionScope')}</li>
=======
                    <Text strong style={{ fontSize: 13 }}>📋 {t('data.entityManagementTitle')}</Text>
                    <Paragraph style={{ marginTop: 4, marginBottom: 8, fontSize: 13 }}>
                      {t('data.entityManagementDesc')}
                    </Paragraph>
                    <ol style={{ marginTop: 4, marginBottom: 0, paddingLeft: 20, fontSize: 12 }}>
                      <li><Text strong>{t('data.addType')}</Text>：{t('data.entityManagementDesc')}</li>
                      <li><Text strong>{t('data.pattern')}</Text>：Define patterns using regular expressions</li>
                      <li><Text strong>{t('data.desensitization')}</Text>：Select appropriate desensitization methods</li>
                      <li><Text strong>{t('data.actions')}</Text>：Configure input/output detection scope</li>
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
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
