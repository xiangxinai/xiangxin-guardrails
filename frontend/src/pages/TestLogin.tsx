import React, { useState } from 'react';
import axios from 'axios';

const TestLogin: React.FC = () => {
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testLogin = async () => {
    setLoading(true);
    setResult('Testing...');

    try {
      // 获取base URL，与其他服务保持一致
      const getBaseURL = () => {
        if (import.meta.env.DEV) {
          return '';
        }
        return '/platform';
      };
      
      // 使用相对路径通过代理访问
      const response = await axios.post(`${getBaseURL()}/api/v1/auth/login`, {
        username: 'admin',
        password: 'xiangxin@2024'
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setResult(`Success: ${JSON.stringify(response.data, null, 2)}`);
    } catch (error: any) {
      console.error('Login test error:', error);
      const errorDetails = {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers,
          data: error.config?.data
        }
      };
      setResult(`Error: ${JSON.stringify(errorDetails, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  const testAuthService = async () => {
    setLoading(true);
    setResult('Testing Auth Service...');

    try {
      // 测试认证服务
      const { authService } = await import('../services/auth');
      const response = await authService.login({
        username: 'admin',
        password: 'xiangxin@2024'
      });
      setResult(`Auth Service Success: ${JSON.stringify(response, null, 2)}`);
    } catch (error: any) {
      console.error('Auth service test error:', error);
      setResult(`Auth Service Error: ${JSON.stringify(error, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Login Test Page</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button onClick={testLogin} disabled={loading}>
          Test Direct API Call
        </button>
        <button onClick={testAuthService} disabled={loading} style={{ marginLeft: '10px' }}>
          Test Auth Service
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <strong>Environment:</strong>
        <br />
        VITE_API_URL: {import.meta.env.VITE_API_URL || 'undefined'}
      </div>

      <pre style={{ 
        background: '#f5f5f5', 
        padding: '10px', 
        whiteSpace: 'pre-wrap',
        maxHeight: '400px',
        overflow: 'auto'
      }}>
        {result}
      </pre>
    </div>
  );
};

export default TestLogin;