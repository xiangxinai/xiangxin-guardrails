import uuid
import json
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models import DetectionResult, ResponseTemplate
from services.model_service import model_service
from services.keyword_service import KeywordService
from services.keyword_cache import keyword_cache
from services.template_cache import template_cache
from services.async_logger import async_detection_logger
from services.risk_config_service import RiskConfigService
from models.requests import GuardrailRequest, Message
from models.responses import GuardrailResponse, GuardrailResult, ComplianceResult, SecurityResult
from utils.logger import setup_logger

logger = setup_logger()

# 风险等级映射
RISK_LEVEL_MAPPING = {
    'S2': '高风险',   # 敏感政治话题
    'S3': '高风险',   # 损害国家形象  
    'S5': '高风险',   # 暴力犯罪
    'S9': '高风险',   # 提示词攻击
    'S1': '中风险', # 一般政治话题
    'S4': '中风险', # 伤害未成年人
    'S6': '中风险', # 违法犯罪
    'S7': '中风险', # 色情
    'S8': '低风险',    # 歧视内容
    'S10': '低风险',   # 辱骂
    'S11': '低风险',   # 侵犯个人隐私
    'S12': '低风险',   # 商业违法违规
}

# 类别名称映射
CATEGORY_NAMES = {
    'S1': '一般政治话题',
    'S2': '敏感政治话题',
    'S3': '损害国家形象',
    'S4': '伤害未成年人',
    'S5': '暴力犯罪',
    'S6': '违法犯罪',
    'S7': '色情',
    'S8': '歧视内容',
    'S9': '提示词攻击',
    'S10': '辱骂',
    'S11': '侵犯个人隐私',
    'S12': '商业违法违规',
}

class GuardrailService:
    """护栏检测服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.keyword_service = KeywordService(db)
        self.risk_config_service = RiskConfigService(db)
    
    async def check_guardrails(
        self, 
        request: GuardrailRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[str] = None  # 改为字符串类型
    ) -> GuardrailResponse:
        """执行护栏检测"""
        
        # 生成请求ID
        request_id = f"guardrails-{uuid.uuid4().hex}"
        
        # 提取用户内容
        user_content = self._extract_user_content(request.messages)
        try:
            # 1. 黑白名单预检（使用高性能内存缓存，按用户隔离）
            blacklist_hit, blacklist_name, blacklist_keywords = await keyword_cache.check_blacklist(user_content, user_id)
            if blacklist_hit:
                return await self._handle_blacklist_hit(
                    request_id, user_content, blacklist_name, blacklist_keywords,
                    ip_address, user_agent, user_id
                )
            
            whitelist_hit, whitelist_name, whitelist_keywords = await keyword_cache.check_whitelist(user_content, user_id)
            if whitelist_hit:
                return await self._handle_whitelist_hit(
                    request_id, user_content, whitelist_name, whitelist_keywords,
                    ip_address, user_agent, user_id
                )
            
            # 2. 模型检测
            # 将 Message 对象转换为字典格式
            messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            model_response = await model_service.check_messages(messages_dict)
            
            # 3. 解析模型响应并应用风险类型过滤
            compliance_result, security_result = self._parse_model_response(model_response, user_id)
            
            # 4. 确定建议动作和回答（传入 user_id 以按用户选择代答模板）
            overall_risk_level, suggest_action, suggest_answer = await self._determine_action(
                compliance_result, security_result, user_id
            )
            
            # 5. 异步记录检测结果到日志
            await self._log_detection_result(
                request_id, user_content, compliance_result, security_result,
                suggest_action, suggest_answer, model_response, 
                ip_address, user_agent, user_id
            )
            
            # 6. 构造响应
            result = GuardrailResult(
                compliance=compliance_result,
                security=security_result
            )
            
            return GuardrailResponse(
                id=request_id,
                result=result,
                overall_risk_level=overall_risk_level,
                suggest_action=suggest_action,
                suggest_answer=suggest_answer,
            )
            
        except Exception as e:
            logger.error(f"Guardrail check error: {e}")
            # 发生错误时返回安全的默认响应
            return await self._handle_error(request_id, user_content, str(e), user_id)
    
    def _extract_user_content(self, messages: List[Message]) -> str:
        """提取完整对话内容"""
        if len(messages) == 1 and messages[0].role == 'user':
            # 单条用户消息（提示词检测）
            return messages[0].content
        else:
            # 多条消息（对话检测），保存完整对话
            conversation_parts = []
            for msg in messages:
                role_label = "用户" if msg.role == "user" else "助手" if msg.role == "assistant" else msg.role
                conversation_parts.append(f"[{role_label}]: {msg.content}")
            return '\n'.join(conversation_parts)
    
    def _parse_model_response(self, response: str, user_id: Optional[str] = None) -> Tuple[ComplianceResult, SecurityResult]:
        """解析模型响应并应用风险类型过滤"""
        response = response.strip()
        
        if response == "无风险":
            return (
                ComplianceResult(risk_level="无风险", categories=[]),
                SecurityResult(risk_level="无风险", categories=[])
            )
        
        if response.startswith("unsafe\n"):
            category = response.split('\n')[1] if '\n' in response else ""
            
            # 检查用户是否禁用了此风险类型
            if user_id and not self.risk_config_service.is_risk_type_enabled(user_id, category):
                logger.info(f"Risk type {category} is disabled for user {user_id}, treating as safe")
                return (
                    ComplianceResult(risk_level="无风险", categories=[]),
                    SecurityResult(risk_level="无风险", categories=[])
                )
            
            risk_level = RISK_LEVEL_MAPPING.get(category, "中风险")
            category_name = CATEGORY_NAMES.get(category, category)
            
            if category == "S9":  # 提示词攻击
                return (
                    ComplianceResult(risk_level="无风险", categories=[]),
                    SecurityResult(risk_level=risk_level, categories=[category_name])
                )
            else:  # 内容合规问题
                return (
                    ComplianceResult(risk_level=risk_level, categories=[category_name]),
                    SecurityResult(risk_level="无风险", categories=[])
                )
        
        # 默认返回安全
        return (
            ComplianceResult(risk_level="无风险", categories=[]),
            SecurityResult(risk_level="无风险", categories=[])
        )
    
    async def _determine_action(
        self, 
        compliance_result: ComplianceResult,
        security_result: SecurityResult,
        user_id: Optional[str] = None
    ) -> Tuple[str, str, Optional[str]]:
        """确定建议动作和回答"""
        
        # 定义风险等级优先级（数值越高优先级越高）
        risk_priority = {
            "无风险": 0,
            "低风险": 1,
            "中风险": 2,
            "高风险": 3
        }
        
        # 获取最高风险等级
        compliance_priority = risk_priority.get(compliance_result.risk_level, 0)
        security_priority = risk_priority.get(security_result.risk_level, 0)
        
        # 取最高优先级对应的风险等级
        max_priority = max(compliance_priority, security_priority)
        overall_risk_level = next(level for level, priority in risk_priority.items() if priority == max_priority)
        
        # 收集所有风险类别
        risk_categories = []
        if compliance_result.risk_level != "无风险":
            risk_categories.extend(compliance_result.categories)
        if security_result.risk_level != "无风险":
            risk_categories.extend(security_result.categories)
        
        # 根据综合风险等级确定动作
        if overall_risk_level == "无风险":
            return overall_risk_level, "通过", None
        elif overall_risk_level == "高风险":
            suggest_answer = await self._get_suggest_answer(risk_categories, user_id)
            return overall_risk_level, "阻断", suggest_answer
        elif overall_risk_level == "中风险":
            suggest_answer = await self._get_suggest_answer(risk_categories, user_id)
            return overall_risk_level, "代答", suggest_answer
        else:  # 低风险
            suggest_answer = await self._get_suggest_answer(risk_categories, user_id)
            return overall_risk_level, "代答", suggest_answer
    
    async def _get_suggest_answer(self, categories: List[str], user_id: Optional[str] = None) -> str:
        """获取建议回答（使用高性能内存缓存，并按用户隔离）"""
        return await template_cache.get_suggest_answer(categories, user_id)
    
    async def _handle_blacklist_hit(
        self, request_id: str, content: str, list_name: str, 
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        user_id: Optional[str] = None
    ) -> GuardrailResponse:
        """处理黑名单命中"""
        
        # 异步记录到日志
        detection_data = {
            "request_id": request_id,
            "user_id": user_id,
            "content": content,
            "suggest_action": "阻断",
            "suggest_answer": f"很抱歉，我不能提供涉及{list_name}的内容。",
            "hit_keywords": json.dumps(keywords),
            "model_response": "blacklist_hit",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "security_risk_level": "无风险",
            "security_categories": [],
            "compliance_risk_level": "高风险",
            "compliance_categories": [list_name],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await async_detection_logger.log_detection(detection_data)
        
        return GuardrailResponse(
            id=request_id,
            result=GuardrailResult(
                compliance=ComplianceResult(risk_level="高风险", categories=[list_name]),
                security=SecurityResult(risk_level="无风险", categories=[])
            ),
            overall_risk_level="高风险",
            suggest_action="阻断",
            suggest_answer=f"很抱歉，我不能提供涉及{list_name}的内容。"
        )
    
    async def _handle_whitelist_hit(
        self, request_id: str, content: str, list_name: str,
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        user_id: Optional[str] = None
    ) -> GuardrailResponse:
        """处理白名单命中"""
        
        # 异步记录到日志
        detection_data = {
            "request_id": request_id,
            "user_id": user_id,
            "content": content,
            "suggest_action": "通过",
            "suggest_answer": None,
            "hit_keywords": json.dumps(keywords),
            "model_response": "whitelist_hit",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "security_risk_level": "无风险",
            "security_categories": [],
            "compliance_risk_level": "无风险",
            "compliance_categories": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await async_detection_logger.log_detection(detection_data)
        
        return GuardrailResponse(
            id=request_id,
            result=GuardrailResult(
                compliance=ComplianceResult(risk_level="无风险", categories=[]),
                security=SecurityResult(risk_level="无风险", categories=[])
            ),
            overall_risk_level="无风险",
            suggest_action="通过",
            suggest_answer=None
        )
    
    async def _log_detection_result(
        self, request_id: str, content: str, compliance_result: ComplianceResult,
        security_result: SecurityResult, suggest_action: str, suggest_answer: Optional[str],
        model_response: str, ip_address: Optional[str], user_agent: Optional[str],
        user_id: Optional[str] = None
    ):
        """异步记录检测结果到日志"""
        
        # 清理内容中的NUL字符
        from utils.validators import clean_null_characters
        
        detection_data = {
            "request_id": request_id,
            "user_id": user_id,
            "content": clean_null_characters(content) if content else content,
            "suggest_action": suggest_action,
            "suggest_answer": clean_null_characters(suggest_answer) if suggest_answer else suggest_answer,
            "model_response": clean_null_characters(model_response) if model_response else model_response,
            "ip_address": ip_address,
            "user_agent": clean_null_characters(user_agent) if user_agent else user_agent,
            "security_risk_level": security_result.risk_level,
            "security_categories": security_result.categories,
            "compliance_risk_level": compliance_result.risk_level,
            "compliance_categories": compliance_result.categories,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hit_keywords": None  # 只有黑白名单命中才有值
        }
        
        # 只写日志文件，不写数据库（由管理服务的日志处理器负责写数据库）
        await async_detection_logger.log_detection(detection_data)
    
    async def _handle_error(self, request_id: str, content: str, error: str, user_id: Optional[int] = None) -> GuardrailResponse:
        """处理错误情况"""
        
        # 异步记录错误检测结果
        detection_data = {
            "request_id": request_id,
            "user_id": user_id,
            "content": content,
            "suggest_action": "通过",
            "suggest_answer": None,
            "model_response": f"error: {error}",
            "security_risk_level": "无风险",
            "security_categories": [],
            "compliance_risk_level": "无风险",
            "compliance_categories": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hit_keywords": None,
            "ip_address": None,
            "user_agent": None
        }
        await async_detection_logger.log_detection(detection_data)
        
        return GuardrailResponse(
            id=request_id,
            result=GuardrailResult(
                compliance=ComplianceResult(risk_level="无风险", categories=[]),
                security=SecurityResult(risk_level="无风险", categories=[])
            ),
            overall_risk_level="无风险",  # 系统错误时按无风险通过处理
            suggest_action="通过",
            suggest_answer=None
        )