#!/bin/bash
# 停止所有服务的脚本

echo "Stopping Xiangxin Guardrails - All Services"
echo "==========================================="

# 检查PID文件是否存在
if [ -f "/tmp/xiangxin_services.pid" ]; then
    PIDS=$(cat /tmp/xiangxin_services.pid)
    echo "Found running services with PIDs: $PIDS"
    
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping service with PID: $PID"
            kill $PID
        else
            echo "Service with PID $PID is not running"
        fi
    done
    
    # 清理PID文件
    rm -f /tmp/xiangxin_services.pid
    echo "All services stopped successfully!"
else
    echo "No PID file found. Trying to find and stop services by name..."
    
    # 查找并停止Python进程
    pkill -f "start_detection_service.py"
    pkill -f "start_admin_service.py"
    pkill -f "start_proxy_service.py"
    
    echo "Attempted to stop all Xiangxin services"
fi

echo "Done!"