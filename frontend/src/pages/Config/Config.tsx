import React, { useState, createContext, useContext } from 'react';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ApplicationSelector from '../../components/ApplicationSelector/ApplicationSelector';
import BlacklistManagement from './BlacklistManagement';
import WhitelistManagement from './WhitelistManagement';
import ResponseTemplateManagement from './ResponseTemplateManagement';
import KnowledgeBaseManagement from './KnowledgeBaseManagement';
import RiskTypeManagement from './RiskTypeManagement';
import SensitivityThresholdManagement from './SensitivityThresholdManagement';
import DataSecurity from '../DataSecurity';
import BanPolicy from './BanPolicy';
import type { Application } from '../../types';

// Create context for selected application across all config tabs
interface ConfigContextType {
  selectedApplicationId: string | undefined;
  selectedApplication: Application | undefined;
}

const ConfigContext = createContext<ConfigContextType>({
  selectedApplicationId: undefined,
  selectedApplication: undefined,
});

export const useConfigContext = () => useContext(ConfigContext);

const Config: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedApplicationId, setSelectedApplicationId] = useState<string>();
  const [selectedApplication, setSelectedApplication] = useState<Application>();

  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/blacklist')) return 'blacklist';
    if (path.includes('/whitelist')) return 'whitelist';
    if (path.includes('/responses')) return 'responses';
    if (path.includes('/knowledge-bases')) return 'knowledge-bases';
    if (path.includes('/risk-types')) return 'risk-types';
    if (path.includes('/sensitivity-thresholds')) return 'sensitivity-thresholds';
    if (path.includes('/data-security')) return 'data-security';
    if (path.includes('/ban-policy')) return 'ban-policy';
    return 'risk-types';
  };

  const handleTabChange = (key: string) => {
    // Ensure navigation under base path with /platform prefix, avoid losing platform prefix after refresh
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
  ];

  const handleApplicationChange = (applicationId: string, application: Application | undefined) => {
    setSelectedApplicationId(applicationId);
    setSelectedApplication(application);
  };

  return (
    <ConfigContext.Provider
      value={{
        selectedApplicationId,
        selectedApplication,
      }}
    >
      <div>
        <h2 style={{ marginBottom: 24 }}>{t('config.title')}</h2>

        <ApplicationSelector
          value={selectedApplicationId}
          onChange={handleApplicationChange}
          style={{ marginBottom: 24 }}
        />

        <Tabs
          activeKey={getActiveKey()}
          items={items}
          onChange={handleTabChange}
        />
      </div>
    </ConfigContext.Provider>
  );
};

export default Config;