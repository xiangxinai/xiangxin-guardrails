#!/bin/bash
# 启动所有三个服务的脚本

echo "Starting Xiangxin Guardrails - All Services"
echo "==========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# 设置环境变量
export PYTHONPATH="$PWD:$PYTHONPATH"

# 启动检测服务（后台运行）
echo "Starting Detection Service on port 5001..."
python3 start_detection_service.py &
DETECTION_PID=$!
echo "Detection Service PID: $DETECTION_PID"

# 等待一秒
sleep 1

# 启动管理服务（后台运行）
echo "Starting Admin Service on port 5000..."
python3 start_admin_service.py &
ADMIN_PID=$!
echo "Admin Service PID: $ADMIN_PID"

# 等待一秒
sleep 1

# 启动代理服务（后台运行）
echo "Starting Proxy Service on port 5002..."
python3 start_proxy_service.py &
PROXY_PID=$!
echo "Proxy Service PID: $PROXY_PID"

echo ""
echo "All services started successfully!"
echo "================================="
echo "Admin Service:     http://localhost:5000 (PID: $ADMIN_PID)"
echo "Detection Service: http://localhost:5001 (PID: $DETECTION_PID)"
echo "Proxy Service:     http://localhost:5002 (PID: $PROXY_PID)"
echo ""
echo "To stop all services, run:"
echo "kill $DETECTION_PID $ADMIN_PID $PROXY_PID"
echo ""
echo "Service logs can be found in the data/logs directory"

# 保存PID到文件，方便停止
echo "$DETECTION_PID $ADMIN_PID $PROXY_PID" > /tmp/xiangxin_services.pid

# 等待用户输入来停止服务
echo "Press Ctrl+C to stop all services"
trap 'echo "Stopping all services..."; kill $DETECTION_PID $ADMIN_PID $PROXY_PID 2>/dev/null; exit 0' INT

# 保持脚本运行
wait