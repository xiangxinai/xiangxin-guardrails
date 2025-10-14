import React from 'react';
import { Alert } from 'antd';
import { useTranslation } from 'react-i18next';
import { useConfigContext } from '../../pages/Config/Config';

interface ApplicationConfigWrapperProps {
  children: React.ReactNode;
}

/**
 * Application Config Wrapper Component
 *
 * Wraps configuration pages and shows an alert when no application is selected.
 * Use this wrapper for all configuration pages that need application context.
 *
 * Usage:
 * ```tsx
 * const MyConfigPage = () => {
 *   const { selectedApplicationId } = useConfigContext();
 *
 *   return (
 *     <ApplicationConfigWrapper>
 *       {selectedApplicationId && (
 *         // Your config page content here
 *       )}
 *     </ApplicationConfigWrapper>
 *   );
 * };
 * ```
 */
const ApplicationConfigWrapper: React.FC<ApplicationConfigWrapperProps> = ({ children }) => {
  const { t } = useTranslation();
  const { selectedApplicationId } = useConfigContext();

  if (!selectedApplicationId) {
    return (
      <Alert
        message={t('applicationSelector.noApplications')}
        description={t('applicationSelector.noApplicationsDesc')}
        type="info"
        showIcon
      />
    );
  }

  return <>{children}</>;
};

export default ApplicationConfigWrapper;
