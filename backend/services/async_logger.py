import os
import json
import asyncio
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger()

class AsyncDetectionLogger:
    """异步检测结果日志记录器"""
    
    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            from config import settings
            log_dir = settings.detection_log_dir
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._queue = asyncio.Queue()
        self._writer_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动异步写入任务"""
        if not self._running:
            self._running = True
            self._writer_task = asyncio.create_task(self._writer_loop())
            logger.info("AsyncDetectionLogger started")
        else:
            logger.debug("AsyncDetectionLogger already running, skipping start")
    
    async def stop(self):
        """停止异步写入任务"""
        if self._running:
            self._running = False
            # 发送停止信号
            await self._queue.put(None)
            if self._writer_task:
                await self._writer_task
            logger.info("AsyncDetectionLogger stopped")
    
    async def log_detection(self, detection_data: Dict[str, Any]):
        """记录检测结果到日志"""
        if not self._running:
            await self.start()
        
        # 添加时间戳
        detection_data['logged_at'] = datetime.now().isoformat()
        
        # 加入队列
        await self._queue.put(detection_data)
    
    async def _writer_loop(self):
        """异步写入循环（批量优化版）"""
        current_date = None
        current_file = None
        batch = []
        batch_size = 50  # 批量大小
        last_flush_time = asyncio.get_event_loop().time()
        flush_interval = 2.0  # 2秒强制刷新一次
        
        try:
            while self._running:
                try:
                    # 收集批量数据
                    current_time = asyncio.get_event_loop().time()
                    try:
                        data = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                        
                        # 停止信号
                        if data is None:
                            break
                        
                        batch.append(data)
                        
                        # 检查是否需要写入
                        should_flush = (
                            len(batch) >= batch_size or 
                            (current_time - last_flush_time) >= flush_interval
                        )
                        
                        if should_flush and batch:
                            await self._flush_batch(batch, current_date, current_file)
                            batch.clear()
                            last_flush_time = current_time
                            
                            # 更新文件句柄
                            today = datetime.now().strftime('%Y%m%d')
                            if current_date != today:
                                if current_file:
                                    await current_file.aclose()
                                
                                current_date = today
                                log_file_path = self.log_dir / f"detection_{today}.jsonl"
                                current_file = await aiofiles.open(log_file_path, 'a', encoding='utf-8')
                                logger.debug(f"Opened new log file: {log_file_path}")
                        
                    except asyncio.TimeoutError:
                        # 超时，检查是否需要刷新积累的数据
                        if batch and (current_time - last_flush_time) >= flush_interval:
                            await self._flush_batch(batch, current_date, current_file)
                            batch.clear()
                            last_flush_time = current_time
                        continue
                        
                except Exception as e:
                    logger.error(f"Error in async logger writer loop: {e}")
            
            # 处理剩余的批量数据
            if batch:
                await self._flush_batch(batch, current_date, current_file)
                
        except Exception as e:
            logger.error(f"Fatal error in async logger writer loop: {e}")
        finally:
            if current_file:
                await current_file.aclose()
            logger.info("Async logger writer loop stopped")
    
    async def _flush_batch(self, batch: list, current_date: str, current_file):
        """刷新批量数据到文件"""
        if not batch or not current_file:
            return
            
        try:
            # 批量写入
            lines = []
            for data in batch:
                json_line = json.dumps(data, ensure_ascii=False) + '\n'
                lines.append(json_line)
            
            await current_file.write(''.join(lines))
            await current_file.flush()
            
            logger.debug(f"Flushed {len(batch)} log entries")
            
        except Exception as e:
            logger.error(f"Error flushing batch: {e}")
    
    def get_log_files(self, date_range: Optional[tuple] = None) -> list:
        """获取日志文件列表"""
        pattern = "detection_*.jsonl"
        files = list(self.log_dir.glob(pattern))
        files.sort(key=lambda x: x.name)
        
        if date_range:
            start_date, end_date = date_range
            filtered_files = []
            for file in files:
                try:
                    file_date = file.stem.split('_')[1]
                    if start_date <= file_date <= end_date:
                        filtered_files.append(file)
                except (IndexError, ValueError):
                    continue
            return filtered_files
        
        return files

# 全局实例
async_detection_logger = AsyncDetectionLogger()