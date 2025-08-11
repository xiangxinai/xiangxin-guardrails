#!/bin/bash

# PostgreSQL数据库设置脚本

set -e

echo "象信AI安全护栏平台 - PostgreSQL数据库设置"
echo "==========================================="

# 检查Docker是否已安装
if ! command -v docker &> /dev/null; then
    echo "错误：Docker未安装，请先安装Docker"
    exit 1
fi

# 停止现有容器（如果存在）
echo "停止现有PostgreSQL容器..."
docker stop xiangxin-postgres 2>/dev/null || true
docker rm xiangxin-postgres 2>/dev/null || true

# 创建数据目录
echo "创建数据目录..."
sudo mkdir -p ~/xiangxin-guardrails-data/db
sudo mkdir -p ~/xiangxin-guardrails-data/logs
sudo mkdir -p ~/xiangxin-guardrails-data/logs/detection
sudo chown -R $USER:$USER ~/xiangxin-guardrails-data/

# 启动PostgreSQL容器
echo "启动PostgreSQL容器..."
docker run -d \
  --name xiangxin-postgres \
  -e POSTGRES_USER=xiangxin \
  -e POSTGRES_PASSWORD='xiangxin@20250808' \
  -p 54321:5432 \
  -v ~/xiangxin-guardrails-data/db:/var/lib/postgresql/data \
  postgres:latest

# 等待PostgreSQL启动
echo "等待PostgreSQL启动..."
sleep 10

# 检查连接
echo "检查PostgreSQL连接..."
for i in {1..30}; do
    if docker exec xiangxin-postgres pg_isready -U xiangxin; then
        echo "PostgreSQL启动成功！"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "错误：PostgreSQL启动超时"
        exit 1
    fi
    
    echo "等待PostgreSQL启动... ($i/30)"
    sleep 2
done

# 创建数据库
echo "创建应用数据库..."
docker exec xiangxin-postgres psql -U xiangxin -c "CREATE DATABASE xiangxin_guardrails;" || echo "数据库可能已存在"

echo ""
echo "PostgreSQL数据库设置完成！"
echo "数据库信息："
echo "  主机: localhost"
echo "  端口: 54321"
echo "  用户名: xiangxin"
echo "  密码: xiangxin@20250808"
echo "  数据库: xiangxin_guardrails"
echo ""
echo "连接字符串: postgresql://xiangxin:xiangxin%4020250808@localhost:54321/xiangxin_guardrails"
echo ""
echo "可以使用以下命令连接数据库："
echo "  docker exec -it xiangxin-postgres psql -U xiangxin -d xiangxin_guardrails"