import uuid
import json
from typing import List, Dict, Tuple, Optional, Union, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from services.model_service import model_service
from services.keyword_service import KeywordService
from services.keyword_cache import keyword_cache
from services.template_cache import template_cache
from services.async_logger import async_detection_logger
from services.risk_config_cache import risk_config_cache
from models.requests import GuardrailRequest, Message
from models.responses import GuardrailResponse, GuardrailResult, ComplianceResult, SecurityResult
from utils.logger import setup_logger
from utils.message_truncator import MessageTruncator

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

class DetectionGuardrailService:
    """检测服务专用护栏服务 - 只写日志，不写数据库"""
    
    def __init__(self):
        # 不需要数据库连接，只使用缓存
        pass
    
    async def detect_content(
        self,
        content: str,
        user_id: str,
        request_id: str,
        model_sensitivity_trigger_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        代理服务专用的简化检测方法
        将单个内容文本包装为GuardrailRequest并调用check_guardrails
        """
        from models.requests import GuardrailRequest, Message
        
        # 将文本内容包装为消息格式
        message = Message(role="user", content=content)
        request = GuardrailRequest(model="detection", messages=[message])

        # 调用完整的检测方法
        result = await self.check_guardrails(
            request=request,
            user_id=user_id,
            model_sensitivity_trigger_level=model_sensitivity_trigger_level
        )
        
        # 返回与代理API兼容的格式
        return {
            "request_id": result.id,
            "suggest_action": result.suggest_action,
            "suggest_answer": result.suggest_answer,
            "overall_risk_level": result.overall_risk_level,
            "compliance_result": result.result.compliance.__dict__ if result.result.compliance else None,
            "security_result": result.result.security.__dict__ if result.result.security else None
        }

    async def detect_messages(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        request_id: str,
        model_sensitivity_trigger_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上下文感知检测方法 - 支持问答对的messages结构
        直接使用messages列表进行检测，支持多轮对话上下文
        """
        from models.requests import GuardrailRequest, Message
        
        # 将字典格式的消息转换为Message对象
        message_objects = []
        for msg in messages:
            message_objects.append(Message(role=msg["role"], content=msg["content"]))
        
        request = GuardrailRequest(model="detection", messages=message_objects)

        # 调用完整的检测方法
        result = await self.check_guardrails(
            request=request,
            user_id=user_id,
            model_sensitivity_trigger_level=model_sensitivity_trigger_level
        )
        
        # 返回与代理API兼容的格式
        return {
            "request_id": result.id,
            "suggest_action": result.suggest_action,
            "suggest_answer": result.suggest_answer,
            "overall_risk_level": result.overall_risk_level,
            "compliance_result": result.result.compliance.__dict__ if result.result.compliance else None,
            "security_result": result.result.security.__dict__ if result.result.security else None
        }
    
    async def check_guardrails(
        self,
        request: GuardrailRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[str] = None,
        model_sensitivity_trigger_level: Optional[str] = None
    ) -> GuardrailResponse:
        """执行护栏检测（只写日志文件）"""
        
        # 生成请求ID
        request_id = f"guardrails-{uuid.uuid4().hex}"
        
        # 首先截断消息以符合最大上下文长度要求
        truncated_messages = MessageTruncator.truncate_messages(request.messages)
        
        # 如果截断后没有消息，返回错误
        if not truncated_messages:
            logger.warning(f"No valid messages after truncation for request {request_id}")
            return await self._handle_error(request_id, "", "No valid messages after truncation", user_id)
        
        # 提取用户内容（使用截断后的消息）
        user_content = self._extract_user_content(truncated_messages)
        
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
            
            # 2. 模型检测（使用截断后的消息，获取敏感度）
            messages_dict = [{"role": msg.role, "content": msg.content} for msg in truncated_messages]
            model_response, sensitivity_score = await model_service.check_messages_with_sensitivity(messages_dict)

            # 3. 解析模型响应并应用风险类型过滤和敏感度阈值
            compliance_result, security_result, sensitivity_level = await self._parse_model_response_with_sensitivity(
                model_response, sensitivity_score, user_id, model_sensitivity_trigger_level
            )
            
            # 4. 确定建议动作和回答
            overall_risk_level, suggest_action, suggest_answer = await self._determine_action(
                compliance_result, security_result, user_id, user_content
            )
            
            # 5. 异步记录检测结果到日志文件（不写数据库）
            await self._log_detection_result(
                request_id, user_content, compliance_result, security_result,
                suggest_action, suggest_answer, model_response,
                ip_address, user_agent, user_id, sensitivity_level, sensitivity_score
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
                prob=sensitivity_score,
            )
            
        except Exception as e:
            logger.error(f"Guardrail check error: {e}")
            # 发生错误时返回安全的默认响应
            return await self._handle_error(request_id, user_content, str(e), user_id)
    
    def _extract_user_content(self, messages: List[Message]) -> str:
        """提取完整对话内容"""
        if len(messages) == 1 and messages[0].role == 'user':
            return messages[0].content
        else:
            conversation_parts = []
            for msg in messages:
                role_label = "用户" if msg.role == "user" else "助手" if msg.role == "assistant" else msg.role
                conversation_parts.append(f"[{role_label}]: {msg.content}")
            return '\n'.join(conversation_parts)
    
    async def _parse_model_response(self, response: str, user_id: Optional[str] = None) -> Tuple[ComplianceResult, SecurityResult]:
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
            if user_id and not await risk_config_cache.is_risk_type_enabled(user_id, category):
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

    async def _parse_model_response_with_sensitivity(
        self, response: str, sensitivity_score: Optional[float], user_id: Optional[str] = None,
        model_sensitivity_trigger_level: Optional[str] = None
    ) -> Tuple[ComplianceResult, SecurityResult, Optional[str]]:
        """解析模型响应并应用风险类型过滤和敏感度阈值"""
        response = response.strip()

        if response == "无风险":
            sensitivity_level = await self._calculate_sensitivity_level(sensitivity_score, user_id) if sensitivity_score else None
            return (
                ComplianceResult(risk_level="无风险", categories=[]),
                SecurityResult(risk_level="无风险", categories=[]),
                sensitivity_level
            )

        if response.startswith("unsafe\n"):
            category = response.split('\n')[1] if '\n' in response else ""

            # 检查用户是否禁用了此风险类型
            if user_id and not await risk_config_cache.is_risk_type_enabled(user_id, category):
                logger.info(f"Risk type {category} is disabled for user {user_id}, treating as safe")
                sensitivity_level = await self._calculate_sensitivity_level(sensitivity_score, user_id) if sensitivity_score else None
                return (
                    ComplianceResult(risk_level="无风险", categories=[]),
                    SecurityResult(risk_level="无风险", categories=[]),
                    sensitivity_level
                )

            # 检查敏感度触发等级（优先使用模型特定配置）
            if sensitivity_score is not None and user_id:
                sensitivity_level = await self._calculate_sensitivity_level(sensitivity_score, user_id)
                trigger_level = model_sensitivity_trigger_level or await self._get_sensitivity_trigger_level(user_id)

                if not await self._should_trigger_detection(sensitivity_score, user_id):
                    logger.info(f"Sensitivity score {sensitivity_score} below current threshold for {category}, treating as safe")
                    return (
                        ComplianceResult(risk_level="无风险", categories=[]),
                        SecurityResult(risk_level="无风险", categories=[]),
                        sensitivity_level
                    )

            risk_level = RISK_LEVEL_MAPPING.get(category, "中风险")
            category_name = CATEGORY_NAMES.get(category, category)
            sensitivity_level = await self._calculate_sensitivity_level(sensitivity_score, user_id) if sensitivity_score else None

            if category == "S9":  # 提示词攻击
                return (
                    ComplianceResult(risk_level="无风险", categories=[]),
                    SecurityResult(risk_level=risk_level, categories=[category_name]),
                    sensitivity_level
                )
            else:  # 内容合规问题
                return (
                    ComplianceResult(risk_level=risk_level, categories=[category_name]),
                    SecurityResult(risk_level="无风险", categories=[]),
                    sensitivity_level
                )

        # 默认返回安全
        sensitivity_level = await self._calculate_sensitivity_level(sensitivity_score, user_id) if sensitivity_score else None
        return (
            ComplianceResult(risk_level="无风险", categories=[]),
            SecurityResult(risk_level="无风险", categories=[]),
            sensitivity_level
        )
    
    def _get_highest_risk_level(self, categories: List[str]) -> str:
        """获取最高风险等级"""
        if not categories:
            return "无风险"
        
        risk_levels = []
        for category in categories:
            for code, name in CATEGORY_NAMES.items():
                if name == category:
                    risk_levels.append(RISK_LEVEL_MAPPING[code])
                    break
        
        if "高风险" in risk_levels:
            return "高风险"
        elif "中风险" in risk_levels:
            return "中风险"
        elif "低风险" in risk_levels:
            return "低风险"
        else:
            return "无风险"
    
    async def _determine_action(self, compliance_result: ComplianceResult, security_result: SecurityResult, user_id: Optional[str] = None, user_query: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
        """确定建议动作"""
        overall_risk_level = "无风险"
        risk_categories = []
        
        if compliance_result.risk_level != "无风险":
            overall_risk_level = compliance_result.risk_level
            risk_categories.extend(compliance_result.categories)
        
        if security_result.risk_level != "无风险":
            if overall_risk_level == "无风险" or (overall_risk_level != "高风险" and security_result.risk_level == "高风险"):
                overall_risk_level = security_result.risk_level
            risk_categories.extend(security_result.categories)
        
        if overall_risk_level == "无风险":
            return overall_risk_level, "通过", None
        elif overall_risk_level == "高风险":
            suggest_answer = await self._get_suggest_answer(risk_categories, user_id, user_query)
            return overall_risk_level, "拒答", suggest_answer
        elif overall_risk_level == "中风险":
            suggest_answer = await self._get_suggest_answer(risk_categories, user_id, user_query)
            return overall_risk_level, "代答", suggest_answer
        else:  # 低风险
            suggest_answer = await self._get_suggest_answer(risk_categories, user_id, user_query)
            return overall_risk_level, "代答", suggest_answer
    
    async def _get_suggest_answer(self, categories: List[str], user_id: Optional[str] = None, user_query: Optional[str] = None) -> str:
        """获取建议回答（使用增强的模板服务，支持知识库搜索）"""
        from services.enhanced_template_service import enhanced_template_service
        return await enhanced_template_service.get_suggest_answer(categories, user_id, user_query)

    async def _calculate_sensitivity_level(self, sensitivity_score: float, user_id: Optional[str] = None) -> str:
        """根据敏感度分数和用户配置计算敏感度等级"""
        if not user_id:
            # 使用默认阈值
            if sensitivity_score >= 0.95:
                return "低"
            elif sensitivity_score >= 0.60:
                return "中"
            else:
                return "高"

        try:
            # 获取用户的敏感度阈值配置
            thresholds = await risk_config_cache.get_sensitivity_thresholds(user_id)

            if sensitivity_score >= thresholds.get("low", 0.95):
                return "低"
            elif sensitivity_score >= thresholds.get("medium", 0.60):
                return "中"
            else:
                return "高"
        except Exception as e:
            logger.warning(f"Failed to get sensitivity thresholds for user {user_id}: {e}")
            # 使用默认阈值
            if sensitivity_score >= 0.95:
                return "低"
            elif sensitivity_score >= 0.60:
                return "中"
            else:
                return "高"


    async def _get_sensitivity_trigger_level(self, user_id: str) -> str:
        """获取用户配置的敏感度触发等级"""
        try:
            from services.risk_config_cache import risk_config_cache
            trigger_level = await risk_config_cache.get_sensitivity_trigger_level(user_id)
            return trigger_level if trigger_level else "medium"  # 默认中敏感度触发
        except Exception as e:
            logger.warning(f"Failed to get sensitivity trigger level for user {user_id}: {e}")
            return "medium"  # 默认中敏感度触发

    async def _should_trigger_detection(self, sensitivity_score: float, user_id: str) -> bool:
        """判断是否应该触发检测基于敏感度分数和当前敏感度等级阈值"""
        try:
            # 获取用户当前敏感度等级
            current_level = await self._get_sensitivity_trigger_level(user_id)

            # 获取敏感度阈值配置
            thresholds = await risk_config_cache.get_sensitivity_thresholds(user_id)

            # 根据当前敏感度等级获取对应阈值
            if current_level == "low":
                threshold = thresholds.get("low", 0.95)
            elif current_level == "medium":
                threshold = thresholds.get("medium", 0.60)
            elif current_level == "high":
                threshold = thresholds.get("high", 0.40)
            else:
                threshold = 0.60  # 默认中敏感度

            # 检测分数 >= 当前敏感度阈值时触发
            return sensitivity_score >= threshold

        except Exception as e:
            logger.warning(f"Failed to check sensitivity trigger for user {user_id}: {e}")
            # 默认使用中敏感度阈值
            return sensitivity_score >= 0.60
    
    async def _handle_blacklist_hit(
        self, request_id: str, content: str, list_name: str, 
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        user_id: Optional[str] = None
    ) -> GuardrailResponse:
        """处理黑名单命中"""
        
        detection_data = {
            "request_id": request_id,
            "user_id": user_id,
            "content": content,
            "suggest_action": "拒答",
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
            suggest_action="拒答",
            suggest_answer=f"很抱歉，我不能提供涉及{list_name}的内容。"
        )
    
    async def _handle_whitelist_hit(
        self, request_id: str, content: str, list_name: str,
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        user_id: Optional[str] = None
    ) -> GuardrailResponse:
        """处理白名单命中"""
        
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
        user_id: Optional[str] = None, sensitivity_level: Optional[str] = None,
        sensitivity_score: Optional[float] = None
    ):
        """异步记录检测结果到日志文件（不写数据库）"""
        
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
            "sensitivity_level": sensitivity_level,
            "sensitivity_score": sensitivity_score,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hit_keywords": None
        }
        await async_detection_logger.log_detection(detection_data)
    
    async def _handle_error(self, request_id: str, content: str, error: str, user_id: Optional[str] = None) -> GuardrailResponse:
        """处理错误情况"""
        
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
            overall_risk_level="无风险",
            suggest_action="通过",
            suggest_answer=None
        )
# 创建全局实例
detection_guardrail_service = DetectionGuardrailService()
