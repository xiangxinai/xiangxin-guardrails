import json
import asyncio
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.connection import get_db_session
from database.models import DetectionResult
from services.async_logger import async_detection_logger
from utils.logger import setup_logger

logger = setup_logger()

class DataSyncService:
    """数据同步服务 - 从日志文件同步到PostgreSQL数据库"""
    
    def __init__(self, sync_interval: int = 60):
        """
        初始化数据同步服务
        
        Args:
            sync_interval: 同步间隔（秒），默认60秒
        """
        self.sync_interval = sync_interval
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._processed_files = set()  # 记录已处理的文件，避免重复处理
    
    async def start(self):
        """启动数据同步服务"""
        if not self._running:
            self._running = True
            self._sync_task = asyncio.create_task(self._sync_loop())
            logger.info("DataSyncService started")
        else:
            logger.debug("DataSyncService already running, skipping start")
    
    async def stop(self):
        """停止数据同步服务"""
        if self._running:
            self._running = False
            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
            logger.info("DataSyncService stopped")
    
    async def _sync_loop(self):
        """同步循环"""
        while self._running:
            try:
                await self.sync_data()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data sync loop: {e}")
                # 发生错误时等待更长时间再重试
                await asyncio.sleep(self.sync_interval * 3)
    
    async def sync_data(self):
        """同步数据到数据库"""
        try:
            # 获取需要处理的日志文件
            log_files = await self._get_pending_log_files()
            
            if not log_files:
                logger.debug("No pending log files to process")
                return
            
            logger.info(f"Found {len(log_files)} log files to process")
            
            # 逐个处理日志文件
            for log_file in log_files:
                await self._process_log_file(log_file)
                
        except Exception as e:
            logger.error(f"Error in sync_data: {e}")
    
    async def _get_pending_log_files(self) -> List[Path]:
        """获取待处理的日志文件"""
        # 获取最近3天的日志文件（避免处理过老的文件）
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=2)
        
        date_range = (
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d')
        )
        
        all_files = async_detection_logger.get_log_files(date_range)
        
        # 过滤出未处理的文件
        pending_files = []
        for file_path in all_files:
            # 检查文件是否已被完全处理
            if not await self._is_file_fully_processed(file_path):
                pending_files.append(file_path)
        
        # 按文件名排序，确保按时间顺序处理
        pending_files.sort(key=lambda x: x.name)
        
        return pending_files
    
    async def _is_file_fully_processed(self, file_path: Path) -> bool:
        """检查文件是否已被完全处理"""
        try:
            # 检查文件修改时间，如果是今天的文件且最近修改，可能还在写入
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # 如果文件在5分钟内被修改，认为可能还在写入
            if datetime.now() - last_modified < timedelta(minutes=5):
                return False
                
            # 检查是否在已处理列表中
            return str(file_path) in self._processed_files
            
        except FileNotFoundError:
            return True  # 文件不存在，认为已处理
    
    async def _process_log_file(self, file_path: Path):
        """处理单个日志文件"""
        logger.info(f"Processing log file: {file_path}")
        
        try:
            processed_count = 0
            error_count = 0
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # 解析JSON行
                        detection_data = json.loads(line)
                        
                        # 同步到数据库
                        await self._sync_detection_to_db(detection_data)
                        processed_count += 1
                        
                        # 批量提交，提高性能
                        if processed_count % 100 == 0:
                            logger.debug(f"Processed {processed_count} records from {file_path.name}")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in {file_path}: {line[:100]}...")
                        error_count += 1
                    except Exception as e:
                        logger.error(f"Error processing record in {file_path}: {e}")
                        error_count += 1
            
            # 标记文件为已处理
            self._processed_files.add(str(file_path))
            
            logger.info(f"Completed processing {file_path.name}: {processed_count} processed, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Error processing log file {file_path}: {e}")
    
    async def _sync_detection_to_db(self, detection_data: Dict[str, Any]):
        """同步单条检测记录到数据库"""
        db: Session = get_db_session()
        
        try:
            # 检查记录是否已存在
            existing = db.query(DetectionResult).filter_by(
                request_id=detection_data.get('request_id')
            ).first()
            
            if existing:
                # 记录已存在，跳过
                return
            
            # 解析时间
            created_at = None
            if detection_data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(detection_data['created_at'].replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.now()
            
            # 创建检测结果记录
            user_id = detection_data.get('user_id')
            # 如果user_id不是UUID格式，尝试转换为UUID
            if user_id is not None:
                import uuid
                try:
                    # 如果是字符串数字，则转换为UUID
                    if isinstance(user_id, str) and user_id.isdigit():
                        # 简单的数字ID不能直接转换为UUID，需要查找对应的实际UUID
                        # 这里先设置为None，避免错误
                        user_id = None
                    elif isinstance(user_id, str):
                        # 尝试解析为UUID
                        user_id = uuid.UUID(user_id)
                    elif isinstance(user_id, int):
                        # 数字ID不能直接转换为UUID
                        user_id = None
                except (ValueError, TypeError):
                    user_id = None
            
            detection_result = DetectionResult(
                    request_id=detection_data.get('request_id'),
                    user_id=user_id,
                    content=detection_data.get('content'),
                    suggest_action=detection_data.get('suggest_action'),
                    suggest_answer=detection_data.get('suggest_answer'),
                    hit_keywords=detection_data.get('hit_keywords'),
                    model_response=detection_data.get('model_response'),
                    ip_address=detection_data.get('ip_address'),
                    user_agent=detection_data.get('user_agent'),
                    security_risk_level=detection_data.get('security_risk_level', '无风险'),
                    security_categories=detection_data.get('security_categories', []),
                    compliance_risk_level=detection_data.get('compliance_risk_level', '无风险'),
                    compliance_categories=detection_data.get('compliance_categories', []),
                    created_at=created_at or datetime.now()
                )
            
            db.add(detection_result)
            db.commit()
            
        except IntegrityError as e:
            # 重复记录，回滚并跳过
            db.rollback()
            logger.debug(f"Duplicate record skipped: {detection_data.get('request_id')}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing detection to DB: {e}")
            raise
        finally:
            db.close()
    
    async def force_sync(self, date_range: Optional[tuple] = None):
        """强制同步指定日期范围的数据"""
        logger.info("Starting force sync...")
        
        try:
            # 清空已处理文件记录，强制重新处理
            if date_range:
                # 只清空指定日期范围的记录
                for file_key in list(self._processed_files):
                    if any(date in file_key for date in [date_range[0], date_range[1]]):
                        self._processed_files.discard(file_key)
            else:
                # 清空所有记录
                self._processed_files.clear()
            
            # 获取文件并处理
            if date_range:
                log_files = async_detection_logger.get_log_files(date_range)
            else:
                log_files = async_detection_logger.get_log_files()
            
            for log_file in log_files:
                await self._process_log_file(log_file)
                
            logger.info("Force sync completed")
            
        except Exception as e:
            logger.error(f"Error in force sync: {e}")
            raise

# 全局实例
data_sync_service = DataSyncService()