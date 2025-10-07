import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import BlacklistManagement from './BlacklistManagement';
import WhitelistManagement from './WhitelistManagement';
import ResponseTemplateManagement from './ResponseTemplateManagement';
import KnowledgeBaseManagement from './KnowledgeBaseManagement';
import RiskTypeManagement from './RiskTypeManagement';
import ProxyModelManagement from './ProxyModelManagement';
import SensitivityThresholdManagement from './SensitivityThresholdManagement';
import DataSecurity from '../DataSecurity';
import BanPolicy from './BanPolicy';

const Config: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/blacklist')) return 'blacklist';
    if (path.includes('/whitelist')) return 'whitelist';
    if (path.includes('/responses')) return 'responses';
    if (path.includes('/knowledge-bases')) return 'knowledge-bases';
    if (path.includes('/risk-types')) return 'risk-types';
    if (path.includes('/sensitivity-thresholds')) return 'sensitivity-thresholds';
    if (path.includes('/proxy-models')) return 'proxy-models';
    if (path.includes('/data-security')) return 'data-security';
    if (path.includes('/ban-policy')) return 'ban-policy';
    return 'risk-types';
  };

  const handleTabChange = (key: string) => {
    // 确保在以 /platform 为前缀的基础路径下导航，避免刷新后丢失平台前缀
    navigate(`/config/${key}`);
  };

  const items = [
    {
      key: 'risk-types',
      label: t('config.riskType'),
      children: <RiskTypeManagement />,
    },
    {
      key: 'sensitivity-thresholds',
      label: t('config.sensitivity'),
      children: <SensitivityThresholdManagement />,
    },
    {
      key: 'data-security',
      label: t('config.dataSecurity'),
      children: <DataSecurity />,
    },
    {
      key: 'ban-policy',
      label: t('config.banPolicy'),
      children: <BanPolicy />,
    },
    {
      key: 'blacklist',
      label: t('config.blacklist'),
      children: <BlacklistManagement />,
    },
    {
      key: 'whitelist',
      label: t('config.whitelist'),
      children: <WhitelistManagement />,
    },
    {
      key: 'responses',
      label: t('config.rejectAnswers'),
      children: <ResponseTemplateManagement />,
    },
    {
      key: 'knowledge-bases',
      label: t('config.knowledge'),
      children: <KnowledgeBaseManagement />,
    },
    {
      key: 'proxy-models',
      label: t('config.proxy'),
      children: <ProxyModelManagement />,
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>{t('config.title')}</h2>
      
      <Tabs
        activeKey={getActiveKey()}
        items={items}
        onChange={handleTabChange}
      />
    </div>
  );
};

export default Config;