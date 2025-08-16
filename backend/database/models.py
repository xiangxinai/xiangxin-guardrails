from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=False)  # 邮箱验证后激活
    is_verified = Column(Boolean, default=False)  # 邮箱是否已验证
    is_super_admin = Column(Boolean, default=False)  # 是否为超级管理员
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    detection_results = relationship("DetectionResult", back_populates="user")
    test_models = relationship("TestModelConfig", back_populates="user")
    blacklists = relationship("Blacklist", back_populates="user")
    whitelists = relationship("Whitelist", back_populates="user")
    response_templates = relationship("ResponseTemplate", back_populates="user")

class EmailVerification(Base):
    """邮箱验证表"""
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    verification_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DetectionResult(Base):
    """检测结果表"""
    __tablename__ = "detection_results"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # 关联用户
    content = Column(Text, nullable=False)
    suggest_action = Column(String(20))  # '通过', '阻断', '代答'
    suggest_answer = Column(Text)  # 建议回答内容
    hit_keywords = Column(Text)  # 命中的关键词(黑白名单)
    model_response = Column(Text)  # 原始模型响应
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)
    # 分离的安全和合规检测结果
    security_risk_level = Column(String(10), default='无风险')  # 提示词攻击风险等级
    security_categories = Column(JSON, default=list)  # 提示词攻击类别
    compliance_risk_level = Column(String(10), default='无风险')  # 内容合规风险等级
    compliance_categories = Column(JSON, default=list)  # 内容合规类别
    
    # 关联关系
    user = relationship("User", back_populates="detection_results")

class Blacklist(Base):
    """黑名单表"""
    __tablename__ = "blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # 关联用户
    name = Column(String(100), nullable=False)  # 黑名单库名称
    keywords = Column(JSON, nullable=False)  # 关键词列表
    description = Column(Text)  # 描述
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="blacklists")

class Whitelist(Base):
    """白名单表"""
    __tablename__ = "whitelist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # 关联用户
    name = Column(String(100), nullable=False)  # 白名单库名称
    keywords = Column(JSON, nullable=False)  # 关键词列表
    description = Column(Text)  # 描述
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="whitelists")

class ResponseTemplate(Base):
    """代答库表"""
    __tablename__ = "response_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    # 允许为空：当为系统级默认模板时，user_id 为空
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # 关联用户（可为空表示全局模板）
    category = Column(String(50), nullable=False, index=True)  # 风险类别 (S1-S12, default)
    risk_level = Column(String(10), nullable=False)  # 风险等级
    template_content = Column(Text, nullable=False)  # 代答内容
    is_default = Column(Boolean, default=False)  # 是否为默认模板
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="response_templates")

class UserSwitch(Base):
    """用户切换记录表（用于超级管理员切换用户视角）"""
    __tablename__ = "user_switches"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 管理员用户ID
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 目标用户ID
    switch_time = Column(DateTime(timezone=True), server_default=func.now())
    session_token = Column(String(128), unique=True, nullable=False)  # 切换会话token
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class LoginAttempt(Base):
    """登录尝试记录表（用于防爆破）"""
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)  # 支持IPv6
    user_agent = Column(Text)
    success = Column(Boolean, default=False, index=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class UserRateLimit(Base):
    """用户限速配置表"""
    __tablename__ = "user_rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    requests_per_second = Column(Integer, default=1, nullable=False)  # 每秒请求数，0表示无限制
    is_active = Column(Boolean, default=True, index=True)  # 是否启用限速
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User")

class UserRateLimitCounter(Base):
    """用户实时限速计数器表 - 用于跨进程限速"""
    __tablename__ = "user_rate_limit_counters"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, index=True)
    current_count = Column(Integer, default=0, nullable=False)  # 当前窗口内的请求计数
    window_start = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 窗口开始时间
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)  # 最后更新时间
    
    # 关联关系
    user = relationship("User")

class TestModelConfig(Base):
    """被测模型配置表"""
    __tablename__ = "test_model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # 模型显示名称
    base_url = Column(String(512), nullable=False)  # API Base URL
    api_key = Column(String(512), nullable=False)  # API Key
    model_name = Column(String(255), nullable=False)  # 模型名称
    enabled = Column(Boolean, default=True, index=True)  # 是否启用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="test_models")
