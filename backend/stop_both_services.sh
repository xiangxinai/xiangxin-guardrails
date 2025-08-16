#!/bin/bash
# 停止双服务脚本

set -e

echo "Stopping Xiangxin Guardrails Services..."
echo "========================================"

# 从配置文件获取日志目录
LOG_DIR=$(python3 -c "from config import settings; print(settings.log_dir)" 2>/dev/null || echo "logs")

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