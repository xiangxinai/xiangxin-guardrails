#!/bin/bash

# 象信AI安全护栏平台启动脚本

echo "🛡️  象信AI安全护栏平台启动脚本"
echo "========================================"

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "   安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    echo "   安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

# 检查Docker服务是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker服务未启动，请先启动Docker服务"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs backend/config

# 设置权限
chmod 755 logs backend/config

# 检查端口占用
echo "🔍 检查端口占用..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口3000已被占用，请先停止相关服务或修改docker-compose.yml中的端口配置"
fi

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口5000已被占用，请先停止相关服务或修改docker-compose.yml中的端口配置"
fi

if lsof -Pi :54321 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口54321已被占用，请先停止相关服务或修改docker-compose.yml中的端口配置"
fi

# 检查是否存在旧版本容器
echo "🧹 清理旧版本容器..."
docker-compose down --remove-orphans 2>/dev/null || true

# 拉取最新镜像
echo "📥 拉取PostgreSQL镜像..."
docker pull postgres:15-alpine

# 启动服务
echo "🚀 启动服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

# 等待数据库启动
echo "⏳ 等待数据库启动..."
for i in {1..30}; do
    if docker exec xiangxin-guardrails-postgres pg_isready -U xiangxin -d xiangxin_guardrails >/dev/null 2>&1; then
        echo "✅ 数据库启动成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 数据库启动超时，请检查日志: docker-compose logs postgres"
        exit 1
    fi
    sleep 2
done

# 等待后端服务启动
echo "⏳ 等待后端服务启动..."
for i in {1..60}; do
    if curl -f http://localhost:5000/health >/dev/null 2>&1; then
        echo "✅ 后端服务启动成功"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ 后端服务启动超时，请检查日志: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

# 等待前端服务启动
echo "⏳ 等待前端服务启动..."
for i in {1..30}; do
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ 前端服务启动成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  前端服务可能需要更长时间启动，请稍后访问或查看日志"
    fi
    sleep 2
done

# 检查服务状态
echo "🔍 检查服务状态..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

echo ""
echo "🎉 服务启动完成！"
echo ""
echo "📊 访问地址："
echo "   🌐 前端管理界面: http://localhost:3000"
echo "   📖 后端API文档: http://localhost:5000/docs"
echo "   🛡️ 护栏检测API: http://localhost:5001/v1/guardrails"
echo "   🐘 PostgreSQL数据库: localhost:54321"
echo ""
echo "🔑 默认管理员账号："
echo "   邮箱: admin@xiangxinai.cn"
echo "   密码: admin123456"
echo "   ⚠️  请在生产环境中修改默认密码！"
echo ""
echo "🔧 常用命令："
echo "   查看所有日志: docker-compose logs -f"
echo "   查看后端日志: docker-compose logs -f backend"
echo "   查看数据库日志: docker-compose logs -f postgres"
echo "   停止所有服务: docker-compose down"
echo "   重启所有服务: docker-compose restart"
echo "   进入数据库: docker exec -it xiangxin-guardrails-postgres psql -U xiangxin -d xiangxin_guardrails"
echo ""
echo "📚 文档："
echo "   项目文档: https://github.com/xiangxinai/xiangxin-guardrails"
echo "   API文档: http://localhost:5000/docs"
echo ""
echo "📧 技术支持: wanglei@xiangxinai.cn"