# 象信AI安全护栏平台 - PostgreSQL部署指南

## 概述

本指南将帮助您部署使用PostgreSQL数据库的象信AI安全护栏平台，并实现异步日志写入机制以优化API性能。

## 架构特性

### 统一数据目录管理

- **数据目录**：`~/xiangxin-guardrails-data/`
  - 数据库数据：`~/xiangxin-guardrails-data/db/`
  - 应用日志：`~/xiangxin-guardrails-data/logs/`
  - 检测日志：`~/xiangxin-guardrails-data/logs/detection/`

### 性能优化方案

1. **异步日志写入**：检测结果立即写入本地JSON日志文件，API立即返回响应
2. **后台数据同步**：独立的后台服务定期将日志数据同步到PostgreSQL数据库
3. **PostgreSQL高性能**：使用PostgreSQL支持更高的并发和更大的数据量

### 性能优势

- **检测API响应时间大幅降低**：不再等待数据库写入
- **更高的并发处理能力**：PostgreSQL支持更好的并发性能
- **数据完整性保障**：即使数据库繁忙，日志文件也能保证数据不丢失
- **可扩展性**：支持更大的数据量和更多的并发请求

## 部署步骤

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 设置PostgreSQL数据库

运行PostgreSQL设置脚本：

```bash
chmod +x scripts/setup_postgres.sh
./scripts/setup_postgres.sh
```

或手动启动Docker容器：

```bash
docker run -d \
  --name xiangxin-postgres \
  -e POSTGRES_USER=xiangxin \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=xiangxin_guardrails \
  -p 54321:5432 \
  -v ~/xiangxin-guardrails-data/db:/var/lib/postgresql/data \
  postgres:16-alpine
```

### 3. 配置环境变量

复制并编辑环境配置文件：

```bash
cp .env.example .env
```

确保 `.env` 文件中的配置正确：

```bash
# 数据目录配置
DATA_DIR=~/xiangxin-guardrails-data

# 数据库配置
DATABASE_URL=postgresql://xiangxin:xiangxin%4020250808@localhost:54321/xiangxin_guardrails
```

### 4. 初始化PostgreSQL数据库

```bash
python scripts/init_postgres.py
```

### 5. 迁移现有数据（可选）

如果您有现有的SQLite数据需要迁移：

```bash
python scripts/migrate_to_postgres.py [sqlite_db_path]
```

默认会从 `./data/guardrails.db` 迁移数据。

### 6. 启动应用

```bash
python main.py
```

## 新功能和API

### 数据同步管理API

#### 1. 强制同步数据

```bash
POST /api/v1/sync/force
```

可选参数：
- `start_date`: 开始日期（YYYYMMDD格式）
- `end_date`: 结束日期（YYYYMMDD格式）

示例：
```bash
curl -X POST "http://localhost:5000/api/v1/sync/force?start_date=20250101&end_date=20250131" \
  -H "Authorization: Bearer your-api-key"
```

#### 2. 获取同步状态

```bash
GET /api/v1/sync/status
```

#### 3. 重启同步服务

```bash
POST /api/v1/sync/restart
```

## 日志文件结构

检测结果日志保存在：`~/xiangxin-guardrails-data/logs/detection/`

文件格式：`detection_YYYYMMDD.jsonl`

每行是一个JSON记录，包含完整的检测信息：

```json
{
  "request_id": "guardrails-xxx",
  "user_id": null,
  "content": "检测内容",
  "suggest_action": "通过",
  "suggest_answer": null,
  "model_response": "safe",
  "ip_address": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "security_risk_level": "无风险",
  "security_categories": [],
  "compliance_risk_level": "无风险", 
  "compliance_categories": [],
  "created_at": "2025-01-01T12:00:00",
  "hit_keywords": null,
  "logged_at": "2025-01-01T12:00:00.123456"
}
```

## 监控和维护

### 查看日志文件

```bash
# 查看当天的检测日志
tail -f ~/xiangxin-guardrails-data/logs/detection/detection_$(date +%Y%m%d).jsonl

# 统计今天的检测数量
wc -l ~/xiangxin-guardrails-data/logs/detection/detection_$(date +%Y%m%d).jsonl
```

### 数据库连接

```bash
# 连接PostgreSQL数据库
docker exec -it xiangxin-postgres psql -U xiangxin -d xiangxin_guardrails

# 查看检测结果统计
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE suggest_action = '通过') as passed,
    COUNT(*) FILTER (WHERE suggest_action = '阻断') as blocked,
    COUNT(*) FILTER (WHERE suggest_action = '代答') as replied
FROM detection_results 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at) 
ORDER BY date DESC;
```

### 性能监控

```bash
# 检查同步服务状态
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:5000/api/v1/sync/status

# 查看应用日志
tail -f ~/xiangxin-guardrails-data/logs/app.log
```

## 故障排除

### 1. PostgreSQL连接问题

检查容器状态：
```bash
docker ps | grep postgres
docker logs xiangxin-postgres
```

### 2. 日志写入问题

检查日志目录权限：
```bash
ls -la ~/xiangxin-guardrails-data/logs/
```

### 3. 数据同步问题

手动触发同步：
```bash
curl -X POST -H "Authorization: Bearer your-api-key" \
  http://localhost:5000/api/v1/sync/force
```

重启同步服务：
```bash
curl -X POST -H "Authorization: Bearer your-api-key" \
  http://localhost:5000/api/v1/sync/restart
```

## 目录结构

部署完成后的目录结构：

```
~/xiangxin-guardrails-data/
├── db/                          # PostgreSQL数据库文件
├── logs/                        # 应用日志目录
│   ├── app.log                  # 应用主日志
│   └── detection/               # 检测结果日志
│       ├── detection_20250101.jsonl
│       ├── detection_20250102.jsonl
│       └── ...
```

## 性能基准测试

迁移完成后，您可以进行简单的性能测试：

```bash
# 测试检测API响应时间
time curl -X POST "http://localhost:5000/v1/guardrails" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "Xiangxin-Guardrails-Text",
    "messages": [{"role": "user", "content": "测试内容"}]
  }'
```

预期改进：
- **响应时间**：从几百毫秒降低到几十毫秒
- **吞吐量**：提升3-5倍
- **并发能力**：支持更多并发请求

## 总结

这次升级实现了：

1. ✅ **性能大幅提升**：异步日志写入，API响应速度提升
2. ✅ **数据库升级**：从SQLite迁移到PostgreSQL
3. ✅ **高可用性**：即使数据库繁忙也不影响API响应
4. ✅ **数据完整性**：多重保障确保数据不丢失
5. ✅ **可扩展性**：支持更大规模的部署
6. ✅ **易于监控**：提供完整的监控和管理API

现在您的象信AI安全护栏平台可以处理更高的并发访问，同时保持优秀的性能表现！