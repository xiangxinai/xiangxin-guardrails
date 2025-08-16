# 象信AI安全护栏 - 私有化部署指南

## 概述

本文档详细说明象信AI安全护栏系统的私有化部署方案，包括环境要求、安装步骤、配置说明和运维指导。

## 部署架构

### 标准架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户中控台    │────│  象信AI护栏系统  │────│   AI模型服务    │
│                 │    │                 │    │                 │
│ - 用户管理      │    │ - 检测服务      │    │ - Xiangxin      │
│ - 配置管理      │    │ - 管理服务      │    │   Guardrails    │
│ - 数据分析      │    │ - 数据库        │    │   Text Model    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 双服务架构组件
- **检测服务 (Detection Service)**: 端口5000，32个工作进程，处理高并发检测API `/v1/guardrails`
- **管理服务 (Admin Service)**: 端口5001，2个工作进程，处理管理平台API `/api/v1/*`  
- **数据库 (PostgreSQL)**: 存储配置信息和可选的检测结果
- **AI模型服务**: 提供内容安全检测能力
- **Nginx反向代理**: 自动路由请求到对应服务

## 系统要求

### 硬件要求
| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核心 | 8核心 |
| 内存 | 8GB | 16GB |
| 存储 | 100GB SSD | 500GB SSD |
| 网络 | 100Mbps | 1Gbps |

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+ (如果源码部署)
- **Node.js**: 16+ (可选，用于前端)
- **PostgreSQL**: 13+ (如果独立部署数据库)

## 快速部署 (Docker)

### 1. 下载部署包

```bash
# 创建部署目录
mkdir -p /opt/xiangxin-guardrails
cd /opt/xiangxin-guardrails

# 下载部署包 (假设已提供)
wget https://releases.xiangxinai.cn/guardrails/v1.0.0/xiangxin-guardrails-private.tar.gz
tar -xzf xiangxin-guardrails-private.tar.gz
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**关键配置项**:
```bash
# 私有化部署模式 - 关键配置！
STORE_DETECTION_RESULTS=false  # false=仅写日志, true=存储到数据库

# JWT密钥 (极其重要！客户需要此密钥生成token)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://guardrails:password@postgres:5432/guardrails_db

# AI模型服务配置
GUARDRAILS_MODEL_API_URL=http://model-service:8000/v1
GUARDRAILS_MODEL_API_KEY=your-model-api-key

# 数据目录 (日志文件将存储在此目录的logs子目录下)
DATA_DIR=/opt/xiangxin-guardrails/data

# 双服务配置
DETECTION_PORT=5000
DETECTION_UVICORN_WORKERS=32
ADMIN_PORT=5001
ADMIN_UVICORN_WORKERS=2
```

### 3. 启动服务

```bash
# 使用Docker Compose启动双服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f detection-service  # 检测服务日志
docker-compose logs -f admin-service      # 管理服务日志
```

### 4. 验证部署

```bash
# 检测服务健康检查
curl http://localhost:5000/health

# 管理服务健康检查
curl http://localhost:5001/health

# 检查数据库连接
docker-compose exec postgres psql -U guardrails -d guardrails_db -c "SELECT version();"
```

## Docker Compose 配置

### docker-compose.yml 示例

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: guardrails_db
      POSTGRES_USER: guardrails
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-secure_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "54321:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U guardrails"]
      interval: 30s
      timeout: 10s
      retries: 5

  detection-service:
    image: xiangxinai/guardrails-detection:v1.0.0
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - GUARDRAILS_MODEL_API_URL=${GUARDRAILS_MODEL_API_URL}
      - GUARDRAILS_MODEL_API_KEY=${GUARDRAILS_MODEL_API_KEY}
      - STORE_DETECTION_RESULTS=${STORE_DETECTION_RESULTS:-false}
      - DATA_DIR=/app/data
    volumes:
      - app_data:/app/data
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  admin-service:
    image: xiangxinai/guardrails-admin:v1.0.0
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - STORE_DETECTION_RESULTS=${STORE_DETECTION_RESULTS:-false}
      - DATA_DIR=/app/data
      - SUPER_ADMIN_USERNAME=${SUPER_ADMIN_USERNAME:-admin@yourdomain.com}
      - SUPER_ADMIN_PASSWORD=${SUPER_ADMIN_PASSWORD:-CHANGE_ME}
    volumes:
      - app_data:/app/data
    ports:
      - "5001:5001"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  model-service:
    image: xiangxinai/guardrails-model:v1.0.0
    environment:
      - MODEL_NAME=Xiangxin-Guardrails-Text
      - MODEL_DEVICE=cpu  # 或 cuda 如果有GPU
    ports:
      - "58002:8000"
    volumes:
      - model_cache:/app/models
    restart: unless-stopped
    # GPU支持 (如果需要)
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # 可选：前端界面 (用于管理和监控)
  frontend:
    image: xiangxinai/guardrails-frontend:v1.0.0
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:5001
    ports:
      - "3000:3000"
    depends_on:
      - admin-service
    restart: unless-stopped

volumes:
  postgres_data:
  app_data:
  model_cache:
```

## 源码部署

### 1. 环境准备

```bash
# 安装Python依赖
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

pip install -r requirements.txt

# 安装Node.js依赖 (如果需要前端)
cd ../frontend
npm install
```

### 2. 数据库初始化

```bash
# 创建数据库
createdb -U postgres guardrails_db

# 运行迁移
cd backend
python -m alembic upgrade head
```

### 3. 启动服务

```bash
# 启动检测服务
cd backend
python detection_service.py &

# 启动管理服务  
python admin_service.py &

# 启动前端 (可选)
cd ../frontend
npm run build
npm run preview &
```

## 配置详解

### 核心配置项

#### 私有化部署关键配置
```bash
# 是否存储检测结果到数据库
# false: 私有化模式，仅写日志文件，数据库只存配置
# true:  SaaS模式，完整存储检测结果
STORE_DETECTION_RESULTS=false
```

#### JWT认证配置
```bash
# JWT密钥 - 客户需要此密钥生成token
JWT_SECRET_KEY=use-openssl-rand-base64-64-to-generate

# JWT算法
JWT_ALGORITHM=HS256

# Token过期时间(分钟)  
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### 数据库配置
```bash
# 数据库连接URL
DATABASE_URL=postgresql://user:password@host:port/database

# 数据目录
DATA_DIR=/opt/xiangxin-guardrails/data
```

#### AI模型配置
```bash
# 模型服务地址
GUARDRAILS_MODEL_API_URL=http://localhost:58002/v1

# 模型API密钥
GUARDRAILS_MODEL_API_KEY=your-api-key

# 模型名称
GUARDRAILS_MODEL_NAME=Xiangxin-Guardrails-Text
```

#### 服务配置
```bash
# 检测服务配置 (高并发)
DETECTION_PORT=5000
DETECTION_UVICORN_WORKERS=32
DETECTION_MAX_CONCURRENT_REQUESTS=400

# 管理服务配置 (低并发)
ADMIN_PORT=5001
ADMIN_UVICORN_WORKERS=2
ADMIN_MAX_CONCURRENT_REQUESTS=50
```

### 安全配置建议

```bash
# 1. 生成安全的JWT密钥
JWT_SECRET_KEY=$(openssl rand -base64 64)

# 2. 设置强密码
SUPER_ADMIN_PASSWORD=$(openssl rand -base64 32)
DATABASE_PASSWORD=$(openssl rand -base64 32)

# 3. 限制网络访问
# 仅内网访问
HOST=0.0.0.0  # 或设置为内网IP

# 4. 开启SSL (如果需要)
USE_SSL=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

## 网络和防火墙配置

### 端口说明
| 端口 | 服务 | 说明 | 访问权限 |
|------|------|------|----------|
| 5000 | 检测服务 | 高并发内容检测API | 客户系统访问 |
| 5001 | 管理服务 | 配置管理API | 客户系统访问 |
| 54321 | PostgreSQL | 数据库 | 内部访问 |
| 58002 | AI模型服务 | 模型推理API | 内部访问 |
| 3000 | 前端界面 | Web管理界面 | 管理员访问 |

### 防火墙规则示例

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow from <client-ip-range> to any port 5000
sudo ufw allow from <client-ip-range> to any port 5001
sudo ufw allow from <admin-ip-range> to any port 3000

# CentOS/RHEL (firewalld)
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<client-ip-range>" port port="5000" protocol="tcp" accept'
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<client-ip-range>" port port="5001" protocol="tcp" accept'
firewall-cmd --reload
```

## 监控和日志

### 日志位置
```bash
# 应用日志
/opt/xiangxin-guardrails/data/logs/

# 检测结果日志 (当STORE_DETECTION_RESULTS=false时)
/opt/xiangxin-guardrails/data/logs/detection/

# Docker日志
docker-compose logs detection-service
docker-compose logs admin-service
```

### 监控指标

#### 健康检查端点
```bash
# 检测服务健康检查
curl http://localhost:5000/health

# 管理服务健康检查  
curl http://localhost:5001/health

# 详细系统信息
curl http://localhost:5001/config/system-info \
  -H "Authorization: Bearer <admin-token>"
```

#### 缓存状态监控
```bash
# 获取缓存状态
curl http://localhost:5001/config/cache-info \
  -H "Authorization: Bearer <admin-token>"

# 手动刷新缓存
curl -X POST http://localhost:5001/config/cache/refresh \
  -H "Authorization: Bearer <admin-token>"
```

### 日志轮转配置

```bash
# 创建logrotate配置
sudo tee /etc/logrotate.d/xiangxin-guardrails << 'EOF'
/opt/xiangxin-guardrails/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}

/opt/xiangxin-guardrails/data/logs/detection/*.jsonl {
    daily
    rotate 90
    compress  
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

## 备份和恢复

### 数据备份

```bash
#!/bin/bash
# 备份脚本示例

BACKUP_DIR="/opt/backups/xiangxin-guardrails"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec -T postgres pg_dump -U guardrails guardrails_db > $BACKUP_DIR/database_$DATE.sql

# 备份配置文件
cp .env $BACKUP_DIR/env_$DATE

# 备份数据目录
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C /opt/xiangxin-guardrails data/

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 数据恢复

```bash
#!/bin/bash
# 恢复脚本示例

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql>"
    exit 1
fi

# 停止服务
docker-compose stop detection-service admin-service

# 恢复数据库
docker-compose exec -T postgres psql -U guardrails -d guardrails_db < $BACKUP_FILE

# 重启服务
docker-compose start detection-service admin-service
```

## 性能优化

### 数据库优化

```sql
-- PostgreSQL配置优化
-- 在postgresql.conf中设置

shared_buffers = 256MB                # 25% of RAM
effective_cache_size = 1GB            # 75% of RAM  
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1                # For SSD
```

### 应用优化

```bash
# 增加检测服务并发数
DETECTION_UVICORN_WORKERS=64
DETECTION_MAX_CONCURRENT_REQUESTS=800

# 调整缓存TTL
KEYWORD_CACHE_TTL=600    # 10分钟
TEMPLATE_CACHE_TTL=1200  # 20分钟

# 启用HTTP/2 (如果使用反向代理)
# nginx配置示例
server {
    listen 443 ssl http2;
    
    location /v1/guardrails {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

## 故障排查

### 常见问题

#### 1. 服务启动失败
```bash
# 检查日志
docker-compose logs detection-service

# 检查配置
grep -v '^#' .env | grep -v '^$'

# 检查数据库连接
docker-compose exec postgres psql -U guardrails -d guardrails_db -c "SELECT 1;"
```

#### 2. 检测API返回500错误
```bash
# 检查模型服务状态
curl http://localhost:58002/health

# 检查数据库连接
curl http://localhost:5000/health

# 查看详细错误
docker-compose logs -f detection-service
```

#### 3. JWT认证失败
```bash
# 验证JWT密钥一致性
echo $JWT_SECRET_KEY

# 测试token生成 (Python)
python3 -c "
import jwt
token = jwt.encode({'user_id':'test','exp':9999999999}, 'your-secret', algorithm='HS256')
print(token)
"
```

#### 4. 数据库连接问题
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U guardrails

# 检查连接配置
echo $DATABASE_URL

# 测试连接
docker-compose exec postgres psql -U guardrails -d guardrails_db
```

### 性能问题排查

#### 检测延迟高
```bash
# 检查模型服务响应时间
time curl -X POST http://localhost:58002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'

# 检查数据库查询性能
docker-compose exec postgres psql -U guardrails -d guardrails_db \
  -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### 内存使用过高
```bash
# 检查各服务内存使用
docker stats

# 检查数据库缓存命中率
docker-compose exec postgres psql -U guardrails -d guardrails_db \
  -c "SELECT * FROM pg_stat_database WHERE datname = 'guardrails_db';"
```

## 升级指南

### 版本升级步骤

```bash
# 1. 备份数据
./backup.sh

# 2. 停止服务
docker-compose down

# 3. 更新镜像版本
# 编辑docker-compose.yml，更新image版本号

# 4. 拉取新镜像
docker-compose pull

# 5. 运行数据库迁移 (如果需要)
docker-compose run --rm admin-service python -m alembic upgrade head

# 6. 启动服务
docker-compose up -d

# 7. 验证升级
curl http://localhost:5000/health
```

### 配置文件迁移

```bash
# 比较配置文件差异
diff .env .env.example

# 合并新配置项
grep -v '^#\|^$' .env.example | while read line; do
    key=$(echo $line | cut -d'=' -f1)
    if ! grep -q "^$key=" .env; then
        echo "Adding new config: $line"
        echo "$line" >> .env
    fi
done
```

## 安全加固

### 系统安全

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 配置防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 3. 禁用不必要的服务
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# 4. 配置SSH安全
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
AllowUsers your-user
```

### 应用安全

```bash
# 1. 使用非root用户运行
# docker-compose.yml
user: "1001:1001"

# 2. 限制容器权限
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp

# 3. 使用secrets管理敏感信息
# 而不是直接在环境变量中存储密码
```

## 技术支持

### 联系方式
- **技术支持邮箱**: wanglei@xiangxinai.cn
- **紧急联系电话**: [提供具体电话]
- **在线文档**: https://docs.xiangxinai.cn/guardrails

### 支持服务等级

| 等级 | 响应时间 | 解决时间 | 覆盖范围 |
|------|----------|----------|----------|
| 一般问题 | 1个工作日 | 3个工作日 | 配置、使用咨询 |
| 重要问题 | 4小时 | 1个工作日 | 功能异常 |
| 紧急问题 | 1小时 | 8小时 | 系统无法使用 |

---

*文档版本: v1.0*  
*更新时间: 2024-01-01*