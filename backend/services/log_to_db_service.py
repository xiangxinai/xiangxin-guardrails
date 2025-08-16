import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
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
        self.processed_files = set()
    
    async def start(self):
        """启动日志导入服务"""
        if self.running:
            return
            
        self.running = True
        self.task = asyncio.create_task(self._process_logs_loop())
        logger.info("Log to DB service started")
    
    async def stop(self):
        """停止日志导入服务"""
        if not self.running:
            return
            
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
                await self._process_single_log_file(log_file)
                self.processed_files.add(log_file.name)
    
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
                    created_at = datetime.fromisoformat(log_data['created_at'].replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()
            
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

# 全局实例
log_to_db_service = LogToDbService()