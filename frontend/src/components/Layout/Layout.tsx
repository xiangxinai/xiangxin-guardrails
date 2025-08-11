import React, { useState, useEffect } from 'react';
import { Layout as AntLayout, Menu, theme, Dropdown, Avatar, Space, Button, Modal, Select, message, Tag } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  FileSearchOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  SwapOutlined,
  ReloadOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { adminApi } from '../../services/api';

const { Header, Sider, Content } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [switchModalVisible, setSwitchModalVisible] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, switchInfo, switchToUser, exitSwitch, refreshSwitchStatus } = useAuth();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  useEffect(() => {
    // 如果是超级管理员，定期检查切换状态
    if (user?.is_super_admin) {
      const interval = setInterval(() => {
        refreshSwitchStatus();
      }, 30000); // 每30秒检查一次
      return () => clearInterval(interval);
    }
  }, [user?.is_super_admin, refreshSwitchStatus]);

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '总览',
    },
    {
      key: '/online-test',
      icon: <ExperimentOutlined />,
      label: '在线测试',
    },
    {
      key: '/results',
      icon: <FileSearchOutlined />,
      label: '检测结果',
    },
    {
      key: '/reports',
      icon: <BarChartOutlined />,
      label: '风险报表',
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: '防护配置',
      children: [
        {
          key: '/config/blacklist',
          label: '黑名单管理',
        },
        {
          key: '/config/whitelist',
          label: '白名单管理',
        },
        {
          key: '/config/responses',
          label: '代答库管理',
        },
      ],
    },
    // 只有超级管理员显示用户管理
    ...(user?.is_super_admin ? [{
      key: '/admin',
      icon: <SettingOutlined />,
      label: '系统管理',
      children: [
        {
          key: '/admin/users',
          label: '用户管理',
        },
        {
          key: '/admin/rate-limits',
          label: '限速配置',
        },
      ],
    }] : []),
    {
      key: '/account',
      icon: <UserOutlined />,
      label: '账号管理',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/config') || path.startsWith('/admin')) {
      return [path];
    }
    if (path === '/' || path === '/') {
      return ['/dashboard'];
    }
    return [path.startsWith('/') ? path : '/platform' + path];
  };

  const getOpenKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/config')) {
      return ['/config'];
    }
    if (path.startsWith('/admin')) {
      return ['/admin'];
    }
    return [];
  };

  const loadUsers = async () => {
    if (!user?.is_super_admin) return;
    
    setLoading(true);
    try {
      const response = await adminApi.getUsers();
      setUsers(response.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchUser = async (userId: string) => {
    try {
      await switchToUser(userId);
      setSwitchModalVisible(false);
      message.success('已切换到用户视角');
      // 刷新当前页面
      window.location.reload();
    } catch (error) {
      console.error('Switch user failed:', error);
      message.error('切换用户失败');
    }
  };

  const handleExitSwitch = async () => {
    try {
      await exitSwitch();
      message.success('已退出用户视角');
      // 刷新当前页面
      window.location.reload();
    } catch (error) {
      console.error('Exit switch failed:', error);
      message.error('退出用户视角失败');
    }
  };

  const showSwitchModal = () => {
    setSwitchModalVisible(true);
    loadUsers();
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div
          style={{
            height: 48,
            margin: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
          onClick={() => navigate('/dashboard')}
        >
          <img 
            src="/platform/xiangxinlogo.png" 
            alt="象信logo" 
            style={{
              height: '100%',
              maxWidth: collapsed ? '32px' : '100%',
              objectFit: 'contain',
            }}
          />
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            padding: 0,
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingRight: 24,
          }}
        >
          <div style={{ paddingLeft: 24, fontSize: 18, fontWeight: 'bold' }}>
            象信AI安全护栏平台
          </div>
          <Space>
            {/* 用户切换状态显示 */}
            {switchInfo.is_switched && (
              <Tag color="orange" style={{ marginRight: 8 }}>
                切换中: {switchInfo.target_user?.email}
              </Tag>
            )}
            
            {/* 超级管理员才显示用户切换按钮 */}
            {user?.is_super_admin && !switchInfo.is_switched && (
              <Button 
                type="link" 
                icon={<SwapOutlined />}
                onClick={showSwitchModal}
                size="small"
              >
                切换用户
              </Button>
            )}
            
            {/* 退出用户切换按钮 */}
            {switchInfo.is_switched && (
              <Button 
                type="link" 
                icon={<ReloadOutlined />}
                onClick={handleExitSwitch}
                size="small"
                danger
              >
                退出切换
              </Button>
            )}
            
            {/* 当前用户名显示 */}
            <span style={{ 
              color: '#1890ff', 
              fontWeight: 500,
              padding: '4px 8px',
              backgroundColor: '#f0f6ff',
              borderRadius: '4px',
              border: '1px solid #d6e4ff'
            }}>
              {user?.email}
              {user?.is_super_admin && <Tag color="red" size="small" style={{ marginLeft: 4 }}>管理员</Tag>}
            </span>
            
            <span style={{ color: '#666' }}>v1.0.0</span>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'account',
                    icon: <UserOutlined />,
                    label: '账号管理',
                    onClick: () => navigate('/account'),
                  },
                  {
                    type: 'divider',
                  },
                  {
                    key: 'logout',
                    icon: <LogoutOutlined />,
                    label: '退出登录',
                    onClick: () => {
                      logout();
                      navigate('/login');
                    },
                  },
                ],
              }}
              placement="bottomRight"
            >
              <Avatar
                style={{ cursor: 'pointer', backgroundColor: '#1890ff' }}
                icon={<UserOutlined />}
              />
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: 6,
          }}
        >
          {children}
        </Content>
      </AntLayout>
      
      {/* 用户切换Modal */}
      <Modal
        title="切换用户视角"
        open={switchModalVisible}
        onCancel={() => setSwitchModalVisible(false)}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <p>选择要切换到的用户视角：</p>
        </div>
        <Select
          style={{ width: '100%' }}
          placeholder="请选择用户"
          loading={loading}
          showSearch
          optionFilterProp="children"
          filterOption={(input, option) =>
            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
          }
          onSelect={handleSwitchUser}
          options={users.map(user => ({
            value: user.id,
            label: (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{user.email}</span>
                <div>
                  {user.is_super_admin && <Tag color="red" size="small">管理员</Tag>}
                  {user.is_verified ? (
                    <Tag color="green" size="small">已验证</Tag>
                  ) : (
                    <Tag color="orange" size="small">未验证</Tag>
                  )}
                </div>
              </div>
            )
          }))}
        />
        <div style={{ marginTop: 16, color: '#666', fontSize: '12px' }}>
          * 切换后您将以所选用户的身份查看数据和API调用记录
        </div>
      </Modal>
    </AntLayout>
  );
};

export default Layout;