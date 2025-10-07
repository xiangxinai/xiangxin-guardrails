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
        # 模板缓存
        self._template_cache: Dict[str, Dict[str, Dict[bool, str]]] = {}
        # 知识库缓存: {tenant_id: {category: [knowledge_base_ids]}}
        self._knowledge_base_cache: Dict[str, Dict[str, List[int]]] = {}
        # 全局知识库缓存: {category: [knowledge_base_ids]}
        self._global_knowledge_base_cache: Dict[str, List[int]] = {}
        self._cache_timestamp = 0
        self._cache_ttl = cache_ttl
        self._lock = asyncio.Lock()

    async def get_suggest_answer(self, categories: List[str], tenant_id: Optional[str] = None, user_query: Optional[str] = None) -> str:
        """
        获取建议回答，优先从知识库搜索，找不到则使用默认模板
        Args:
            categories: 风险类别列表
            tenant_id: 用户ID
            user_query: 用户原始问题（用于知识库搜索）
        Returns:
            建议回答内容
        """
        await self._ensure_cache_fresh()

        if not categories:
            return self._get_default_answer(tenant_id)

        try:
            # 1. 尝试从知识库获取答案
            if user_query and user_query.strip():
                kb_answer = await self._search_knowledge_base_answer(categories, tenant_id, user_query.strip())
                if kb_answer:
                    logger.info(f"Found answer from knowledge base for user {tenant_id}, category: {categories}")
                    return kb_answer

            # 2. 知识库没有找到答案，使用传统模板逻辑
            return await self._get_template_answer(categories, tenant_id)

        except Exception as e:
            logger.error(f"Get suggest answer error: {e}")
            return self._get_default_answer(tenant_id)

    async def _search_knowledge_base_answer(self, categories: List[str], tenant_id: Optional[str], user_query: str) -> Optional[str]:
        """从知识库搜索答案"""
        if not tenant_id:
            return None

        try:
            # 定义风险等级优先级
            risk_priority = {
                "high_risk": 3,
                "medium_risk": 2,
                "low_risk": 1,
                "no_risk": 0
            }

            # 风险等级映射
            risk_level_mapping = {
                'S2': 'high_risk', 'S3': 'high_risk', 'S5': 'high_risk', 'S9': 'high_risk',
                'S1': 'medium_risk', 'S4': 'medium_risk', 'S6': 'medium_risk', 'S7': 'medium_risk',
                'S8': 'low_risk', 'S10': 'low_risk', 'S11': 'low_risk', 'S12': 'low_risk',
            }

            # 类别名称映射
            category_names = {
                'S1': 'General Political Topics', 'S2': 'Sensitive Political Topics', 'S3': 'Damage to National Image',
                'S4': 'Harm to Minors', 'S5': 'Violent Crime', 'S6': 'Illegal Activities',
                'S7': 'Pornography', 'S8': 'Discriminatory Content', 'S9': 'Prompt Injection',
                'S10': 'Insults', 'S11': 'Privacy Violation', 'S12': 'Business Violations',
            }

            # 将类别名称转换为类别代码，并计算风险等级
            category_risk_mapping = []
            for category in categories:
                category_key = None
                for key, name in category_names.items():
                    if name == category:
                        category_key = key
                        break

                if category_key:
                    risk_level = risk_level_mapping.get(category_key, "低风险")
                    priority = risk_priority.get(risk_level, 0)
                    category_risk_mapping.append((category_key, risk_level, priority))

            # 按风险等级排序，优先级高的在前
            category_risk_mapping.sort(key=lambda x: x[2], reverse=True)

            # 按最高风险等级搜索知识库
            user_cache = self._knowledge_base_cache.get(str(tenant_id), {})

            for category_key, risk_level, priority in category_risk_mapping:
                # 收集要搜索的知识库ID: 用户自己的 + 全局的
                knowledge_base_ids = user_cache.get(category_key, []).copy()
                global_kb_ids = self._global_knowledge_base_cache.get(category_key, [])
                knowledge_base_ids.extend(global_kb_ids)

                # 去重
                knowledge_base_ids = list(set(knowledge_base_ids))

                for kb_id in knowledge_base_ids:
                    try:
                        # 搜索相似问题
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
        """使用传统模板获取答案"""
        try:
            # 定义风险等级优先级
            risk_priority = {
                "high_risk": 3,
                "medium_risk": 2,
                "low_risk": 1,
                "no_risk": 0
            }

            # 风险等级映射
            risk_level_mapping = {
                'S2': 'high_risk', 'S3': 'high_risk', 'S5': 'high_risk', 'S9': 'high_risk',
                'S1': 'medium_risk', 'S4': 'medium_risk', 'S6': 'medium_risk', 'S7': 'medium_risk',
                'S8': 'low_risk', 'S10': 'low_risk', 'S11': 'low_risk', 'S12': 'low_risk',
            }

            # 类别名称映射
            category_names = {
                'S1': 'General Political Topics', 'S2': 'Sensitive Political Topics', 'S3': 'Damage to National Image',
                'S4': 'Harm to Minors', 'S5': 'Violent Crime', 'S6': 'Illegal Activities',
                'S7': 'Pornography', 'S8': 'Discriminatory Content', 'S9': 'Prompt Injection',
                'S10': 'Insults', 'S11': 'Privacy Violation', 'S12': 'Business Violations',
            }

            # 将类别名称转换为类别代码，并计算风险等级
            category_risk_mapping = []
            for category in categories:
                category_key = None
                for key, name in category_names.items():
                    if name == category:
                        category_key = key
                        break

                if category_key:
                    risk_level = risk_level_mapping.get(category_key, "低风险")
                    priority = risk_priority.get(risk_level, 0)
                    category_risk_mapping.append((category_key, risk_level, priority))

            # 按风险等级排序，优先级高的在前
            category_risk_mapping.sort(key=lambda x: x[2], reverse=True)

            # 按最高风险等级查找模板
            for category_key, risk_level, priority in category_risk_mapping:
                # 优先查找"当前用户"的模板（非默认优先），找不到再回退到全局默认
                user_cache = self._template_cache.get(str(tenant_id or "__none__"), {})
                if category_key in user_cache:
                    templates = user_cache[category_key]
                    if False in templates:  # 非默认模板
                        return templates[False]
                    if True in templates:  # 默认模板
                        return templates[True]

                # 回退到"全局默认用户"None的模板（用于系统级默认模板）
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
        """获取默认回答"""
        # 先找用户自定义的 default
        user_cache = self._template_cache.get(str(tenant_id or "__none__"), {})
        if "default" in user_cache and True in user_cache["default"]:
            return user_cache["default"][True]
        # 再回退到全局 default
        global_cache = self._template_cache.get("__global__", {})
        if "default" in global_cache and True in global_cache["default"]:
            return global_cache["default"][True]
        return "很抱歉，我不能回答这个问题。如有疑问请联系客服。"

    async def _ensure_cache_fresh(self):
        """确保缓存是最新的"""
        current_time = time.time()

        if current_time - self._cache_timestamp > self._cache_ttl:
            async with self._lock:
                # 双重检查锁定
                if current_time - self._cache_timestamp > self._cache_ttl:
                    await self._refresh_cache()

    async def _refresh_cache(self):
        """刷新缓存"""
        try:
            db = get_db_session()
            try:
                # 1. 加载所有启用的响应模板
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

                # 2. 加载所有启用的知识库
                knowledge_bases = db.query(KnowledgeBase).filter_by(is_active=True).all()
                new_kb_cache: Dict[str, Dict[str, List[int]]] = {}
                # 全局知识库缓存: {category: [knowledge_base_ids]}
                global_kb_cache: Dict[str, List[int]] = {}

                for kb in knowledge_bases:
                    user_key = str(kb.tenant_id)
                    category = kb.category

                    # 用户自己的知识库
                    if user_key not in new_kb_cache:
                        new_kb_cache[user_key] = {}
                    if category not in new_kb_cache[user_key]:
                        new_kb_cache[user_key][category] = []
                    new_kb_cache[user_key][category].append(kb.id)

                    # 全局知识库
                    if kb.is_global:
                        if category not in global_kb_cache:
                            global_kb_cache[category] = []
                        global_kb_cache[category].append(kb.id)

                # 保存全局知识库缓存
                self._global_knowledge_base_cache = global_kb_cache

                # 3. 原子性更新缓存
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
        """立即失效缓存"""
        async with self._lock:
            self._cache_timestamp = 0
            logger.info("Enhanced template cache invalidated")

    def get_cache_info(self) -> dict:
        """获取缓存统计信息"""
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

# 全局增强模板服务实例
enhanced_template_service = EnhancedTemplateService(cache_ttl=600)  # 10分钟缓存