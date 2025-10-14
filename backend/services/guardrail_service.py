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

# Risk level mapping
RISK_LEVEL_MAPPING = {
    'S2': 'high_risk',   # Sensitive Political Topics
    'S3': 'high_risk',   # Damage to National Image
    'S5': 'high_risk',   # Violent Crime
    'S9': 'high_risk',   # Prompt Injection
    'S1': 'medium_risk', # General Political Topics
    'S4': 'medium_risk', # Harm to Minors
    'S6': 'medium_risk', # Illegal Activities
    'S7': 'medium_risk', # Pornography
    'S8': 'low_risk',    # Discriminatory Content
    'S10': 'low_risk',   # Insults
    'S11': 'low_risk',   # Privacy Violation
    'S12': 'low_risk',   # Business Violations
}

# Category name mapping
CATEGORY_NAMES = {
    'S1': 'General Political Topics',
    'S2': 'Sensitive Political Topics',
    'S3': 'Damage to National Image',
    'S4': 'Harm to Minors',
    'S5': 'Violent Crime',
    'S6': 'Illegal Activities',
    'S7': 'Pornography',
    'S8': 'Discriminatory Content',
    'S9': 'Prompt Injection',
    'S10': 'Insults',
    'S11': 'Privacy Violation',
    'S12': 'Business Violations',
}

class GuardrailService:
    """Guardrail Detection Service"""

    def __init__(self, db: Session, application_id: Optional[str] = None):
        """
        Initialize GuardrailService

        Args:
            db: Database session
            application_id: Application ID for application-level configuration
        """
        self.db = db
        self.application_id = application_id
        self.keyword_service = KeywordService(db)
        self.risk_config_service = RiskConfigService(db)

    async def check_guardrails(
        self,
        request: GuardrailRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[str] = None,  # For ban policy and logging
        application_id: Optional[str] = None  # Application ID for application-level config
    ) -> GuardrailResponse:
        """Execute guardrail detection"""

        # Generate request ID
        request_id = f"guardrails-{uuid.uuid4().hex}"

        # Use application_id if provided, otherwise use instance application_id
        app_id = application_id or self.application_id

        # Extract user content
        user_content = self._extract_user_content(request.messages)
        try:
            # 1. Blacklist/whitelist pre-check (using high-performance memory cache, isolated by application)
            # Use application_id for keyword checking instead of tenant_id
            blacklist_hit, blacklist_name, blacklist_keywords = await keyword_cache.check_blacklist(user_content, app_id)
            if blacklist_hit:
                return await self._handle_blacklist_hit(
                    request_id, user_content, blacklist_name, blacklist_keywords,
                    ip_address, user_agent, tenant_id, app_id
                )

            whitelist_hit, whitelist_name, whitelist_keywords = await keyword_cache.check_whitelist(user_content, app_id)
            if whitelist_hit:
                return await self._handle_whitelist_hit(
                    request_id, user_content, whitelist_name, whitelist_keywords,
                    ip_address, user_agent, tenant_id, app_id
                )

            # 2. Model detection
            # Convert Message objects to dict format and process images
            from utils.image_utils import image_utils

            messages_dict = []
            has_image = False
            saved_image_paths = []

            for msg in request.messages:
                content = msg.content
                if isinstance(content, str):
                    messages_dict.append({"role": msg.role, "content": content})
                elif isinstance(content, list):
                    # Multimodal content
                    content_parts = []
                    for part in content:
                        if hasattr(part, 'type'):
                            if part.type == 'text' and hasattr(part, 'text'):
                                content_parts.append({"type": "text", "text": part.text})
                            elif part.type == 'image_url' and hasattr(part, 'image_url'):
                                has_image = True
                                original_url = part.image_url.url
                                # Process image: save and get path
                                processed_url, saved_path = image_utils.process_image_url(original_url, tenant_id)
                                if saved_path:
                                    saved_image_paths.append(saved_path)
                                content_parts.append({"type": "image_url", "image_url": {"url": processed_url}})
                    messages_dict.append({"role": msg.role, "content": content_parts})
                else:
                    messages_dict.append({"role": msg.role, "content": content})

            # Select model based on whether there are images
            use_vl_model = has_image
            model_response = await model_service.check_messages(messages_dict, use_vl_model=use_vl_model)

            # 3. Parse model response and apply risk type filtering
            compliance_result, security_result = self._parse_model_response(model_response, tenant_id)

            # 3.5. Data leak detection (detect input content)
            data_security_service = DataSecurityService(self.db)
            logger.info(f"Starting data leak detection for tenant {tenant_id}")
            data_detection_result = await data_security_service.detect_sensitive_data(
                text=user_content,
                tenant_id=tenant_id,
                direction='input'  # Detect input
            )
            logger.info(f"Data leak detection result: {data_detection_result}")

            # Construct data security result
            data_result = DataSecurityResult(
                risk_level=data_detection_result.get('risk_level', 'no_risk'),
                categories=data_detection_result.get('categories', [])
            )

            # 4. Determine suggested action and answer (pass tenant_id to select answer template by tenant, pass user query to support knowledge base search)
            overall_risk_level, suggest_action, suggest_answer = await self._determine_action(
                compliance_result, security_result, tenant_id, user_content, data_result
            )

            # 5. Asynchronously log detection results
            await self._log_detection_result(
                request_id, user_content, compliance_result, security_result,
                suggest_action, suggest_answer, model_response,
                ip_address, user_agent, tenant_id, app_id,
                has_image=has_image, image_count=len(saved_image_paths), image_paths=saved_image_paths
            )

            # 6. Construct response
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
            # Return safe default response on error
            return await self._handle_error(request_id, user_content, str(e), tenant_id)
    
    def _extract_user_content(self, messages: List[Message]) -> str:
        """Extract complete conversation content"""
        if len(messages) == 1 and messages[0].role == 'user':
            # Single user message (prompt detection)
            content = messages[0].content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # For multimodal content, only extract text part for log
                text_parts = []
                for part in content:
                    if hasattr(part, 'type') and part.type == 'text' and hasattr(part, 'text'):
                        text_parts.append(part.text)
                    elif hasattr(part, 'type') and part.type == 'image_url':
                        text_parts.append("[Image]")
                return ' '.join(text_parts) if text_parts else "[Multimodal content]"
            else:
                return str(content)
        else:
            # Multiple messages (conversation detection), save full conversation
            conversation_parts = []
            for msg in messages:
                role_label = "User" if msg.role == "user" else "Assistant" if msg.role == "assistant" else msg.role
                content = msg.content
                if isinstance(content, str):
                    conversation_parts.append(f"[{role_label}]: {content}")
                elif isinstance(content, list):
                    # For multimodal content, only extract text part
                    text_parts = []
                    for part in content:
                        if hasattr(part, 'type') and part.type == 'text' and hasattr(part, 'text'):
                            text_parts.append(part.text)
                        elif hasattr(part, 'type') and part.type == 'image_url':
                            text_parts.append("[Image]")
                    content_str = ' '.join(text_parts) if text_parts else "[Multimodal content]"
                    conversation_parts.append(f"[{role_label}]: {content_str}")
                else:
                    conversation_parts.append(f"[{role_label}]: {content}")
            return '\n'.join(conversation_parts)
    
    def _parse_model_response(self, response: str, tenant_id: Optional[str] = None) -> Tuple[ComplianceResult, SecurityResult]:
        """Parse model response and apply risk type filtering

        Note: Parameter name kept as tenant_id for backward compatibility
        """
        response = response.strip()

        if response == "safe":
            return (
                ComplianceResult(risk_level="no_risk", categories=[]),
                SecurityResult(risk_level="no_risk", categories=[])
            )

        if response.startswith("unsafe\n"):
            category = response.split('\n')[1] if '\n' in response else ""

            # Check if tenant has disabled this risk type
            if tenant_id and not self.risk_config_service.is_risk_type_enabled(tenant_id, category):
                logger.info(f"Risk type {category} is disabled for tenant {tenant_id}, treating as safe")
                return (
                    ComplianceResult(risk_level="no_risk", categories=[]),
                    SecurityResult(risk_level="no_risk", categories=[])
                )

            risk_level = RISK_LEVEL_MAPPING.get(category, "medium_risk")
            category_name = CATEGORY_NAMES.get(category, category)

            if category == "S9":  # Prompt Injection
                return (
                    ComplianceResult(risk_level="no_risk", categories=[]),
                    SecurityResult(risk_level=risk_level, categories=[category_name])
                )
            else:  # Compliance issues
                return (
                    ComplianceResult(risk_level=risk_level, categories=[category_name]),
                    SecurityResult(risk_level="no_risk", categories=[])
                )

        # Default return safe
        return (
            ComplianceResult(risk_level="no_risk", categories=[]),
            SecurityResult(risk_level="no_risk", categories=[])
        )
    
    async def _determine_action(
        self,
        compliance_result: ComplianceResult,
        security_result: SecurityResult,
        tenant_id: Optional[str] = None,  # tenant_id for backward compatibility
        user_query: Optional[str] = None,
        data_result: Optional[DataSecurityResult] = None
    ) -> Tuple[str, str, Optional[str]]:
        """Determine suggested action and answer"""

        # Define risk level priority (higher value = higher priority)
        risk_priority = {
            "no_risk": 0,
            "low_risk": 1,
            "medium_risk": 2,
            "high_risk": 3
        }

        # Get highest risk level (including data leak detection)
        compliance_priority = risk_priority.get(compliance_result.risk_level, 0)
        security_priority = risk_priority.get(security_result.risk_level, 0)
        data_priority = risk_priority.get(data_result.risk_level, 0) if data_result else 0

        # Get the risk level corresponding to the highest priority
        max_priority = max(compliance_priority, security_priority, data_priority)
        overall_risk_level = next(level for level, priority in risk_priority.items() if priority == max_priority)

        # Collect all risk categories
        risk_categories = []
        if compliance_result.risk_level != "no_risk":
            risk_categories.extend(compliance_result.categories)
        if security_result.risk_level != "no_risk":
            risk_categories.extend(security_result.categories)
        if data_result and data_result.risk_level != "no_risk":
            risk_categories.extend(data_result.categories)

        # Determine action based on overall risk level
        if overall_risk_level == "no_risk":
            return overall_risk_level, "pass", None
        elif overall_risk_level == "high_risk":
            suggest_answer = await self._get_suggest_answer(risk_categories, tenant_id, user_query)
            return overall_risk_level, "reject", suggest_answer
        elif overall_risk_level == "medium_risk":
            suggest_answer = await self._get_suggest_answer(risk_categories, tenant_id, user_query)
            return overall_risk_level, "replace", suggest_answer
        else:  # low_risk
            suggest_answer = await self._get_suggest_answer(risk_categories, tenant_id, user_query)
            return overall_risk_level, "replace", suggest_answer
    
    async def _get_suggest_answer(self, categories: List[str], tenant_id: Optional[str] = None, user_query: Optional[str] = None) -> str:
        """Get suggested answer (using enhanced template service, supports knowledge base search)

        Note: Parameter name kept as tenant_id for backward compatibility
        """
        return await enhanced_template_service.get_suggest_answer(categories, tenant_id, user_query)
    
    async def _handle_blacklist_hit(
        self, request_id: str, content: str, list_name: str,
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        tenant_id: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> GuardrailResponse:
        """Handle blacklist hit"""

        # Asynchronously log to database
        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "application_id": application_id,
            "content": content,
            "suggest_action": "reject",
            "suggest_answer": f"I'm sorry, I cannot provide content related to {list_name}.",
            "hit_keywords": json.dumps(keywords),
            "model_response": "blacklist_hit",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "security_risk_level": "no_risk",
            "security_categories": [],
            "compliance_risk_level": "high_risk",
            "compliance_categories": [list_name],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await async_detection_logger.log_detection(detection_data)

        return GuardrailResponse(
            id=request_id,
            result=GuardrailResult(
                compliance=ComplianceResult(risk_level="high_risk", categories=[list_name]),
                security=SecurityResult(risk_level="no_risk", categories=[])
            ),
            overall_risk_level="high_risk",
            suggest_action="reject",
            suggest_answer=f"Sorry, I can't provide content involving {list_name}."
        )
    
    async def _handle_whitelist_hit(
        self, request_id: str, content: str, list_name: str,
        keywords: List[str], ip_address: Optional[str], user_agent: Optional[str],
        tenant_id: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> GuardrailResponse:
        """Handle whitelist hit"""

        # Asynchronously record to log
        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "application_id": application_id,
            "content": content,
            "suggest_action": "pass",
            "suggest_answer": None,
            "hit_keywords": json.dumps(keywords),
            "model_response": "whitelist_hit",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "security_risk_level": "no_risk",
            "security_categories": [],
            "compliance_risk_level": "no_risk",
            "compliance_categories": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await async_detection_logger.log_detection(detection_data)
        
        return GuardrailResponse(
            id=request_id,
            result=GuardrailResult(
                compliance=ComplianceResult(risk_level="no_risk", categories=[]),
                security=SecurityResult(risk_level="no_risk", categories=[])
            ),
            overall_risk_level="no_risk",
            suggest_action="pass",
            suggest_answer=None
        )
    
    async def _log_detection_result(
        self, request_id: str, content: str, compliance_result: ComplianceResult,
        security_result: SecurityResult, suggest_action: str, suggest_answer: Optional[str],
        model_response: str, ip_address: Optional[str], user_agent: Optional[str],
        tenant_id: Optional[str] = None,
        application_id: Optional[str] = None,
        has_image: bool = False,
        image_count: int = 0, image_paths: List[str] = None
    ):
        """Asynchronously record detection results to log"""

        # Clean NUL characters in content
        from utils.validators import clean_null_characters

        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "application_id": application_id,
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
            "hit_keywords": None,  # Only hit keywords for blacklist/whitelist
            "has_image": has_image,
            "image_count": image_count,
            "image_paths": image_paths or []
        }

        # Only write log file, not write database (managed by admin service's log processor)
        await async_detection_logger.log_detection(detection_data)
    
    async def _handle_error(self, request_id: str, content: str, error: str, tenant_id: Optional[int] = None) -> GuardrailResponse:
        """Handle error situation"""
        
        # Asynchronously record error detection results
        detection_data = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "content": content,
            "suggest_action": "pass",
            "suggest_answer": None,
            "model_response": f"error: {error}",
            "security_risk_level": "no_risk",
            "security_categories": [],
            "compliance_risk_level": "no_risk",
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
                compliance=ComplianceResult(risk_level="no_risk", categories=[]),
                security=SecurityResult(risk_level="no_risk", categories=[])
            ),
            overall_risk_level="no_risk",  # When system error, treat as no risk
            suggest_action="pass",
            suggest_answer=None
        )