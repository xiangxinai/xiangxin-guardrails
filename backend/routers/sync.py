from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, date
from services.data_sync_service import data_sync_service
from services.async_logger import async_detection_logger
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Data Sync"])

@router.post("/sync/force")
async def force_sync_data(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYYMMDD)")
):
    """
    强制同步日志数据到数据库
    
    Args:
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD
    """
    try:
        date_range = None
        if start_date and end_date:
            # 验证日期格式
            try:
                datetime.strptime(start_date, '%Y%m%d')
                datetime.strptime(end_date, '%Y%m%d')
                date_range = (start_date, end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYYMMDD 格式")
        
        # 执行强制同步
        await data_sync_service.force_sync(date_range)
        
        return {
            "status": "success",
            "message": "数据同步完成",
            "date_range": date_range,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Force sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

@router.get("/sync/status")
async def get_sync_status():
    """
    获取数据同步服务状态
    """
    try:
        # 获取日志文件信息
        log_files = async_detection_logger.get_log_files()
        
        # 统计日志文件信息
        file_info = []
        for log_file in log_files[-5:]:  # 只显示最近5个文件
            try:
                stat = log_file.stat()
                file_info.append({
                    "filename": log_file.name,
                    "size_bytes": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except:
                continue
        
        return {
            "sync_service_running": data_sync_service._running,
            "async_logger_running": async_detection_logger._running,
            "recent_log_files": file_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get sync status failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.post("/sync/restart")
async def restart_sync_service():
    """
    重启数据同步服务
    """
    try:
        # 停止服务
        await data_sync_service.stop()
        await async_detection_logger.stop()
        
        # 启动服务
        await async_detection_logger.start()
        await data_sync_service.start()
        
        return {
            "status": "success",
            "message": "数据同步服务重启完成",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Restart sync service failed: {e}")
        raise HTTPException(status_code=500, detail=f"重启失败: {str(e)}")