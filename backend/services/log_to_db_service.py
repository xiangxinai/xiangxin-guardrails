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
    """Log to DB service - import detection log files to PostgreSQL database"""
    
    def __init__(self):
        self.running = False
        self.task = None
        self.processed_files: Set[str] = set()
        self._state_file = None  # Will be initialized when starting
    
    async def start(self):
        """Start log to DB service"""
        if self.running:
            return
        
        # Initialize state file path
        from config import settings
        self._state_file = Path(settings.data_dir) / "log_to_db_service_state.pkl"
        
        # Load processed files state
        await self._load_processed_files_state()
            
        self.running = True
        self.task = asyncio.create_task(self._process_logs_loop())
        logger.info(f"Log to DB service started (loaded {len(self.processed_files)} processed files from state)")
    
    async def stop(self):
        """Stop log to DB service"""
        if not self.running:
            return
        
        # Save processed files state
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
        """Process logs file loop"""
        while self.running:
            try:
                await self._process_log_files()
                await asyncio.sleep(5)  # Check new logs every 5 seconds (greatly improve sync frequency)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log processing error: {e}")
                await asyncio.sleep(60)  # Wait longer when error occurs
    
    async def _process_log_files(self):
        """Process all unprocessed log files"""
        from config import settings
        
        detection_log_dir = Path(settings.detection_log_dir)
        if not detection_log_dir.exists():
            return
        
        # Find all detection log files
        log_files = list(detection_log_dir.glob("detection_*.jsonl"))
        
        for log_file in log_files:
            if log_file.name not in self.processed_files:
                # Additional check: if all records in the file already exist in the database, skip
                if await self._is_file_already_in_db(log_file):
                    logger.info(f"File {log_file.name} already fully processed in database, skipping")
                    self.processed_files.add(log_file.name)
                    # Save state update
                    await self._save_processed_files_state()
                    continue
                
                await self._process_single_log_file(log_file)
                self.processed_files.add(log_file.name)
                # Save state after each file is processed
                await self._save_processed_files_state()
    
    async def _process_single_log_file(self, log_file: Path):
        """Process single log file"""
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
                            
                            # Clean NUL characters in data
                            from utils.validators import clean_detection_data
                            cleaned_data = clean_detection_data(log_data)
                            
                            await self._save_log_to_db(db, cleaned_data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON in {log_file}:{line_num}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing log entry {log_file}:{line_num}: {e}")
                
                # Commit all changes
                db.commit()
                logger.info(f"Processed log file: {log_file.name}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing log file {log_file}: {e}")
    
    async def _save_log_to_db(self, db: Session, log_data: dict):
        """Save log data to database"""
        try:
            # Check if already exists (avoid duplicate import)
            existing = db.query(DetectionResult).filter_by(
                request_id=log_data.get('request_id')
            ).first()
            
            if existing:
                return  # Already exists, skip
            
            # Parse tenant ID
            tenant_id = log_data.get('tenant_id')  # Field name kept as tenant_id for backward compatibility
            if tenant_id and isinstance(tenant_id, str):
                try:
                    tenant_id = uuid.UUID(tenant_id)
                except ValueError:
                    tenant_id = None
            
            # Parse created time
            created_at = None
            if log_data.get('created_at'):
                try:
                    # Process multiple time formats
                    time_str = log_data['created_at']
                    if time_str.endswith('Z'):
                        time_str = time_str.replace('Z', '+00:00')
                    elif not time_str.endswith(('+00:00', '+08:00')) and 'T' in time_str:
                        # If there is no timezone information, assume local time in China (UTC+8)
                        time_str = time_str + '+08:00'
                    created_at = datetime.fromisoformat(time_str)
                except ValueError:
                    created_at = datetime.now(timezone.utc)
            else:
                created_at = datetime.now(timezone.utc)
            
            # Create detection result record
            detection_result = DetectionResult(
                request_id=log_data.get('request_id'),
                tenant_id=tenant_id,
                content=log_data.get('content'),
                suggest_action=log_data.get('suggest_action'),
                suggest_answer=log_data.get('suggest_answer'),
                model_response=log_data.get('model_response'),
                ip_address=log_data.get('ip_address'),
                user_agent=log_data.get('user_agent'),
                security_risk_level=log_data.get('security_risk_level', 'no_risk'),
                security_categories=log_data.get('security_categories', []),
                compliance_risk_level=log_data.get('compliance_risk_level', 'no_risk'),
                compliance_categories=log_data.get('compliance_categories', []),
                created_at=created_at
            )
            
            db.add(detection_result)
            
        except Exception as e:
            logger.error(f"Error saving log data to DB: {e}")
            # Don't throw exception, continue processing next log
    
    async def _load_processed_files_state(self):
        """Load processed files state from file"""
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
        """Save processed files state to file"""
        try:
            if self._state_file:
                # Ensure directory exists
                self._state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._state_file, 'wb') as f:
                    pickle.dump(self.processed_files, f)
                logger.debug(f"Saved {len(self.processed_files)} processed files to state file")
        except Exception as e:
            logger.error(f"Error saving processed files state: {e}")
    
    async def _is_file_already_in_db(self, log_file: Path) -> bool:
        """Check if the content of the log file is already fully in the database"""
        try:
            db = get_admin_db_session()
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    # Check if the first 10 lines are already in the database
                    lines_checked = 0
                    lines_found = 0
                    
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        lines_checked += 1
                        if lines_checked > 10:  # Only check the first 10 lines to improve performance
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
                    
                    # If the number of checked lines is greater than 0 and all lines are in the database, consider the file processed
                    return lines_checked > 0 and lines_found == lines_checked
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error checking if file {log_file} is in DB: {e}")
            return False

# Global instance
log_to_db_service = LogToDbService()