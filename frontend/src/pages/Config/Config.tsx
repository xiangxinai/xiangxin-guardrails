import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Tabs } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
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
      label: '风险类型',
      children: <RiskTypeManagement />,
    },
    {
      key: 'sensitivity-thresholds',
      label: '敏感度阈值',
      children: <SensitivityThresholdManagement />,
    },
    {
      key: 'data-security',
      label: '数据防泄漏',
      children: <DataSecurity />,
    },
    {
      key: 'ban-policy',
      label: '封禁策略',
      children: <BanPolicy />,
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
      label: '拒答答案库',
      children: <ResponseTemplateManagement />,
    },
    {
      key: 'knowledge-bases',
      label: '代答知识库',
      children: <KnowledgeBaseManagement />,
    },
    {
      key: 'proxy-models',
      label: '安全网关配置',
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