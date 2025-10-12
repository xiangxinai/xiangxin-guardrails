import React from 'react';
import { Tabs } from 'antd';
import { useTranslation } from 'react-i18next';
import {
  SafetyCertificateOutlined,
  DashboardOutlined,
  StopOutlined,
  CheckCircleOutlined,
  BookOutlined,
  MessageOutlined,
  UserDeleteOutlined,
  SecurityScanOutlined,
} from '@ant-design/icons';
import RiskTypeManagement from './RiskTypeManagement';
import SensitivityThresholdManagement from './SensitivityThresholdManagement';
import BlacklistManagement from './BlacklistManagement';
import WhitelistManagement from './WhitelistManagement';
import KnowledgeBaseManagement from './KnowledgeBaseManagement';
import ResponseTemplateManagement from './ResponseTemplateManagement';
import BanPolicy from './BanPolicy';
import EntityTypeManagement from '../DataSecurity/EntityTypeManagement';

/**
 * Config Center - All configuration options in tabs
 *
 * This page displays all configuration options as tabs, allowing users to
 * easily navigate between different configuration sections.
 */
const Config: React.FC = () => {
  const { t } = useTranslation();

  const items = [
    {
      key: 'risk-types',
      label: (
        <span>
          <SafetyCertificateOutlined /> {t('config.riskTypes') || 'Risk Types'}
        </span>
      ),
      children: <RiskTypeManagement />,
    },
    {
      key: 'sensitivity',
      label: (
        <span>
          <DashboardOutlined /> {t('config.sensitivity') || 'Sensitivity Thresholds'}
        </span>
      ),
      children: <SensitivityThresholdManagement />,
    },
    {
      key: 'blacklist',
      label: (
        <span>
          <StopOutlined /> {t('config.blacklist') || 'Blacklist'}
        </span>
      ),
      children: <BlacklistManagement />,
    },
    {
      key: 'whitelist',
      label: (
        <span>
          <CheckCircleOutlined /> {t('config.whitelist') || 'Whitelist'}
        </span>
      ),
      children: <WhitelistManagement />,
    },
    {
      key: 'knowledge-base',
      label: (
        <span>
          <BookOutlined /> {t('config.knowledgeBase') || 'Knowledge Base'}
        </span>
      ),
      children: <KnowledgeBaseManagement />,
    },
    {
      key: 'response-templates',
      label: (
        <span>
          <MessageOutlined /> {t('config.responseTemplates') || 'Response Templates'}
        </span>
      ),
      children: <ResponseTemplateManagement />,
    },
    {
      key: 'data-security',
      label: (
        <span>
          <SecurityScanOutlined /> {t('config.dataSecurity') || 'Data Security'}
        </span>
      ),
      children: <EntityTypeManagement />,
    },
    {
      key: 'ban-policy',
      label: (
        <span>
          <UserDeleteOutlined /> {t('config.banPolicy') || 'Ban Policy'}
        </span>
      ),
      children: <BanPolicy />,
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>{t('config.title') || 'Configuration Center'}</h2>
      <Tabs
        defaultActiveKey="risk-types"
        items={items}
        tabPosition="top"
        size="large"
      />
    </div>
  );
};

export default Config;
