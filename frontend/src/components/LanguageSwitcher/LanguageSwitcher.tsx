import React from 'react';
import { GlobalOutlined } from '@ant-design/icons';
import { Dropdown, MenuProps } from 'antd';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('i18nextLng', lang);
    window.location.reload();
  };

  const items: MenuProps['items'] = [
    {
      key: 'en',
      label: 'English',
      onClick: () => handleLanguageChange('en'),
    },
    {
      key: 'zh',
      label: '中文',
      onClick: () => handleLanguageChange('zh'),
    },
  ];

  return (
    <Dropdown menu={{ items }} placement="bottomRight">
      <div style={{ cursor: 'pointer', padding: '0 12px' }}>
        <GlobalOutlined style={{ fontSize: '16px' }} />
        <span style={{ marginLeft: '8px' }}>
          {i18n.language === 'zh' ? '中文' : 'English'}
        </span>
      </div>
    </Dropdown>
  );
};

export default LanguageSwitcher;
