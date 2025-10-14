from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

# Create PostgreSQL database engine - optimized for separated services
# Detection service engine - minimal connection pool (only for authentication)
detection_engine = create_engine(
    settings.database_url,
    pool_size=1,  # Detection service only needs authentication, minimal connection pool
    max_overflow=2,  # Detection service minimal overflow connection
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    echo=False
)

# Management service engine - low concurrency optimization
admin_engine = create_engine(
    settings.database_url,
    pool_size=3,  # Management service connection pool  
    max_overflow=5,  # Management service overflow connection
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    echo=False
)

# Proxy service engine - medium concurrency optimization
proxy_engine = create_engine(
    settings.database_url,
    pool_size=3,  # Proxy service connection pool (reduced from 5)
    max_overflow=5,  # Proxy service overflow connection (reduced from 10)
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    echo=False
)

# Default engine (backward compatibility)
engine = detection_engine

# Create session - separated services
DetectionSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=detection_engine)
AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)
ProxySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=proxy_engine)

# Default session (backward compatibility)
SessionLocal = DetectionSessionLocal

# Create base class
Base = declarative_base()

def get_database_url():
    """Get database URL"""
    return settings.database_url

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get database session (non-generator version)"""
    return SessionLocal()

def get_detection_db_session():
    """Get detection service database session"""
    return DetectionSessionLocal()

def get_admin_db_session():
    """Get management service database session"""
    return AdminSessionLocal()

def get_proxy_db_session():
    """Get proxy service database session"""
    return ProxySessionLocal()

def create_detection_engine():
    """Create detection service engine"""
    return detection_engine

def create_admin_engine():
    """Create management service engine"""
    return admin_engine

def create_proxy_engine():
    """Create proxy service engine"""
    return proxy_engine

async def init_db(minimal=False):
<<<<<<< HEAD
    """Initialize database (using PostgreSQL advisory lock, avoid multi-process concurrent initialization; lock and business transaction use different connections)
    
=======
    """初始化数据库（使用PostgreSQL咨询锁，避免多进程并发初始化；锁与业务事务使用不同连接）

>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
    Args:
        minimal: Whether to minimize initialization (detection service used)
    """
    from database.models import DetectionResult, Blacklist, Whitelist, ResponseTemplate, SystemConfig, Tenant, EmailVerification, TenantSwitch
    from services.admin_service import admin_service

    lock_key = 0x5A6F_5858_4941_4752  # Fixed 64-bit lock key

    # 1) Use independent auto-commit connection to get/release advisory lock (do not reuse the same connection with business transactions)
    # Management service is responsible for full initialization
    init_engine = admin_engine if not minimal else detection_engine
    with init_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as lock_conn:
        lock_conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": lock_key})
        try:
<<<<<<< HEAD
            # 2) Execute DDL and initialization in a new transaction, avoid transaction state interference with the lock connection
=======
            # 2) 先运行数据库迁移（仅管理服务，避免重复执行）
            if not minimal:
                try:
                    from database.run_migrations import run_migrations
                    await run_migrations()
                    logger.info("Database migrations completed successfully")
                except Exception as e:
                    logger.error(f"Database migrations failed: {e}")
                    # 迁移失败不应该阻止整个初始化过程，但应该记录错误
                    # 继续使用SQLAlchemy create_all作为后备方案

            # 3) 在全新的事务中执行DDL与初始化，避免与锁连接产生事务状态干扰
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
            with init_engine.begin() as tx_conn:
                if settings.reset_database_on_startup:
                    # Safely cascade delete all tables, maintain backward compatibility with old data format
                    try:
                        # Try to delete tables with foreign key dependencies first
                        tx_conn.execute(text("DROP TABLE IF EXISTS proxy_configs CASCADE"))
                        tx_conn.execute(text("DROP TABLE IF EXISTS email_verifications CASCADE"))
                        tx_conn.execute(text("DROP TABLE IF EXISTS user_switches CASCADE"))
                        # Then delete other tables
                        Base.metadata.drop_all(bind=tx_conn)
                    except Exception as e:
                        # If there is still a problem, use cascade delete
                        tx_conn.execute(text("DROP SCHEMA public CASCADE"))
                        tx_conn.execute(text("CREATE SCHEMA public"))
                        tx_conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
<<<<<<< HEAD
                
                # checkfirst=True (default), only create missing tables, maintain backward compatibility
=======

                # checkfirst=True（默认），仅创建缺失表，保持向后兼容
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
                Base.metadata.create_all(bind=tx_conn)

                # Use the same connection for idempotent initialization
                db = Session(bind=tx_conn)

                # Detection service only needs basic table structure, management service needs full initialization
                if not minimal:
                    # Create super admin account (idempotent)
                    admin_service.create_super_admin_if_not_exists(db)

                    # Initialize default data (idempotent)
                    existing_config = db.query(SystemConfig).filter_by(config_key="initialized").first()
                    if not existing_config:
                        default_configs = [
                            SystemConfig(config_key="initialized", config_value="true", description="System initialization flag"),
                            SystemConfig(config_key="default_action", config_value="reject", description="Default action for high risk content"),
                        ]

                        default_responses = [
<<<<<<< HEAD
                            ResponseTemplate(category="S1", risk_level="high_risk", template_content="I'm sorry, I can't discuss political topics.", is_default=True),
                            ResponseTemplate(category="S2", risk_level="high_risk", template_content="I'm sorry, I can't answer questions involving sensitive political topics.", is_default=True), 
                            ResponseTemplate(category="S3", risk_level="high_risk", template_content="I'm sorry, I can't answer questions that may damage national image.", is_default=True),
                            ResponseTemplate(category="S4", risk_level="high_risk", template_content="I'm sorry, I can't provide content that may harm minors.", is_default=True),
                            ResponseTemplate(category="S5", risk_level="high_risk", template_content="I'm sorry, I can't answer questions involving violent crime.", is_default=True),
                            ResponseTemplate(category="S6", risk_level="high_risk", template_content="I'm sorry, I can't provide content involving illegal activities.", is_default=True),
                            ResponseTemplate(category="S7", risk_level="high_risk", template_content="I'm sorry, I can't provide content involving pornography.", is_default=True),
                            ResponseTemplate(category="S8", risk_level="high_risk", template_content="Please keep friendly and respectful, avoid discriminatory speech. Everyone deserves平等对待。", is_default=True),
                            ResponseTemplate(category="S9", risk_level="high_risk", template_content="I'm sorry, I can't answer questions involving prompt injection attacks.", is_default=True),
                            ResponseTemplate(category="S10", risk_level="high_risk", template_content="Please keep friendly and respectful, avoid discriminatory speech. Everyone deserves平等对待。", is_default=True),
                            ResponseTemplate(category="S11", risk_level="high_risk", template_content="I'm sorry, I can't discuss content involving personal privacy. Please respect others' privacy.", is_default=True),
                            ResponseTemplate(category="S12", risk_level="high_risk", template_content="I'm sorry, I can't provide advice on possible business violations. Please consult with a professional.", is_default=True),
                            ResponseTemplate(category="default", risk_level="high_risk", template_content="I'm sorry, I can't answer this question. Please contact customer service if you have any questions.", is_default=True),
=======
                            ResponseTemplate(category="S1", risk_level="高风险", template_content="很抱歉，我不能讨论涉政话题。", is_default=True),
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
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
                        ]

                        for config in default_configs:
                            db.add(config)
                        for response in default_responses:
                            db.add(response)
                        db.commit()
        finally:
<<<<<<< HEAD
            # 3) Release advisory lock (still use independent auto-commit connection)
=======
            # 4) 释放advisory lock（依旧使用独立的自动提交连接）
>>>>>>> 861b916 (feat: implement tenant migration scripts and database initialization)
            lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": lock_key})