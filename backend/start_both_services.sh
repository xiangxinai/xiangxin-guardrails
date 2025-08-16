#!/bin/bash
# 启动双服务脚本 - 分别启动检测服务和管理服务

set -e

echo "Starting Xiangxin Guardrails Dual Services..."
echo "================================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# 从.env文件获取数据目录
source .env
if [ -z "$DATA_DIR" ]; then
    echo "Error: DATA_DIR not set in .env file"
    exit 1
fi

# 设置日志目录为数据目录下的logs子目录
LOG_DIR="$DATA_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 启动检测服务（高并发）
echo "Starting Detection Service (High Concurrency)..."
nohup python3 start_detection_service.py > "$LOG_DIR/detection_service.log" 2>&1 &
DETECTION_PID=$!
echo "Detection Service started with PID: $DETECTION_PID"

# 等待检测服务启动
sleep 3

# 启动管理服务（低并发）
echo "Starting Admin Service (Low Concurrency)..."
nohup python3 start_admin_service.py > "$LOG_DIR/admin_service.log" 2>&1 &
ADMIN_PID=$!
echo "Admin Service started with PID: $ADMIN_PID"

# 保存PID文件
echo $DETECTION_PID > "$LOG_DIR/detection_service.pid"
echo $ADMIN_PID > "$LOG_DIR/admin_service.pid"

echo "================================================"
echo "Both services started successfully!"
echo ""
echo "Detection Service:"
echo "  - PID: $DETECTION_PID"
echo "  - Port: ${DETECTION_PORT:-5000}"
echo "  - API: /v1/guardrails"
echo "  - Log: $LOG_DIR/detection_service.log"
echo ""
echo "Admin Service:"
echo "  - PID: $ADMIN_PID" 
echo "  - Port: ${ADMIN_PORT:-5001}"
echo "  - API: /api/v1/*"
echo "  - Log: $LOG_DIR/admin_service.log"
echo ""
echo "Data Directory: $DATA_DIR"
echo "Log Directory: $LOG_DIR"
echo ""
echo "To stop services:"
echo "  ./stop_both_services.sh"
echo ""
echo "To check logs:"
echo "  tail -f $LOG_DIR/detection_service.log"
echo "  tail -f $LOG_DIR/admin_service.log"