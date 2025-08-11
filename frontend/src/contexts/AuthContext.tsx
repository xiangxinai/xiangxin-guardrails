import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, UserInfo } from '../services/auth';
import { adminApi } from '../services/api';

interface SwitchInfo {
  is_switched: boolean;
  admin_user?: { id: string; email: string };
  target_user?: { id: string; email: string; api_key: string };
}

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  switchInfo: SwitchInfo;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchToUser: (userId: string) => Promise<void>;
  exitSwitch: () => Promise<void>;
  refreshSwitchStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [switchInfo, setSwitchInfo] = useState<SwitchInfo>({ is_switched: false });

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      if (authService.isAuthenticated()) {
        const userInfo = await authService.getCurrentUser();
        setUser(userInfo);
        setIsAuthenticated(true);
        
        // 检查用户切换状态
        await refreshSwitchStatus();
      } else {
        setUser(null);
        setIsAuthenticated(false);
        setSwitchInfo({ is_switched: false });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setIsAuthenticated(false);
      setSwitchInfo({ is_switched: false });
      authService.clearToken();
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSwitchStatus = async () => {
    try {
      const response = await adminApi.getCurrentSwitch();
      setSwitchInfo(response);
    } catch (error) {
      // 如果不是超级管理员或者没有切换权限，忽略错误
      setSwitchInfo({ is_switched: false });
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await authService.login({ email, password });
      authService.setToken(response.access_token);
      
      const userInfo = await authService.getCurrentUser();
      setUser(userInfo);
      setIsAuthenticated(true);
      // 登录后刷新一次切换状态，避免首页并发请求导致401提示
      try {
        await refreshSwitchStatus();
      } catch (e) {
        // 忽略切换状态错误
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setSwitchInfo({ is_switched: false });
      localStorage.removeItem('switch_session_token');
    }
  };

  const switchToUser = async (userId: string) => {
    try {
      const response = await adminApi.switchToUser(userId);
      localStorage.setItem('switch_session_token', response.switch_session_token);
      await refreshSwitchStatus();
    } catch (error) {
      console.error('Switch user failed:', error);
      throw error;
    }
  };

  const exitSwitch = async () => {
    try {
      await adminApi.exitSwitch();
      localStorage.removeItem('switch_session_token');
      await refreshSwitchStatus();
    } catch (error) {
      console.error('Exit switch failed:', error);
      throw error;
    }
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    switchInfo,
    login,
    logout,
    switchToUser,
    exitSwitch,
    refreshSwitchStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};