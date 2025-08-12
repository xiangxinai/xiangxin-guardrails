import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, message, Space, Steps } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import './Register.css';

const { Title, Text } = Typography;
const { Step } = Steps;

interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

interface VerifyFormData {
  verificationCode: string;
}

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [userEmail, setUserEmail] = useState('');
  const [countdown, setCountdown] = useState(0);
  const navigate = useNavigate();

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

  const handleResendCode = async () => {
    try {
      setResendLoading(true);
      
      const response = await fetch('/api/v1/users/resend-verification-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
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

  const handleRegister = async (values: RegisterFormData) => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/v1/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: values.email,
          password: values.password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '注册失败');
      }

      setUserEmail(values.email);
      setCurrentStep(1);
      setCountdown(60); // 设置初始倒计时
      message.success('注册成功！请检查您的邮箱获取验证码。');
    } catch (error: any) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (values: VerifyFormData) => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/v1/users/verify-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
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

  const renderRegisterForm = () => (
    <Form
      name="register"
      onFinish={handleRegister}
      autoComplete="off"
      layout="vertical"
      size="large"
    >
      <Form.Item
        name="email"
        rules={[
          { required: true, message: '请输入邮箱地址' },
          { type: 'email', message: '请输入有效的邮箱地址' },
        ]}
      >
        <Input
          prefix={<MailOutlined />}
          placeholder="邮箱地址"
          autoComplete="email"
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 8, message: '密码长度至少8位' },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="密码（至少8位）"
          autoComplete="new-password"
        />
      </Form.Item>

      <Form.Item
        name="confirmPassword"
        dependencies={['password']}
        rules={[
          { required: true, message: '请确认密码' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('两次输入的密码不一致'));
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="确认密码"
          autoComplete="new-password"
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          block
          className="register-button"
        >
          注册账户
        </Button>
      </Form.Item>
    </Form>
  );

  const renderVerifyForm = () => (
    <Form
      name="verify"
      onFinish={handleVerify}
      autoComplete="off"
      layout="vertical"
      size="large"
    >
      <div style={{ marginBottom: 24, textAlign: 'center' }}>
        <Text type="secondary">
          验证码已发送到 <strong>{userEmail}</strong>
        </Text>
        <br />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          您也可以稍后在 <Link to={`/verify?email=${encodeURIComponent(userEmail)}`}>验证页面</Link> 完成验证
        </Text>
      </div>

      <Form.Item
        name="verificationCode"
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
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">没有收到验证码？</Text>
            <Button
              type="link"
              onClick={handleResendCode}
              loading={resendLoading}
              disabled={countdown > 0}
              style={{ padding: '0 4px' }}
            >
              {countdown > 0 ? `重新发送 (${countdown}s)` : '重新发送验证码'}
            </Button>
          </div>
          <Button
            type="link"
            onClick={() => setCurrentStep(0)}
            block
          >
            返回重新注册
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );

  return (
    <div className="register-container">
      <div className="register-content">
        <Card className="register-card">
          <div className="register-header">
            <Title level={2} className="register-title">
              象信AI安全护栏
            </Title>
            <Text type="secondary" className="register-subtitle">
              用户注册
            </Text>
          </div>

          <Steps current={currentStep} className="register-steps">
            <Step title="填写信息" description="输入邮箱和密码" />
            <Step title="邮箱验证" description="验证邮箱地址" />
          </Steps>

          <div className="register-form">
            {currentStep === 0 ? renderRegisterForm() : renderVerifyForm()}
          </div>

          <div className="register-footer">
            <Space direction="vertical" align="center">
              <Text type="secondary">
                已有账户？ <Link to="/login">立即登录</Link>
              </Text>
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

export default Register;