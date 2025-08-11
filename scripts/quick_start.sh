#!/bin/bash

# 象信AI安全护栏平台快速启动脚本

echo "🛡️  象信AI安全护栏平台快速启动"
echo "========================================"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data logs

# 设置权限
chmod 755 data logs

# 启动前端（开发模式）
echo "🚀 启动前端服务..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

# 启动后端（开发模式）
echo "🚀 启动后端服务..."
cd backend
pip install -r requirements.txt
python main.py &
BACKEND_PID=$!
cd ..

echo ""
echo "✅ 服务启动中..."
echo ""
echo "📊 访问地址："
echo "   前端管理界面: http://localhost:3000"
echo "   后端API文档: http://localhost:5000/docs"
echo "   护栏API: http://localhost:5000/v1/guardrails"
echo ""
echo "🔧 停止服务："
echo "   Ctrl+C 或运行: kill $FRONTEND_PID $BACKEND_PID"
echo ""
echo "📧 技术支持: wanglei@xiangxinai.cn"

# 等待用户中断
wait