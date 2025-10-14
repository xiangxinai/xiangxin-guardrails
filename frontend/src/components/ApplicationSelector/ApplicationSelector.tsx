import React, { useState, useEffect } from 'react';
import { Select, Space, Typography, message, Alert } from 'antd';
import { AppstoreOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { applicationApi } from '../../services/api';
import type { Application } from '../../types';

const { Text } = Typography;

interface ApplicationSelectorProps {
  value?: string;
  onChange?: (applicationId: string, application: Application | undefined) => void;
  style?: React.CSSProperties;
}

/**
 * Application Selector Component
 * Reusable component for selecting applications across configuration pages
 */
const ApplicationSelector: React.FC<ApplicationSelectorProps> = ({
  value,
  onChange,
  style,
}) => {
  const { t } = useTranslation();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAppId, setSelectedAppId] = useState<string | undefined>(value);

  useEffect(() => {
    fetchApplications();
  }, []);

  useEffect(() => {
    setSelectedAppId(value);
  }, [value]);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await applicationApi.list();
      const activeApps = data.filter((app) => app.is_active);
      setApplications(activeApps);

      // Auto-select first application if none selected
      if (!value && activeApps.length > 0) {
        const firstApp = activeApps[0];
        setSelectedAppId(firstApp.id);
        onChange?.(firstApp.id, firstApp);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || t('applications.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (appId: string) => {
    setSelectedAppId(appId);
    const selectedApp = applications.find((app) => app.id === appId);
    onChange?.(appId, selectedApp);
  };

  if (applications.length === 0 && !loading) {
    return (
      <Alert
        message={t('applicationSelector.noApplications')}
        description={t('applicationSelector.noApplicationsDesc')}
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />
    );
  }

  return (
    <Space direction="vertical" size="small" style={{ width: '100%', ...style }}>
      <Space>
        <AppstoreOutlined style={{ fontSize: 16 }} />
        <Text strong>{t('applicationSelector.selectApplication')}:</Text>
      </Space>
      <Select
        value={selectedAppId}
        onChange={handleChange}
        loading={loading}
        placeholder={t('applicationSelector.placeholder')}
        style={{ minWidth: 300 }}
        options={applications.map((app) => ({
          label: app.name,
          value: app.id,
        }))}
      />
      <Text type="secondary" style={{ fontSize: 12 }}>
        {t('applicationSelector.description')}
      </Text>
    </Space>
  );
};

export default ApplicationSelector;
