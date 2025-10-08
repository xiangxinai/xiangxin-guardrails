import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { AuthProvider } from './contexts/AuthContext'
import App from './App'
import './i18n' // Initialize i18n
import { initializeLanguage } from './utils/languageDetector'
import './index.css'

// Initialize language detection and render app
initializeLanguage().then((detectedLang) => {
  const antdLocale = detectedLang === 'zh' ? zhCN : enUS;

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ConfigProvider locale={antdLocale}>
        <BrowserRouter basename="/platform">
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ConfigProvider>
    </React.StrictMode>,
  )
})