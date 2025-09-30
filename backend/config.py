from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path

def get_version() -> str:
    """
    获取版本号，优先级：
    1. VERSION 文件
    2. 环境变量 APP_VERSION
    3. 默认版本
    """
    try:
        # 尝试从 VERSION 文件读取
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    
    # 尝试从环境变量获取
    import os
    env_version = os.getenv('APP_VERSION')
    if env_version:
        return env_version
    
    # 默认版本
    return "1.0.0"

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Xiangxin Guardrails"
    app_version: str = get_version()
    debug: bool = False
    
    # 超级管理员配置
    # 警告：请在生产环境中修改这些默认值！
    super_admin_username: str = "admin@yourdomain.com"
    super_admin_password: str = "CHANGE-THIS-PASSWORD-IN-PRODUCTION"
    
    # 数据目录配置
    data_dir: str = "/mnt/data/xiangxin-guardrails-data"

    @property
    def media_dir(self) -> str:
        """媒体文件目录"""
        return f"{self.data_dir}/media"
    
    # 数据库配置
    database_url: str = "postgresql://xiangxin:your_password@localhost:54321/xiangxin_guardrails"
    
    # 模型配置
    guardrails_model_api_url: str = "http://your-host-ip:your-port/v1"
    guardrails_model_api_key: str = "your-guardrails-model-api-key"
    guardrails_model_name: str = "Xiangxin-Guardrails-Text"

    # 多模态模型配置
    guardrails_vl_model_api_url: str = "http://localhost:58003/v1"
    guardrails_vl_model_api_key: str = "your-vl-model-api-key"
    guardrails_vl_model_name: str = "Xiangxin-Guardrails-VL"
    
    # 检测最大上下文长度配置 (应该等于模型max-model-len - 1000)
    max_detection_context_length: int = 7168
    
    # 嵌入模型API配置
    # 用于知识库向量化的嵌入模型API
    embedding_api_base_url: str = "http://your-host-ip:your-port/v1"
    embedding_api_key: str = "your-embedding-api-key"
    embedding_model_name: str = "Xiangxin-Embedding-1024"
    embedding_model_dimension: int = 1024  # 嵌入向量维度
    embedding_similarity_threshold: float = 0.7  # 相似度阈值
    embedding_max_results: int = 5  # 最大返回结果数

    # API配置
    cors_origins: str = "*"
    
    # 日志配置  
    log_level: str = "INFO"
    
    @property
    def log_dir(self) -> str:
        """日志目录"""
        return f"{self.data_dir}/logs"
    
    @property 
    def detection_log_dir(self) -> str:
        """检测结果日志目录"""
        return f"{self.data_dir}/logs/detection"
    
    # 联系方式
    support_email: str = "wanglei@xiangxinai.cn"
    
    # HuggingFace模型
    huggingface_model: str = "xiangxinai/Xiangxin-Guardrails-Text"
    
    # JWT配置
    # 警告：请生成安全的随机密钥！使用: openssl rand -base64 64
    jwt_secret_key: str = "GENERATE-A-SECURE-RANDOM-JWT-KEY-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    
    # 邮箱配置
    smtp_server: str = ""
    smtp_port: Optional[int] = None
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    

    # 服务器配置 - 双服务架构
    host: str = "0.0.0.0"
    
    # 检测服务主机名（用于服务间调用）
    # Docker环境: detection-service，本地环境: localhost
    detection_host: str = "localhost"
    
    # 管理服务配置（低并发）
    admin_port: int = 5000
    admin_uvicorn_workers: int = 2
    admin_max_concurrent_requests: int = 50

    # 检测服务配置（高并发）
    detection_port: int = 5001
    detection_uvicorn_workers: int = 32
    detection_max_concurrent_requests: int = 400

    # 反向代理服务配置（高并发）
    proxy_port: int = 5002
    proxy_uvicorn_workers: int = 24
    proxy_max_concurrent_requests: int = 300

    # 开发运维：是否在启动时重置数据库（删除并重建所有表）
    reset_database_on_startup: bool = False
    
    # 私有化部署配置：是否将检测结果存储到数据库
    # true: 存储到数据库（SaaS模式，完整数据分析）
    # false: 仅写日志文件（私有化模式，减少数据库压力）
    store_detection_results: bool = True

    class Config:
        # Ensure we load the .env file next to this config module,
        # regardless of the current working directory
        env_file = str(Path(__file__).with_name('.env'))
        case_sensitive = False
        extra = "allow"

settings = Settings()
