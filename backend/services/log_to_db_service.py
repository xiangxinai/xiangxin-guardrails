import asyncio
import json
import uuid
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set
from sqlalchemy.orm import Session
from database.models import DetectionResult
from database.connection import get_admin_db_session
from utils.logger import setup_logger

logger = setup_logger()

class LogToDbService:
    """将检测日志文件导入数据库的服务"""
    
    def __init__(self):
        self.running = False
        self.task = None
        self.processed_files: Set[str] = set()
        self._state_file = None  # 将在启动时初始化
    
    async def start(self):
        """启动日志导入服务"""
        if self.running:
            return
        
        # 初始化状态文件路径
        from config import settings
        self._state_file = Path(settings.data_dir) / "log_to_db_service_state.pkl"
        
        # 加载已处理文件状态
        await self._load_processed_files_state()
            
        self.running = True
        self.task = asyncio.create_task(self._process_logs_loop())
        logger.info(f"Log to DB service started (loaded {len(self.processed_files)} processed files from state)")
    
    async def stop(self):
        """停止日志导入服务"""
        if not self.running:
            return
        
        # 保存已处理文件状态
        await self._save_processed_files_state()
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Log to DB service stopped")
    
    async def _process_logs_loop(self):
        """处理日志文件的循环"""
        while self.running:
            try:
                await self._process_log_files()
                await asyncio.sleep(5)  # 每5秒检查一次新日志（大幅提高同步频率）
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log processing error: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间
    
    async def _process_log_files(self):
        """处理所有未处理的日志文件"""
        from config import settings
        
        detection_log_dir = Path(settings.detection_log_dir)
        if not detection_log_dir.exists():
            return
        
        # 查找所有检测日志文件
        log_files = list(detection_log_dir.glob("detection_*.jsonl"))
        
        for log_file in log_files:
            if log_file.name not in self.processed_files:
                # 额外检查：如果该文件的所有记录都已存在于数据库中，则跳过
                if await self._is_file_already_in_db(log_file):
                    logger.info(f"File {log_file.name} already fully processed in database, skipping")
                    self.processed_files.add(log_file.name)
                    # 保存状态更新
                    await self._save_processed_files_state()
                    continue
                
                await self._process_single_log_file(log_file)
                self.processed_files.add(log_file.name)
                # 每处理完一个文件就保存状态
                await self._save_processed_files_state()
    
    async def _process_single_log_file(self, log_file: Path):
        """处理单个日志文件"""
        try:
            db = get_admin_db_session()
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_data = json.loads(line)
                            await self._save_log_to_db(db, log_data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON in {log_file}:{line_num}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing log entry {log_file}:{line_num}: {e}")
                
                # 提交所有更改
                db.commit()
                logger.info(f"Processed log file: {log_file.name}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing log file {log_file}: {e}")
    
    async def _save_log_to_db(self, db: Session, log_data: dict):
        """将日志数据保存到数据库"""
        try:
            # 检查是否已存在（避免重复导入）
            existing = db.query(DetectionResult).filter_by(
                request_id=log_data.get('request_id')
            ).first()
            
            if existing:
                return  # 已存在，跳过
            
            # 解析用户ID
            user_id = log_data.get('user_id')
            if user_id and isinstance(user_id, str):
                try:
                    user_id = uuid.UUID(user_id)
                except ValueError:
                    user_id = None
            
            # 解析创建时间
            created_at = None
            if log_data.get('created_at'):
                try:
                    # 处理多种时间格式
                    time_str = log_data['created_at']
                    if time_str.endswith('Z'):
                        time_str = time_str.replace('Z', '+00:00')
                    elif not time_str.endswith(('+00:00', '+08:00')) and 'T' in time_str:
                        # 如果没有时区信息，假设是中国本地时间（UTC+8）
                        time_str = time_str + '+08:00'
                    created_at = datetime.fromisoformat(time_str)
                except ValueError:
                    created_at = datetime.now(timezone.utc)
            else:
                created_at = datetime.now(timezone.utc)
            
            # 创建检测结果记录
            detection_result = DetectionResult(
                request_id=log_data.get('request_id'),
                user_id=user_id,
                content=log_data.get('content'),
                suggest_action=log_data.get('suggest_action'),
                suggest_answer=log_data.get('suggest_answer'),
                model_response=log_data.get('model_response'),
                ip_address=log_data.get('ip_address'),
                user_agent=log_data.get('user_agent'),
                security_risk_level=log_data.get('security_risk_level', '无风险'),
                security_categories=log_data.get('security_categories', []),
                compliance_risk_level=log_data.get('compliance_risk_level', '无风险'),
                compliance_categories=log_data.get('compliance_categories', []),
                created_at=created_at
            )
            
            db.add(detection_result)
            
        except Exception as e:
            logger.error(f"Error saving log data to DB: {e}")
            # 不抛出异常，继续处理下一条日志
    
    async def _load_processed_files_state(self):
        """从文件加载已处理文件状态"""
        try:
            if self._state_file and self._state_file.exists():
                with open(self._state_file, 'rb') as f:
                    self.processed_files = pickle.load(f)
                logger.info(f"Loaded {len(self.processed_files)} processed files from state file")
            else:
                logger.info("No state file found, starting with empty processed files set")
        except Exception as e:
            logger.error(f"Error loading processed files state: {e}")
            self.processed_files = set()
    
    async def _save_processed_files_state(self):
        """保存已处理文件状态到文件"""
        try:
            if self._state_file:
                # 确保目录存在
                self._state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._state_file, 'wb') as f:
                    pickle.dump(self.processed_files, f)
                logger.debug(f"Saved {len(self.processed_files)} processed files to state file")
        except Exception as e:
            logger.error(f"Error saving processed files state: {e}")
    
    async def _is_file_already_in_db(self, log_file: Path) -> bool:
        """检查日志文件的内容是否已完全存在于数据库中"""
        try:
            db = get_admin_db_session()
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    # 检查前10行是否都已存在于数据库中
                    lines_checked = 0
                    lines_found = 0
                    
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        lines_checked += 1
                        if lines_checked > 10:  # 只检查前10行以提高性能
                            break
                            
                        try:
                            log_data = json.loads(line)
                            request_id = log_data.get('request_id')
                            if request_id:
                                existing = db.query(DetectionResult).filter_by(
                                    request_id=request_id
                                ).first()
                                if existing:
                                    lines_found += 1
                        except json.JSONDecodeError:
                            continue
                    
                    # 如果检查的行数大于0且所有行都在数据库中，认为文件已处理
                    return lines_checked > 0 and lines_found == lines_checked
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error checking if file {log_file} is in DB: {e}")
            return False

# 全局实例
log_to_db_service = LogToDbService()