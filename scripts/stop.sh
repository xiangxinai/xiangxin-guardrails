#!/bin/bash

# 象信AI安全护栏平台停止脚本

echo "🛡️  象信AI安全护栏平台停止脚本"
echo "========================================"

# 停止服务
echo "🛑 停止服务..."
docker-compose down

# 清理无用的容器和镜像
read -p "是否清理无用的Docker镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理无用镜像..."
    docker system prune -f
fi

echo "✅ 服务已停止！"