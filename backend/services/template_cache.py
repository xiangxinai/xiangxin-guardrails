import time
import asyncio
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from database.models import ResponseTemplate
from database.connection import get_db_session
from utils.logger import setup_logger

logger = setup_logger()

class TemplateCache:
    """响应模板缓存服务"""
    
    def __init__(self, cache_ttl: int = 600):  # 10分钟缓存，模板变化不频繁
        # 多租户模板缓存结构：{tenant_id: {category: {is_default: template_content}}}
        self._template_cache: Dict[str, Dict[str, Dict[bool, str]]] = {}
        self._cache_timestamp = 0
        self._cache_ttl = cache_ttl
        self._lock = asyncio.Lock()
        
    async def get_suggest_answer(self, categories: List[str], tenant_id: Optional[str] = None) -> str:
        """获取建议回答（内存缓存版）"""
        await self._ensure_cache_fresh()
        
        if not categories:
            return self._get_default_answer(tenant_id)
        
        try:
            # 定义风险等级优先级
            risk_priority = {
                "高风险": 3,
                "中风险": 2, 
                "低风险": 1,
                "无风险": 0
            }
            
            # 风险等级映射
            risk_level_mapping = {
                'S2': '高风险', 'S3': '高风险', 'S5': '高风险', 'S9': '高风险',
                'S1': '中风险', 'S4': '中风险', 'S6': '中风险', 'S7': '中风险',
                'S8': '低风险', 'S10': '低风险', 'S11': '低风险', 'S12': '低风险',
            }
            
            # 类别名称映射
            category_names = {
                'S1': '一般政治话题', 'S2': '敏感政治话题', 'S3': '损害国家形象',
                'S4': '伤害未成年人', 'S5': '暴力犯罪', 'S6': '违法犯罪',
                'S7': '色情', 'S8': '歧视内容', 'S9': '提示词攻击',
                'S10': '辱骂', 'S11': '侵犯个人隐私', 'S12': '商业违法违规',
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
                # 优先查找“当前用户”的模板（非默认优先），找不到再回退到全局默认
                user_cache = self._template_cache.get(str(tenant_id or "__none__"), {})
                if category_key in user_cache:
                    templates = user_cache[category_key]
                    if False in templates:  # 非默认模板
                        return templates[False]
                    if True in templates:  # 默认模板
                        return templates[True]

                # 回退到“全局默认用户”None的模板（用于系统级默认模板）
                global_cache = self._template_cache.get("__global__", {})
                if category_key in global_cache:
                    templates = global_cache[category_key]
                    if True in templates:
                        return templates[True]

            return self._get_default_answer(tenant_id)
            
        except Exception as e:
            logger.error(f"Get suggest answer error: {e}")
            return self._get_default_answer()
    
    def _get_default_answer(self, tenant_id: Optional[str]) -> str:
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
                # 加载所有启用的响应模板（按用户分组，None 代表全局默认模板）
                templates = db.query(ResponseTemplate).filter_by(is_active=True).all()
                new_cache: Dict[str, Dict[str, Dict[bool, str]]] = {}
                for template in templates:
                    user_key = str(template.tenant_id) if template.tenant_id is not None else "__global__"
                    category = template.category
                    is_default = template.is_default
                    content = template.template_content

                    if user_key not in new_cache:
                        new_cache[user_key] = {}
                    if category not in new_cache[user_key]:
                        new_cache[user_key][category] = {}
                    new_cache[user_key][category][is_default] = content
                
                # 原子性更新缓存
                self._template_cache = new_cache
                self._cache_timestamp = time.time()
                
                template_count = sum(
                    sum(len(templates) for templates in user_categories.values())
                    for user_categories in new_cache.values()
                )
                logger.debug(
                    f"Template cache refreshed - Users: {len(new_cache)}, Templates: {template_count}"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to refresh template cache: {e}")
    
    async def invalidate_cache(self):
        """立即失效缓存"""
        async with self._lock:
            self._cache_timestamp = 0
            logger.info("Template cache invalidated")
    
    def get_cache_info(self) -> dict:
        """获取缓存统计信息"""
        template_count = sum(
            sum(len(templates) for templates in user_categories.values())
            for user_categories in self._template_cache.values()
        )
        
        return {
            "users": len(self._template_cache),
            "templates": template_count,
            "last_refresh": self._cache_timestamp,
            "cache_age_seconds": time.time() - self._cache_timestamp if self._cache_timestamp > 0 else 0
        }

# 全局模板缓存实例
template_cache = TemplateCache(cache_ttl=600)  # 10分钟缓存