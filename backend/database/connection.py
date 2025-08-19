from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import settings

# 创建PostgreSQL数据库引擎 - 分离服务优化
# 检测服务引擎 - 极简连接池（只用于认证）
detection_engine = create_engine(
    settings.database_url,
    pool_size=2,  # 检测服务只需要认证，极小连接池
    max_overflow=3,  # 检测服务极小溢出连接
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    echo=False
)

# 管理服务引擎 - 低并发优化
admin_engine = create_engine(
    settings.database_url,
    pool_size=3,  # 管理服务连接池  
    max_overflow=5,  # 管理服务溢出连接
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    echo=False
)

# 默认引擎（向后兼容）
engine = detection_engine

# 创建会话 - 分离服务
DetectionSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=detection_engine)
AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)

# 默认会话（向后兼容）
SessionLocal = DetectionSessionLocal

# 创建基类
Base = declarative_base()

def get_database_url():
    """获取数据库URL"""
    return settings.database_url

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """获取数据库会话（非生成器版本）"""
    return SessionLocal()

def get_detection_db_session():
    """获取检测服务数据库会话"""
    return DetectionSessionLocal()

def get_admin_db_session():
    """获取管理服务数据库会话"""
    return AdminSessionLocal()

def create_detection_engine():
    """创建检测服务引擎"""
    return detection_engine

def create_admin_engine():
    """创建管理服务引擎"""
    return admin_engine

async def init_db(minimal=False):
    """初始化数据库（使用PostgreSQL咨询锁，避免多进程并发初始化；锁与业务事务使用不同连接）
    
    Args:
        minimal: 是否最小化初始化（检测服务用）
    """
    from database.models import DetectionResult, Blacklist, Whitelist, ResponseTemplate, SystemConfig, User, EmailVerification, UserSwitch
    from services.admin_service import admin_service

    lock_key = 0x5A6F_5858_4941_4752  # 固定 64-bit 锁键

    # 1) 使用独立的自动提交连接获取/释放 advisory lock（不与业务事务复用同一连接）
    # 管理服务负责完整初始化
    init_engine = admin_engine if not minimal else detection_engine
    with init_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as lock_conn:
        lock_conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": lock_key})
        try:
            # 2) 在全新的事务中执行DDL与初始化，避免与锁连接产生事务状态干扰
            with init_engine.begin() as tx_conn:
                if settings.reset_database_on_startup:
                    Base.metadata.drop_all(bind=tx_conn)
                # checkfirst=True（默认），仅创建缺失表
                Base.metadata.create_all(bind=tx_conn)

                # 使用相同连接进行幂等初始化
                db = Session(bind=tx_conn)

                # 检测服务只需要基础表结构，管理服务需要完整初始化
                if not minimal:
                    # 创建超级管理员账户（幂等）
                    admin_service.create_super_admin_if_not_exists(db)

                    # 初始化默认数据（幂等）
                    existing_config = db.query(SystemConfig).filter_by(config_key="initialized").first()
                    if not existing_config:
                        default_configs = [
                            SystemConfig(config_key="initialized", config_value="true", description="System initialization flag"),
                            SystemConfig(config_key="default_action", config_value="代答", description="Default action for high risk content"),
                        ]

                        default_responses = [
                            ResponseTemplate(category="S1", risk_level="高风险", template_content="很抱歉，我不能讨论涉及政治敏感的话题。", is_default=True),
                            ResponseTemplate(category="S2", risk_level="高风险", template_content="很抱歉，我不能回答涉及敏感政治话题的问题。", is_default=True), 
                            ResponseTemplate(category="S3", risk_level="高风险", template_content="很抱歉，我不能回答损害国家形象的问题。", is_default=True),
                            ResponseTemplate(category="S4", risk_level="高风险", template_content="很抱歉，我不能提供可能对未成年人造成伤害的内容。", is_default=True),
                            ResponseTemplate(category="S5", risk_level="高风险", template_content="很抱歉，我不能回答涉及暴力犯罪的问题。", is_default=True),
                            ResponseTemplate(category="S6", risk_level="高风险", template_content="很抱歉，我不能提供涉及违法犯罪的信息。", is_default=True),
                            ResponseTemplate(category="S7", risk_level="高风险", template_content="很抱歉，我不能提供涉及色情的内容。", is_default=True),
                            ResponseTemplate(category="S8", risk_level="高风险", template_content="请保持友善和尊重，避免歧视性言论。每个人都值得被平等对待。", is_default=True),
                            ResponseTemplate(category="S9", risk_level="高风险", template_content="检测到提示词攻击，请重新组织您的问题。", is_default=True),
                            ResponseTemplate(category="S10", risk_level="高风险", template_content="请保持文明用语，我们可以友好地交流。有什么我可以帮助您的吗？", is_default=True),
                            ResponseTemplate(category="S11", risk_level="高风险", template_content="很抱歉，我不能讨论涉及侵犯个人隐私的内容。请尊重他人的隐私权。", is_default=True),
                            ResponseTemplate(category="S12", risk_level="高风险", template_content="很抱歉，我不能提供可能涉及商业违法行为的建议。请咨询相关专业人士。", is_default=True),
                            ResponseTemplate(category="default", risk_level="高风险", template_content="很抱歉，我不能回答这个问题。如有疑问请联系客服。", is_default=True),
                        ]

                        for config in default_configs:
                            db.add(config)
                        for response in default_responses:
                            db.add(response)
                        db.commit()
        finally:
            # 3) 释放advisory lock（依旧使用独立的自动提交连接）
            lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": lock_key})