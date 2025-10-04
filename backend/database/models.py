from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint, Float
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
    risk_config = relationship("RiskTypeConfig", back_populates="user", uselist=False)

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
    suggest_action = Column(String(20))  # '通过', '拒答', '代答'
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
    # 数据安全检测结果
    data_risk_level = Column(String(10), default='无风险')  # 数据泄漏风险等级
    data_categories = Column(JSON, default=list)  # 数据泄漏类别
    # 敏感度相关字段
    sensitivity_level = Column(String(10))  # 敏感度等级: '高', '中', '低'
    sensitivity_score = Column(Float)  # 原始敏感度分数 (0.0-1.0)
    # 多模态相关字段
    has_image = Column(Boolean, default=False, index=True)  # 是否包含图片
    image_count = Column(Integer, default=0)  # 图片数量
    image_paths = Column(JSON, default=list)  # 保存的图片文件路径列表

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

class RiskTypeConfig(Base):
    """风险类型开关配置表"""
    __tablename__ = "risk_type_config"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, unique=True)

    # S1-S12风险类型开关配置
    s1_enabled = Column(Boolean, default=True)  # 一般政治话题
    s2_enabled = Column(Boolean, default=True)  # 敏感政治话题
    s3_enabled = Column(Boolean, default=True)  # 损害国家形象
    s4_enabled = Column(Boolean, default=True)  # 伤害未成年人
    s5_enabled = Column(Boolean, default=True)  # 暴力犯罪
    s6_enabled = Column(Boolean, default=True)  # 违法犯罪
    s7_enabled = Column(Boolean, default=True)  # 色情
    s8_enabled = Column(Boolean, default=True)  # 歧视内容
    s9_enabled = Column(Boolean, default=True)  # 提示词攻击
    s10_enabled = Column(Boolean, default=True) # 辱骂
    s11_enabled = Column(Boolean, default=True) # 侵犯个人隐私
    s12_enabled = Column(Boolean, default=True) # 商业违法违规

    # 全局敏感度阈值配置
    high_sensitivity_threshold = Column(Float, default=0.40)    # 高敏感度阈值
    medium_sensitivity_threshold = Column(Float, default=0.60)  # 中敏感度阈值
    low_sensitivity_threshold = Column(Float, default=0.95)     # 低敏感度阈值

    # 敏感度触发等级配置 (low, medium, high)
    sensitivity_trigger_level = Column(String(10), default="medium")  # 触发检测命中的最低敏感度等级

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User", back_populates="risk_config")

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
    """代理模型配置表"""
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

class ProxyModelConfig(Base):
    """反向代理模型配置表"""
    __tablename__ = "proxy_model_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    config_name = Column(String(100), nullable=False, index=True)  # 代理模型名称，用于model参数匹配
    api_base_url = Column(String(512), nullable=False)  # 上游API基础URL
    api_key_encrypted = Column(Text, nullable=False)  # 加密的上游API密钥
    model_name = Column(String(255), nullable=False)  # 上游API模型名称
    enabled = Column(Boolean, default=True, index=True)  # 是否启用

    # 安全配置（极简设计）
    block_on_input_risk = Column(Boolean, default=False)  # 输入风险时是否阻断，默认不阻断
    block_on_output_risk = Column(Boolean, default=False)  # 输出风险时是否阻断，默认不阻断
    enable_reasoning_detection = Column(Boolean, default=True)  # 是否检测reasoning内容，默认开启
    stream_chunk_size = Column(Integer, default=50)  # 流式检测间隔，每N个chunk检测一次，默认50

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User")

class ProxyRequestLog(Base):
    """反向代理请求日志表"""
    __tablename__ = "proxy_request_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    proxy_config_id = Column(UUID(as_uuid=True), ForeignKey("proxy_model_configs.id"), nullable=False)
    
    # 请求信息
    model_requested = Column(String(255), nullable=False)  # 用户请求的模型名
    model_used = Column(String(255), nullable=False)  # 实际使用的模型名
    provider = Column(String(50), nullable=False)  # 提供商
    
    # 检测结果
    input_detection_id = Column(String(64), index=True)  # 输入检测请求ID
    output_detection_id = Column(String(64), index=True)  # 输出检测请求ID
    input_blocked = Column(Boolean, default=False)  # 输入是否被阻断
    output_blocked = Column(Boolean, default=False)  # 输出是否被阻断
    
    # 统计信息
    request_tokens = Column(Integer)  # 请求token数
    response_tokens = Column(Integer)  # 响应token数
    total_tokens = Column(Integer)  # 总token数
    response_time_ms = Column(Integer)  # 响应时间(毫秒)
    
    # 状态
    status = Column(String(20), nullable=False)  # success, blocked, error
    error_message = Column(Text)  # 错误信息
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 关联关系
    user = relationship("User")
    proxy_config = relationship("ProxyModelConfig")

class KnowledgeBase(Base):
    """代答知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # 风险类别 (S1-S12)
    name = Column(String(255), nullable=False)  # 知识库名称
    description = Column(Text)  # 描述
    file_path = Column(String(512), nullable=False)  # 原始JSONL文件路径
    vector_file_path = Column(String(512))  # 向量化文件路径
    total_qa_pairs = Column(Integer, default=0)  # 问答对总数
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    is_global = Column(Boolean, default=False, index=True)  # 是否为全局知识库（所有用户生效），仅管理员可设置
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User")

class OnlineTestModelSelection(Base):
    """在线测试模型选择表 - 记录用户在在线测试中选择的代理模型"""
    __tablename__ = "online_test_model_selections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    proxy_model_id = Column(UUID(as_uuid=True), ForeignKey("proxy_model_configs.id"), nullable=False, index=True)
    selected = Column(Boolean, default=False, nullable=False)  # 是否被选中用于在线测试
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User")
    proxy_model = relationship("ProxyModelConfig")
    
    # 添加唯一约束，确保每个用户对每个代理模型只有一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'proxy_model_id', name='_user_proxy_model_selection_uc'),
    )

class DataSecurityEntityType(Base):
    """数据安全实体类型配置表"""
    __tablename__ = "data_security_entity_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # 实体类型代码，如 ID_CARD_NUMBER
    display_name = Column(String(200), nullable=False)  # 显示名称，如 "身份证号"
    category = Column(String(50), nullable=False, index=True)  # 风险等级: 低、中、高
    recognition_method = Column(String(20), nullable=False)  # 识别方法: regex
    recognition_config = Column(JSON, nullable=False)  # 识别配置，如 {"pattern": "...", "check_input": true, "check_output": true}
    anonymization_method = Column(String(20), default='replace')  # 脱敏方法: replace, mask, hash, encrypt, shuffle, random
    anonymization_config = Column(JSON)  # 脱敏配置，如 {"replacement": "<ID_CARD>"}
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    is_global = Column(Boolean, default=False, index=True)  # 是否为全局配置
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User")
