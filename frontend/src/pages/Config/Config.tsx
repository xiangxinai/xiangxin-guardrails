import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import BlacklistManagement from './BlacklistManagement';
import WhitelistManagement from './WhitelistManagement';
import ResponseTemplateManagement from './ResponseTemplateManagement';
import RiskTypeManagement from './RiskTypeManagement';
import ProxyModelManagement from './ProxyModelManagement';
import SensitivityThresholdManagement from './SensitivityThresholdManagement';

const Config: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const getActiveKey = () => {
    const path = location.pathname;
    if (path.includes('/blacklist')) return 'blacklist';
    if (path.includes('/whitelist')) return 'whitelist';
    if (path.includes('/responses')) return 'responses';
    if (path.includes('/risk-types')) return 'risk-types';
    if (path.includes('/sensitivity-thresholds')) return 'sensitivity-thresholds';
    if (path.includes('/proxy-models')) return 'proxy-models';
    return 'risk-types';
  };

  const handleTabChange = (key: string) => {
    // 确保在以 /platform 为前缀的基础路径下导航，避免刷新后丢失平台前缀
    navigate(`/config/${key}`);
  };

  const items = [
    {
      key: 'risk-types',
      label: '风险类型配置',
      children: <RiskTypeManagement />,
    },
    {
      key: 'sensitivity-thresholds',
      label: '敏感度阈值管理',
      children: <SensitivityThresholdManagement />,
    },
    {
      key: 'blacklist',
      label: '黑名单管理',
      children: <BlacklistManagement />,
    },
    {
      key: 'whitelist',
      label: '白名单管理',
      children: <WhitelistManagement />,
    },
    {
      key: 'responses',
      label: '代答库管理',
      children: <ResponseTemplateManagement />,
    },
    {
      key: 'proxy-models',
      label: '代理模型配置',
      children: <ProxyModelManagement />,
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>防护配置</h2>
      
      <Tabs
        activeKey={getActiveKey()}
        items={items}
        onChange={handleTabChange}
      />
    </div>
  );
};

export default Config;