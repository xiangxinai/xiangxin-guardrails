import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Space, Alert } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import './Login.css';

const { Title, Text } = Typography;

interface LoginFormData {
  email: string;
  password: string;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [showVerificationAlert, setShowVerificationAlert] = useState(false);
  const [unverifiedEmail, setUnverifiedEmail] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (values: LoginFormData) => {
    try {
      setLoading(true);
      setShowVerificationAlert(false); // 重置状态
      await login(values.email, values.password);
      message.success('登录成功');
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Login error:', error);
      console.error('Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        config: error.config
      });
      
      const errorMessage = error.response?.data?.detail || '登录失败，请检查邮箱和密码';
      
      // 检查是否是账号未激活错误
      if (error.response?.status === 403 && errorMessage.includes('not activated')) {
        setUnverifiedEmail(values.email);
        setShowVerificationAlert(true);
      } else {
        message.error(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-content">
        <Card className="login-card">
          <div className="login-header">
            <Title level={2} className="login-title">
              象信AI安全护栏
            </Title>
            <Text type="secondary" className="login-subtitle">
              账号登录
            </Text>
          </div>

          {showVerificationAlert && (
            <Alert
              message="账号需要验证"
              description={
                <div>
                  <p>您的账号 <strong>{unverifiedEmail}</strong> 尚未验证邮箱。</p>
                  <Space>
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => navigate(`/verify?email=${encodeURIComponent(unverifiedEmail)}`)}
                    >
                      前往验证页面
                    </Button>
                    <span>|</span>
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => setShowVerificationAlert(false)}
                    >
                      关闭提醒
                    </Button>
                  </Space>
                </div>
              }
              type="warning"
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}

          <Form
            name="login"
            onFinish={handleSubmit}
            autoComplete="off"
            layout="vertical"
            size="large"
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="邮箱地址"
                autoComplete="email"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                className="login-button"
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          <div className="login-footer">
            <Space direction="vertical" align="center">
              <Space>
                <Text type="secondary">
                  没有账户？ <Link to="/register">立即注册</Link>
                </Text>
                <Text type="secondary">|</Text>
                <Text type="secondary">
                  需要验证邮箱？ <Link to="/verify">验证页面</Link>
                </Text>
              </Space>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                © 2025 象信AI. All rights reserved.
              </Text>
            </Space>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Login;