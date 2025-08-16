# 双服务架构说明

## 架构优化

原有单一服务存在的问题：
- **连接数爆炸**：32个worker × 150连接 = 4,800个数据库连接
- **资源浪费**：管理平台API不需要高并发却占用大量资源
- **性能瓶颈**：高并发检测和低频管理操作混合在一起

## 新架构

### 1. 检测服务 (detection_service.py)
**职责**：处理高并发检测API请求
- **端口**：5000
- **路由**：`/v1/guardrails`
- **Workers**：32个
- **连接池**：2 + 3 = 5 per worker（仅用于认证）
- **总连接数**：32 × 5 = 160个连接
- **优化**：
  - 只做认证查询和写日志文件
  - 不写数据库（DetectionResult）
  - 使用专用轻量级GuardrailService
  - 最小化数据库连接

### 2. 管理服务 (admin_service.py)
**职责**：处理管理平台API请求
- **端口**：5001
- **路由**：`/api/v1/*`
- **Workers**：2个
- **连接池**：3 + 5 = 8 per worker
- **总连接数**：2 × 8 = 16个连接
- **功能**：
  - 完整管理功能、用户切换、数据同步
  - 日志文件导入数据库服务
  - 检测结果查询和统计

## 性能提升

### 连接数对比
```
原架构：32 × 150 = 4,800 连接
新架构：160 + 16 = 176 连接
优化比例：96% 减少
```

### 资源分配
- **检测服务**：专注高并发，只做认证+写日志，极简数据库使用
- **管理服务**：专注功能完整性，负责日志导入数据库，资源节约

### 数据流架构
```
检测API请求 → 检测服务 → 认证缓存 + 写日志文件
日志文件 → 管理服务 → 日志导入器 → 数据库
管理API请求 → 管理服务 → 数据库查询
```

## 启动方式

### 方式一：双服务启动（推荐）
```bash
# 启动两个服务
./start_both_services.sh

# 停止两个服务
./stop_both_services.sh
```

### 方式二：单独启动
```bash
# 只启动检测服务
python3 start_detection_service.py

# 只启动管理服务
python3 start_admin_service.py
```

### 方式三：传统方式（向后兼容）
```bash
# 使用原有的单一服务
python3 main.py
```

## 配置说明

### 环境变量
```env
# 检测服务（高并发）
DETECTION_PORT=5000
DETECTION_UVICORN_WORKERS=32
DETECTION_MAX_CONCURRENT_REQUESTS=400

# 管理服务（低并发）
ADMIN_PORT=5001
ADMIN_UVICORN_WORKERS=2
ADMIN_MAX_CONCURRENT_REQUESTS=50
```

### 数据库连接池
```python
# 检测服务引擎（极简）
detection_engine = create_engine(
    pool_size=2,      # 极小连接池（仅认证）
    max_overflow=3    # 极小溢出连接
)

# 管理服务引擎
admin_engine = create_engine(
    pool_size=3,      # 基础连接池
    max_overflow=5    # 溢出连接
)
```

## API 访问

### 检测API
```
POST http://localhost:5000/v1/guardrails
GET  http://localhost:5000/health
```

### 管理API
```
POST http://localhost:5001/api/v1/auth/login
GET  http://localhost:5001/api/v1/dashboard/stats
GET  http://localhost:5001/health
```

## 监控建议

### 日志文件
- 检测服务：`logs/detection_service.log`
- 管理服务：`logs/admin_service.log`

### 监控指标
- 数据库连接数（检测服务应该很少）
- API响应时间
- 内存使用情况
- Worker负载分布
- 日志文件处理延迟
- 日志导入数据库成功率

## 部署建议

### 生产环境
1. 使用反向代理（Nginx）统一入口
2. 设置健康检查
3. 配置日志轮转
4. 监控资源使用

### Nginx 配置示例
```nginx
upstream detection_service {
    server 127.0.0.1:5000;
}

upstream admin_service {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    
    location /v1/guardrails {
        proxy_pass http://detection_service;
    }
    
    location /api/v1/ {
        proxy_pass http://admin_service;
    }
}
```