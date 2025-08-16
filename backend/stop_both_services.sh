#!/bin/bash
# 停止双服务脚本

set -e

echo "Stopping Xiangxin Guardrails Services..."
echo "========================================"

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Using default log directory."
    LOG_DIR="logs"
else
    # 从.env文件获取数据目录
    source .env
    if [ -z "$DATA_DIR" ]; then
        echo "Warning: DATA_DIR not set in .env file, using default."
        LOG_DIR="logs"
    else
        LOG_DIR="$DATA_DIR/logs"
    fi
fi

# 停止检测服务
if [ -f "$LOG_DIR/detection_service.pid" ]; then
    DETECTION_PID=$(cat "$LOG_DIR/detection_service.pid")
    if kill -0 $DETECTION_PID 2>/dev/null; then
        echo "Stopping Detection Service (PID: $DETECTION_PID)..."
        kill $DETECTION_PID
        echo "Detection Service stopped."
    else
        echo "Detection Service is not running."
    fi
    rm -f "$LOG_DIR/detection_service.pid"
else
    echo "Detection Service PID file not found."
fi

# 停止管理服务
if [ -f "$LOG_DIR/admin_service.pid" ]; then
    ADMIN_PID=$(cat "$LOG_DIR/admin_service.pid")
    if kill -0 $ADMIN_PID 2>/dev/null; then
        echo "Stopping Admin Service (PID: $ADMIN_PID)..."
        kill $ADMIN_PID
        echo "Admin Service stopped."
    else
        echo "Admin Service is not running."
    fi
    rm -f "$LOG_DIR/admin_service.pid"
else
    echo "Admin Service PID file not found."
fi

echo "========================================"
echo "All services stopped."