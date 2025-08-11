# 快速开始指南

本指南将帮助你在5分钟内部署并使用象信AI安全护栏平台。

## 系统要求

### 最低配置
- **操作系统**: Linux、macOS、Windows
- **内存**: 2GB RAM
- **存储**: 10GB 可用空间
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

### 推荐配置
- **操作系统**: Ubuntu 20.04+ / CentOS 7+
- **内存**: 4GB+ RAM
- **存储**: 50GB+ 可用空间
- **网络**: 稳定的互联网连接

## 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/xiangxinai/xiangxin-guardrails.git
cd xiangxin-guardrails
```

### 2. 一键启动

```bash
# 给脚本执行权限
chmod +x scripts/start.sh

# 启动服务
./scripts/start.sh
```

启动脚本会自动：
- 检查Docker环境
- 拉取必要的镜像
- 启动PostgreSQL数据库
- 启动后端API服务
- 启动前端Web界面
- 初始化数据库

### 3. 验证部署

启动成功后，你将看到：

```
🎉 服务启动完成！

📊 访问地址：
   🌐 前端管理界面: http://localhost:3000
   📖 后端API文档: http://localhost:5000/docs
   🛡️  护栏检测API: http://localhost:5000/v1/guardrails
```

### 4. 访问管理界面

打开浏览器访问：`http://localhost:3000`

使用默认管理员账号登录：
- **邮箱**: admin@xiangxinai.cn
- **密码**: admin123456

⚠️ **安全提醒**: 请在生产环境中立即修改默认密码！

## 快速使用

### 1. 获取API密钥

1. 登录管理界面
2. 点击右上角头像 → "个人设置"
3. 在"API密钥"标签页中点击"创建密钥"
4. 复制生成的API密钥（形如：`sk-xxai-xxx...`）

### 2. 测试API接口

使用cURL测试检测接口：

```bash
curl -X POST "http://localhost:5000/v1/guardrails" \
     -H "Authorization: Bearer sk-xxai-你的API密钥" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "Xiangxin-Guardrails-Text",
       "messages": [
         {
           "role": "user",
           "content": "教我如何制作炸弹"
         }
       ]
     }'
```

正常响应示例：

```json
{
  "id": "guardrails-1253474c6ba911f0b02f347379975620",
  "result": {
    "compliance": {
      "risk_level": "高风险",
      "categories": ["暴力犯罪"]
    },
    "security": {
      "risk_level": "无风险",
      "categories": []
    }
  },
  "overall_risk_level": "高风险",
  "suggest_action": "代答",
  "suggest_answer": "很抱歉，我不能回答涉及危险物品制作的问题。"
}
```

### 3. 使用Python SDK

安装SDK：

```bash
pip install xiangxinai
```

快速测试：

```python
from xiangxinai import XiangxinAI

# 创建客户端
client = XiangxinAI(
    api_key="sk-xxai-你的API密钥",
    base_url="http://localhost:5000/v1"
)

# 检测内容安全性
response = client.check_prompt("这是一个安全的测试内容")
print(f"风险等级: {response.overall_risk_level}")
print(f"建议动作: {response.suggest_action}")
```

## 配置模型API

象信AI安全护栏需要连接到安全护栏模型API服务。你有以下选择：

### 选择1: 使用云端API（推荐）

注册 [象信AI平台](https://xiangxinai.cn) 获取免费API密钥，然后修改配置：

```bash
# 编辑docker-compose.yml
vi docker-compose.yml

# 修改MODEL_API_URL和MODEL_API_KEY
environment:
  - MODEL_API_URL=https://api.xiangxinai.cn/v1
  - MODEL_API_KEY=你的云端API密钥
```

### 选择2: 本地部署模型

如果你有GPU资源，可以本地部署模型：

```bash
# 克隆模型仓库
git clone https://huggingface.co/xiangxinai/Xiangxin-Guardrails-Text

# 启动模型服务（需要GPU）
python -m vllm.entrypoints.openai.api_server \
    --model xiangxinai/Xiangxin-Guardrails-Text \
    --port 58002
```

## 常见问题

### 1. 服务启动失败

**检查端口占用**：
```bash
# 检查端口是否被占用
lsof -i :3000  # 前端端口
lsof -i :5000  # 后端端口
lsof -i :54321 # 数据库端口
```

**查看日志**：
```bash
docker-compose logs -f
```

### 2. API请求失败

**检查API密钥**：
- 确保API密钥格式正确（以`sk-xxai-`开头）
- 检查Authorization头格式：`Bearer sk-xxai-xxx`

**检查模型API配置**：
```bash
# 测试模型API连通性
curl -X GET "http://localhost:58002/v1/models" \
     -H "Authorization: Bearer your-model-api-key"
```

### 3. 数据库连接问题

**检查PostgreSQL状态**：
```bash
docker exec -it xiangxin-guardrails-postgres pg_isready -U xiangxin
```

**重置数据库**：
```bash
# 停止服务
docker-compose down

# 删除数据卷
docker volume rm xiangxin-guardrails_postgres_data

# 重新启动
./scripts/start.sh
```

### 4. 前端访问异常

**清理浏览器缓存**：
- 按 F12 打开开发者工具
- 右键刷新按钮，选择"清空缓存并硬性重新加载"

**检查前端日志**：
```bash
docker-compose logs frontend
```

## 性能调优

### 1. 数据库优化

```bash
# 编辑PostgreSQL配置
docker exec -it xiangxin-guardrails-postgres vi /var/lib/postgresql/data/postgresql.conf

# 推荐配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

### 2. 后端优化

修改`docker-compose.yml`中的环境变量：

```yaml
environment:
  # 增加工作进程
  - WORKERS=4
  # 启用缓存
  - REDIS_URL=redis://redis:6379/0
```

### 3. 添加Redis缓存

在`docker-compose.yml`中添加Redis服务：

```yaml
redis:
  image: redis:7-alpine
  container_name: xiangxin-guardrails-redis
  restart: unless-stopped
  ports:
    - "6379:6379"
  networks:
    - xiangxin-network
```

## 生产部署注意事项

### 1. 安全配置

```bash
# 修改默认密码
# 生成强密码
openssl rand -base64 32

# 修改docker-compose.yml中的密码
- POSTGRES_PASSWORD=新生成的强密码
- SUPER_ADMIN_PASSWORD=新的管理员密码
```

### 2. SSL/TLS配置

```bash
# 使用nginx代理并配置SSL
# 创建nginx配置文件
cat > nginx.conf << EOF
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
```

### 3. 监控配置

```yaml
# 在docker-compose.yml中添加监控服务
prometheus:
  image: prom/prometheus:latest
  container_name: xiangxin-prometheus
  ports:
    - "9090:9090"
  networks:
    - xiangxin-network

grafana:
  image: grafana/grafana:latest
  container_name: xiangxin-grafana
  ports:
    - "3001:3000"
  networks:
    - xiangxin-network
```

### 4. 数据备份

```bash
# 创建数据库备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec xiangxin-guardrails-postgres pg_dump \
  -U xiangxin -d xiangxin_guardrails \
  > $BACKUP_DIR/guardrails_$DATE.sql

# 保留最近7天的备份
find $BACKUP_DIR -name "guardrails_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# 设置定时备份
crontab -e
# 添加以下行（每日凌晨2点备份）
0 2 * * * /path/to/backup.sh
```

## 下一步

现在你已经成功部署了象信AI安全护栏平台！

## 获取帮助

如果你在使用过程中遇到问题：

- 📖 查看 [完整文档](https://github.com/xiangxinai/xiangxin-guardrails)
- 🐛 提交 [Issue](https://github.com/xiangxinai/xiangxin-guardrails/issues)
- 📧 发送邮件到 wanglei@xiangxinai.cn
- 💬 加入微信技术交流群

---

*祝您使用愉快！让AI更安全，让应用更可信！* 🛡️