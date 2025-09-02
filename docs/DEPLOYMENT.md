# 部署说明

## Docker Compose 部署（推荐）

使用Docker Compose是最简单的部署方式，所有服务会自动配置好网络连接。

象信AI安全护栏2.0采用三服务架构：
- **管理服务** (5000端口)：处理管理平台API 
- **检测服务** (5001端口)：高并发护栏检测API
- **代理服务** (5002端口)：安全网关反向代理 🆕

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f admin-service      # 管理服务
docker compose logs -f detection-service  # 检测服务
docker compose logs -f proxy-service      # 代理服务
```

## 本地手动部署

如果需要手动分别启动各个服务（开发调试用），需要注意以下配置：

### 1. 环境配置

复制并修改环境配置文件：

```bash
cp backend/.env.local.example backend/.env
```

关键配置项：
- `DETECTION_HOST=localhost`  # 本地环境使用localhost
- `DATABASE_URL=postgresql://...`  # 数据库连接
- 其他配置根据实际情况修改

### 2. 启动顺序

1. 启动PostgreSQL数据库
2. 启动detection服务（端口5001）
3. 启动admin服务（端口5000）
4. 启动proxy服务（端口5002） 🆕
5. 启动frontend（端口3000）

### 3. 服务间连接配置

系统会根据 `DETECTION_HOST` 环境变量自动选择连接方式：

- **Docker环境**: `DETECTION_HOST=detection-service`（使用Docker服务名）
- **本地环境**: `DETECTION_HOST=localhost`（使用本地主机）

## 环境变量说明

| 变量名 | Docker默认值 | 本地默认值 | 说明 |
|-------|-------------|-----------|------|
| `DETECTION_HOST` | `detection-service` | `localhost` | 检测服务主机名 |
| `DETECTION_PORT` | `5001` | `5001` | 检测服务端口 |
| `ADMIN_PORT` | `5000` | `5000` | 管理服务端口 |
| `PROXY_PORT` | `5002` | `5002` | 代理服务端口 🆕 |

## 故障排除

### 连接失败问题

如果看到 "Guardrail API call failed: All connection attempts failed" 错误：

1. 检查 `DETECTION_HOST` 配置是否正确
2. 确认detection-service正在运行且可访问
3. 验证API密钥是否有效

### 环境切换

从Docker切换到本地开发：
```bash
export DETECTION_HOST=localhost
```

从本地切换到Docker：
```bash
export DETECTION_HOST=detection-service
```