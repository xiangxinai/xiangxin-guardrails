import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { MailOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import '../Register/Register.css'; // 使用相同的样式

const { Title, Text } = Typography;

interface VerifyFormData {
  email: string;
  verificationCode: string;
}

interface ResendFormData {
  email: string;
}

const Verify: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const initialEmail = searchParams.get('email') || '';

  // 倒计时处理
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [countdown]);

  const handleVerify = async (values: VerifyFormData) => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/v1/users/verify-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: values.email,
          verification_code: values.verificationCode,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '验证失败');
      }

      message.success('邮箱验证成功！即将跳转到登录页面。');
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (error: any) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async (email: string) => {
    try {
      setResendLoading(true);
      
      const response = await fetch('/api/v1/users/resend-verification-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '重发失败');
      }

      setCountdown(60); // 设置60秒倒计时
      message.success('验证码已重新发送！请检查您的邮箱。');
    } catch (error: any) {
      message.error(error.message);
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-content">
        <Card className="register-card">
          <div className="register-header">
            <Title level={2} className="register-title">
              象信AI安全护栏
            </Title>
            <Text type="secondary" className="register-subtitle">
              邮箱验证 / 重发验证码
            </Text>
          </div>

          <div className="register-form">
            <Form
              name="verify"
              onFinish={handleVerify}
              autoComplete="off"
              layout="vertical"
              size="large"
              initialValues={{ email: initialEmail }}
            >
              <Form.Item
                name="email"
                label="邮箱地址"
                rules={[
                  { required: true, message: '请输入邮箱地址' },
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="请输入注册时使用的邮箱地址"
                  autoComplete="email"
                />
              </Form.Item>

              <Form.Item
                name="verificationCode"
                label="验证码"
                rules={[
                  { required: true, message: '请输入验证码' },
                  { len: 6, message: '验证码为6位数字' },
                ]}
              >
                <Input
                  prefix={<SafetyOutlined />}
                  placeholder="6位验证码"
                  maxLength={6}
                  style={{ textAlign: 'center', fontSize: '18px', letterSpacing: '4px' }}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                  className="verify-button"
                >
                  验证邮箱
                </Button>
              </Form.Item>

              <Form.Item>
                <Space direction="vertical" style={{ width: '100%' }} align="center">
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary">没有收到验证码？</Text>
                    <Form.Item
                      noStyle
                      shouldUpdate={(prevValues, currentValues) => prevValues.email !== currentValues.email}
                    >
                      {({ getFieldValue }) => (
                        <Button
                          type="link"
                          onClick={() => handleResendCode(getFieldValue('email'))}
                          loading={resendLoading}
                          disabled={countdown > 0 || !getFieldValue('email')}
                          style={{ padding: '0 4px' }}
                        >
                          {countdown > 0 ? `重新发送 (${countdown}s)` : '重新发送验证码'}
                        </Button>
                      )}
                    </Form.Item>
                  </div>
                  
                  <Space>
                    <Link to="/register">重新注册</Link>
                    <Text type="secondary">|</Text>
                    <Link to="/login">已有账户，直接登录</Link>
                  </Space>
                </Space>
              </Form.Item>
            </Form>
          </div>

          <div className="register-footer">
            <Space direction="vertical" align="center">
              <Text type="secondary" style={{ fontSize: '12px' }}>
                © 2024 象信AI. All rights reserved.
              </Text>
            </Space>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Verify;