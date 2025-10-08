"""
增强的代答服务
结合传统代答模板和知识库问答对，提供更智能的代答功能
"""
import time
import asyncio
from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import Session
from database.models import ResponseTemplate, KnowledgeBase
from database.connection import get_db_session
from services.knowledge_base_service import knowledge_base_service
from utils.logger import setup_logger

logger = setup_logger()

class EnhancedTemplateService:
    """增强的代答模板服务，支持知识库搜索"""

    def __init__(self, cache_ttl: int = 600):
        # Template cache
        self._template_cache: Dict[str, Dict[str, Dict[bool, str]]] = {}
        # Knowledge base cache: {tenant_id: {category: [knowledge_base_ids]}}
        self._knowledge_base_cache: Dict[str, Dict[str, List[int]]] = {}
        # Global knowledge base cache: {category: [knowledge_base_ids]}
        self._global_knowledge_base_cache: Dict[str, List[int]] = {}
        self._cache_timestamp = 0
        self._cache_ttl = cache_ttl
        self._lock = asyncio.Lock()

    async def get_suggest_answer(self, categories: List[str], tenant_id: Optional[str] = None, user_query: Optional[str] = None) -> str:
        """
        Get suggested answer, first search from knowledge base, if not found, use default template
        Args:
            categories: Risk categories list
            tenant_id: User ID
            user_query: User original question (for knowledge base search)
        Returns:
            Suggested answer content
        """
        await self._ensure_cache_fresh()

        if not categories:
            return self._get_default_answer(tenant_id)

        try:
            # 1. Try to get answer from knowledge base
            if user_query and user_query.strip():
                kb_answer = await self._search_knowledge_base_answer(categories, tenant_id, user_query.strip())
                if kb_answer:
                    logger.info(f"Found answer from knowledge base for user {tenant_id}, category: {categories}")
                    return kb_answer

            # 2. Knowledge base didn't find answer, use traditional template logic
            return await self._get_template_answer(categories, tenant_id)

        except Exception as e:
            logger.error(f"Get suggest answer error: {e}")
            return self._get_default_answer(tenant_id)

    async def _search_knowledge_base_answer(self, categories: List[str], tenant_id: Optional[str], user_query: str) -> Optional[str]:
        """Search answer from knowledge base"""
        if not tenant_id:
            return None

        try:
            # Define risk level priority
            risk_priority = {
                "high_risk": 3,
                "medium_risk": 2,
                "low_risk": 1,
                "no_risk": 0
            }

            # Risk level mapping
            risk_level_mapping = {
                'S2': 'high_risk', 'S3': 'high_risk', 'S5': 'high_risk', 'S9': 'high_risk',
                'S1': 'medium_risk', 'S4': 'medium_risk', 'S6': 'medium_risk', 'S7': 'medium_risk',
                'S8': 'low_risk', 'S10': 'low_risk', 'S11': 'low_risk', 'S12': 'low_risk',
            }

            # Category name mapping
            category_names = {
                'S1': 'General Political Topics', 'S2': 'Sensitive Political Topics', 'S3': 'Damage to National Image',
                'S4': 'Harm to Minors', 'S5': 'Violent Crime', 'S6': 'Illegal Activities',
                'S7': 'Pornography', 'S8': 'Discriminatory Content', 'S9': 'Prompt Injection',
                'S10': 'Insults', 'S11': 'Privacy Violation', 'S12': 'Business Violations',
            }

            # Convert category name to category code, and calculate risk level
            category_risk_mapping = []
            for category in categories:
                category_key = None
                for key, name in category_names.items():
                    if name == category:
                        category_key = key
                        break

                if category_key:
                    risk_level = risk_level_mapping.get(category_key, "low_risk")
                    priority = risk_priority.get(risk_level, 0)
                    category_risk_mapping.append((category_key, risk_level, priority))

            # Sort by risk level, higher priority first
            category_risk_mapping.sort(key=lambda x: x[2], reverse=True)

            # Search knowledge base by highest risk level
            user_cache = self._knowledge_base_cache.get(str(tenant_id), {})

            for category_key, risk_level, priority in category_risk_mapping:
                # Collect knowledge base IDs to search: user's own + global
                knowledge_base_ids = user_cache.get(category_key, []).copy()
                global_kb_ids = self._global_knowledge_base_cache.get(category_key, [])
                knowledge_base_ids.extend(global_kb_ids)

                # Remove duplicates
                knowledge_base_ids = list(set(knowledge_base_ids))

                for kb_id in knowledge_base_ids:
                    try:
                        # Search similar questions
                        results = knowledge_base_service.search_similar_questions(user_query, kb_id, top_k=1)

                        if results:
                            best_result = results[0]
                            kb_type = "global" if kb_id in global_kb_ids else "user"
                            logger.info(f"Found similar question in {kb_type} KB {kb_id}: similarity={best_result['similarity_score']:.3f}")
                            return best_result['answer']

                    except Exception as e:
                        logger.warning(f"Error searching knowledge base {kb_id}: {e}")
                        continue

            return None

        except Exception as e:
            logger.error(f"Search knowledge base answer error: {e}")
            return None

    async def _get_template_answer(self, categories: List[str], tenant_id: Optional[str]) -> str:
        """Use traditional template to get answer"""
        try:
            # Define risk level priority
            risk_priority = {
                "high_risk": 3,
                "medium_risk": 2,
                "low_risk": 1,
                "no_risk": 0
            }

            # Risk level mapping
            risk_level_mapping = {
                'S2': 'high_risk', 'S3': 'high_risk', 'S5': 'high_risk', 'S9': 'high_risk',
                'S1': 'medium_risk', 'S4': 'medium_risk', 'S6': 'medium_risk', 'S7': 'medium_risk',
                'S8': 'low_risk', 'S10': 'low_risk', 'S11': 'low_risk', 'S12': 'low_risk',
            }

            # Category name mapping
            category_names = {
                'S1': 'General Political Topics', 'S2': 'Sensitive Political Topics', 'S3': 'Damage to National Image',
                'S4': 'Harm to Minors', 'S5': 'Violent Crime', 'S6': 'Illegal Activities',
                'S7': 'Pornography', 'S8': 'Discriminatory Content', 'S9': 'Prompt Injection',
                'S10': 'Insults', 'S11': 'Privacy Violation', 'S12': 'Business Violations',
            }

            # Convert category name to category code, and calculate risk level
            category_risk_mapping = []
            for category in categories:
                category_key = None
                for key, name in category_names.items():
                    if name == category:
                        category_key = key
                        break

                if category_key:
                    risk_level = risk_level_mapping.get(category_key, "low_risk")
                    priority = risk_priority.get(risk_level, 0)
                    category_risk_mapping.append((category_key, risk_level, priority))

            # Sort by risk level, higher priority first
            category_risk_mapping.sort(key=lambda x: x[2], reverse=True)

            # Find template by highest risk level
            for category_key, risk_level, priority in category_risk_mapping:
                # First find template for "current user" (non-default priority), if not found, fallback to global default
                user_cache = self._template_cache.get(str(tenant_id or "__none__"), {})
                if category_key in user_cache:
                    templates = user_cache[category_key]
                    if False in templates:  # Non-default template
                        return templates[False]
                    if True in templates:  # Default template
                        return templates[True]

                # Fallback to "global default user" None template (for system-level default template)
                global_cache = self._template_cache.get("__global__", {})
                if category_key in global_cache:
                    templates = global_cache[category_key]
                    if True in templates:
                        return templates[True]

            return self._get_default_answer(tenant_id)

        except Exception as e:
            logger.error(f"Get template answer error: {e}")
            return self._get_default_answer(tenant_id)

    def _get_default_answer(self, tenant_id: Optional[str] = None) -> str:
        """Get default answer"""
        # First find user-defined default
        user_cache = self._template_cache.get(str(tenant_id or "__none__"), {})
        if "default" in user_cache and True in user_cache["default"]:
            return user_cache["default"][True]
        # Then fallback to global default
        global_cache = self._template_cache.get("__global__", {})
        if "default" in global_cache and True in global_cache["default"]:
            return global_cache["default"][True]
        return "Sorry, I can't answer this question. If you have any questions, please contact customer service."

    async def _ensure_cache_fresh(self):
        """Ensure cache is fresh"""
        current_time = time.time()

        if current_time - self._cache_timestamp > self._cache_ttl:
            async with self._lock:
                # Double check lock
                if current_time - self._cache_timestamp > self._cache_ttl:
                    await self._refresh_cache()

    async def _refresh_cache(self):
        """Refresh cache"""
        try:
            db = get_db_session()
            try:
                # 1. Load all enabled response templates
                templates = db.query(ResponseTemplate).filter_by(is_active=True).all()
                new_template_cache: Dict[str, Dict[str, Dict[bool, str]]] = {}

                for template in templates:
                    user_key = str(template.tenant_id) if template.tenant_id is not None else "__global__"
                    category = template.category
                    is_default = template.is_default
                    content = template.template_content

                    if user_key not in new_template_cache:
                        new_template_cache[user_key] = {}
                    if category not in new_template_cache[user_key]:
                        new_template_cache[user_key][category] = {}
                    new_template_cache[user_key][category][is_default] = content

                # 2. Load all enabled knowledge bases
                knowledge_bases = db.query(KnowledgeBase).filter_by(is_active=True).all()
                new_kb_cache: Dict[str, Dict[str, List[int]]] = {}
                # Global knowledge base cache: {category: [knowledge_base_ids]}
                global_kb_cache: Dict[str, List[int]] = {}

                for kb in knowledge_bases:
                    user_key = str(kb.tenant_id)
                    category = kb.category

                    # User's own knowledge base
                    if user_key not in new_kb_cache:
                        new_kb_cache[user_key] = {}
                    if category not in new_kb_cache[user_key]:
                        new_kb_cache[user_key][category] = []
                    new_kb_cache[user_key][category].append(kb.id)

                    # Global knowledge base
                    if kb.is_global:
                        if category not in global_kb_cache:
                            global_kb_cache[category] = []
                        global_kb_cache[category].append(kb.id)

                # Save global knowledge base cache
                self._global_knowledge_base_cache = global_kb_cache

                # 3. Atomic update cache
                self._template_cache = new_template_cache
                self._knowledge_base_cache = new_kb_cache
                self._cache_timestamp = time.time()

                template_count = sum(
                    sum(len(templates) for templates in user_categories.values())
                    for user_categories in new_template_cache.values()
                )
                kb_count = sum(
                    sum(len(kb_ids) for kb_ids in user_categories.values())
                    for user_categories in new_kb_cache.values()
                )

                logger.debug(
                    f"Enhanced template cache refreshed - Users: {len(new_template_cache)}, "
                    f"Templates: {template_count}, Knowledge Bases: {kb_count}"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to refresh enhanced template cache: {e}")

    async def invalidate_cache(self):
        """Immediately invalidate cache"""
        async with self._lock:
            self._cache_timestamp = 0
            logger.info("Enhanced template cache invalidated")

    def get_cache_info(self) -> dict:
        """Get cache statistics"""
        template_count = sum(
            sum(len(templates) for templates in user_categories.values())
            for user_categories in self._template_cache.values()
        )

        kb_count = sum(
            sum(len(kb_ids) for kb_ids in user_categories.values())
            for user_categories in self._knowledge_base_cache.values()
        )

        global_kb_count = sum(len(kb_ids) for kb_ids in self._global_knowledge_base_cache.values())

        return {
            "users": len(self._template_cache),
            "templates": template_count,
            "knowledge_bases": kb_count,
            "global_knowledge_bases": global_kb_count,
            "last_refresh": self._cache_timestamp,
            "cache_age_seconds": time.time() - self._cache_timestamp if self._cache_timestamp > 0 else 0
        }

# Global enhanced template service instance
enhanced_template_service = EnhancedTemplateService(cache_ttl=600)  # 10 minutes cache