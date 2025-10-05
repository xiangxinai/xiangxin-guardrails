import uuid
import json
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models import DetectionResult, ResponseTemplate
from services.model_service import model_service
from services.keyword_service import KeywordService
from services.keyword_cache import keyword_cache
from services.enhanced_template_service import enhanced_template_service
from services.async_logger import async_detection_logger
from services.risk_config_service import RiskConfigService
from services.data_security_service import DataSecurityService
from models.requests import GuardrailRequest, Message
from models.responses import GuardrailResponse, GuardrailResult, ComplianceResult, SecurityResult, DataSecurityResult
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
        tenant_id: Optional[str] = None  # tenant_id，为向后兼容保持参数名为 tenant_id
    ) -> GuardrailResponse:
        """执行护栏检测"""
        
        # 生成请求ID
        request_id = f"guardrails-{uuid.uuid4().hex}"
        
        # 提取用户内容
        user_content = self._extract_user_content(request.messages)
        try:
            # 1. 黑白名单预检（使用高性能内存缓存，按租户隔离）
            blacklist_hit, blacklist_name, blacklist_keywords = await keyword_cache.check_blacklist(user_content, tenant_id)
            if blacklist_hit:
                return await self._handle_blacklist_hit(
                    request_id, user_content, blacklist_name, blacklist_keywords,
                    ip_address, user_agent, tenant_id
                )
            
            whitelist_hit, whitelist_name, whitelist_keywords = await keyword_cache.check_whitelist(user_content, tenant_id)
            if whitelist_hit:
                return await self._handle_whitelist_hit(
                    request_id, user_content, whitelist_name, whitelist_keywords,
                    ip_address, user_agent, tenant_id
                )
            
            # 2. 模型检测
            # 将 Message 对象转换为字典格式，同时处理图片
            from utils.image_utils import image_utils

            messages_dict = []
            has_image = False
            saved_image_paths = []

            for msg in request.messages:
                content = msg.content
                if isinstance(content, str):
                    messages_dict.append({"role": msg.role, "content": content})
                elif isinstance(content, list):
                    # 多模态内容
                    content_parts = []
                    for part in content:
                        if hasattr(part, 'type'):
                            if part.type == 'text' and hasattr(part, 'text'):
                                content_parts.append({"type": "text", "text": part.text})
                            elif part.type == 'image_url' and hasattr(part, 'image_url'):
                                has_image = True
                                original_url = part.image_url.url
                                # 处理图片：保存并获取路径
                                processed_url, saved_path = image_utils.process_image_url(original_url, tenant_id)
                                if saved_path:
                                    saved_image_paths.append(saved_path)
                                content_parts.append({"type": "image_url", "image_url": {"url": processed_url}})
                    messages_dict.append({"role": msg.role, "content": content_parts})
                else:
                    messages_dict.append({"role": msg.role, "content": content})

            # 根据是否有图片选择模型
            use_vl_model = has_image
            model_response = await model_service.check_messages(messages_dict, use_vl_model=use_vl_model)

            # 3. 解析模型响应并应用风险类型过滤
            compliance_result, security_result = self._parse_model_response(model_response, tenant_id)

            # 3.5. 数据防泄漏检测（检测输入内容）
            data_security_service = DataSecurityService(self.db)
            logger.info(f"Starting data leak detection for tenant {tenant_id}")
            data_detection_result = await data_security_service.detect_sensitive_data(
                text=user_content,
                tenant_id=tenant_id,  # 实际是 tenant_id
                direction='input'  # 检测输入
            )
            logger.info(f"Data leak detection result: {data_detection_result}")

            # 构造数据安全结果
            data_result = DataSecurityResult(
                risk_level=data_detection_result.get('risk_level', '无风险'),
                categories=data_detection_result.get('categories', [])
            )

            # 4. 确定建议动作和回答（传入 tenant_id（实际是tenant_id）以按租户选择代答模板，传入用户查询以支持知识库搜索）
            overall_risk_level, suggest_action, suggest_answer = await self._determine_action(
                compliance_result, security_result, tenant_id, user_content, data_result
            )
            
            # 5. 异步记录检测结果到日志
            await self._log_detection_result(
                request_id, user_content, compliance_result, security_result,
                suggest_action, suggest_answer, model_response,
                ip_address, user_agent, tenant_id,
                has_image=has_image, image_count=len(saved_image_paths), image_paths=saved_image_paths
            )
            
            # 6. 构造响应
            result = GuardrailResult(
                compliance=compliance_result,
                security=security_result,
                data=data_result
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
            return await self._handle_error(request_id, user_content, str(e), tenant_id)
    
    def _extract_user_content(self, messages: List[Message]) -> str:
        """提取完整对话内容"""
        if len(messages) == 1 and messages[0].role == 'user':
            # 单条用户消息（提示词检测）
            content = messages[0].content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # 对于多模态内容，只提取文本部分用于日志
                text_parts = []
                for part in content:
                    if hasattr(part, 'type') and part.type == 'text' and hasattr(part, 'text'):
                        text_parts.append(part.text)
                    elif hasattr(part, 'type') and part.type == 'image_url':
                        text_parts.append("[图片]")
                return ' '.join(text_parts) if text_parts else "[多模态内容]"
            else:
                return str(content)
        else:
            # 多条消息（对话检测），保存完整对话
            conversation_parts = []
            for msg in messages:
                role_label = "用户" if msg.role == "user" else "助手" if msg.role == "assistant" else msg.role
                content = msg.content
                if isinstance(content, str):
                    conversation_parts.append(f"[{role_label}]: {content}")
                elif isinstance(content, list):
                    # 对于多模态内容，只提取文本部分
                    text_parts = []
                    for part in content:
                        if hasattr(part, 'type') and part.type == 'text' and hasattr(part, 'text'):
                            text_parts.append(part.text)
                        elif hasattr(part, 'type') and part.type == 'image_url':
                            text_parts.append("[图片]")
                    content_str = ' '.join(text_parts) if text_parts else "[多模态内容]"
                    conversation_parts.append(f"[{role_label}]: {content_str}")
                else:
                    conversation_parts.append(f"[{role_label}]: {content}")
            return '\n'.join(conversation_parts)
    
    def _parse_model_response(self, response: str, tenant_id: Optional[str] = None) -> Tuple[ComplianceResult, SecurityResult]:
        """解析模型响应并应用风险类型过滤

        注意：参数名保持为 tenant_id 以向后兼容，但实际处理的是 tenant_id
        """
        response = response.strip()

        if response == "无风险":
            return (
                ComplianceResult(risk_level="无风险", categories=[]),
                SecurityResult(risk_level="无风险", categories=[])
            )

        if response.startswith("unsafe\n"):
            category = response.split('\n')[1] if '\n' in response else ""

            # 检查租户是否禁用了此风险类型
            if tenant_id and not self.risk_config_service.is_risk_type_enabled(tenant_id, category):
                logger.info(f"Risk type {category} is disabled for tenant {tenant_id}, treating as safe")
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
        tenant_id: Optional[str] = None,  # tenant_id，为向后兼容保持参数名为 tenant_id
        user_query: Optional[str] = None,
        data_result: Optional[DataSecurityResult] = None
    ) -> Tuple[str, str, Optional[str]]:
        """确定建议动作和回答"""

        # 定义风险等级优先级（数值越高优先级越高）
        risk_priority = {
            "无风险": 0,
            "低风险": 1,
            "中风险": 2,
            "高风险": 3
        }

        # 获取最高风险等级（包括数据防泄漏）
        compliance_priority = risk_priority.get(compliance_result.risk_level, 0)
        security_priority = risk_priority.get(security_result.risk_level, 0)
        data_priority = risk_priority.get(data_result.risk_level, 0) if data_result else 0

        # 取最高优先级对应的风险等级
        max_priority = max(compliance_priority, security_priority, data_priority)
        overall_risk_level = next(level for level, priority in risk_priority.items() if priority == max_priority)

        # 收集所有风险类别
        risk_categories = []
        if compliance_result.risk_level != "无风险":
            risk_categories.extend(compliance_result.categories)
        if security_result.risk_level != "无风险":
            risk_categories.extend(security_result.categories)
        if data_result and data_result.risk_level != "无风险":
            risk_categories.extend(data_result.categories)
        
        # 根据综合风险等级确定动作
        if overall_risk_level == "无风险":
            return overall_risk_level, "通过", None
        elif overall_risk_level == "高风险":
            suggest_answer = await self._get_suggest_answer(risk_categories, tenant_id, user_query)
            return overall_risk_level, "拒答", suggest_answer
        elif overall_risk_level == "中风险":
            suggest_answer = await self._get_suggest_answer(risk_categories, tenant_id, user_query)
            return overall_risk_level, "代答", suggest_answer
        else:  # 低风险
            suggest_answer = await self._get_suggest_answer(risk_categories, tenant_id, user_query)
            return overall_risk_level, "代答", suggest_answer
    
    async def _get_suggest_answer(self, categories: List[str], tenant_id: Optional[str] = None, user_query: Optional[str] = None) -> str:
        """获取建议回答（使用增强的模板服务，支持知识库搜索）

        注意：参数名保持为 tenant_id 以向后兼容，但实际处理的是 tenant_id
        """
        return await enhanced_template_service.get_suggest_answer(categories, tenant_id, user_query)
    
    async def _handle_blacklist_hit(
        self, request_id: str, content: str, list_name: str, 
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        tenant_id: Optional[str] = None
    ) -> GuardrailResponse:
        """处理黑名单命中"""
        
        # 异步记录到日志
        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
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
        tenant_id: Optional[str] = None
    ) -> GuardrailResponse:
        """处理白名单命中"""
        
        # 异步记录到日志
        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
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
        tenant_id: Optional[str] = None, has_image: bool = False,
        image_count: int = 0, image_paths: List[str] = None
    ):
        """异步记录检测结果到日志"""

        # 清理内容中的NUL字符
        from utils.validators import clean_null_characters

        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
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
            "hit_keywords": None,  # 只有黑白名单命中才有值
            "has_image": has_image,
            "image_count": image_count,
            "image_paths": image_paths or []
        }

        # 只写日志文件，不写数据库（由管理服务的日志处理器负责写数据库）
        await async_detection_logger.log_detection(detection_data)
    
    async def _handle_error(self, request_id: str, content: str, error: str, tenant_id: Optional[int] = None) -> GuardrailResponse:
        """处理错误情况"""
        
        # 异步记录错误检测结果
        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
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