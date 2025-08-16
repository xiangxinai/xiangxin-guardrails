"""
象信AI安全护栏 - Python客户端SDK

使用示例:
    from guardrails_client import GuardrailsClient
    
    client = GuardrailsClient(
        api_base_url="http://your-guardrails-api.com",
        jwt_secret="your-jwt-secret-key"
    )
    
    # 检测内容
    result = client.check_content(
        user_id="550e8400-e29b-41d4-a716-446655440001",
        user_email="user@example.com",
        messages=[{"role": "user", "content": "要检测的内容"}]
    )
"""

import jwt
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging


class GuardrailsError(Exception):
    """护栏系统基础异常"""
    pass


class AuthenticationError(GuardrailsError):
    """认证错误"""
    pass


class ValidationError(GuardrailsError):
    """数据验证错误"""
    pass


class NotFoundError(GuardrailsError):
    """资源不存在错误"""
    pass


class RateLimitError(GuardrailsError):
    """请求频率限制错误"""
    pass


class GuardrailsClient:
    """象信AI安全护栏客户端"""
    
    def __init__(self, api_base_url: str, jwt_secret: str, 
                 timeout: int = 30, max_retries: int = 3):
        """
        初始化客户端
        
        Args:
            api_base_url: API基础URL
            jwt_secret: JWT密钥（与护栏系统相同）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.jwt_secret = jwt_secret
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 会话对象，支持连接池
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GuardrailsClient-Python/1.0.0'
        })
    
    def generate_user_token(self, user_id: str, user_email: str, 
                          expire_hours: int = 1) -> str:
        """
        为指定用户生成JWT token
        
        Args:
            user_id: 用户UUID字符串
            user_email: 用户邮箱
            expire_hours: token过期时间（小时）
            
        Returns:
            JWT token字符串
        """
        payload = {
            "user_id": str(user_id),
            "sub": str(user_id),
            "email": user_email,
            "role": "user",
            "exp": datetime.utcnow() + timedelta(hours=expire_hours)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def _make_request(self, method: str, endpoint: str, user_id: str, 
                     user_email: str, **kwargs) -> requests.Response:
        """
        发起API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            user_id: 用户ID
            user_email: 用户邮箱
            **kwargs: 其他requests参数
            
        Returns:
            requests.Response对象
            
        Raises:
            GuardrailsError: API请求相关错误
        """
        # 生成JWT token
        token = self.generate_user_token(user_id, user_email)
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        url = f"{self.api_base_url}{endpoint}"
        
        # 重试机制
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"请求 {method} {url} (尝试 {attempt + 1})")
                response = self.session.request(method, url, **kwargs)
                
                # 处理HTTP错误
                if response.status_code == 401:
                    raise AuthenticationError("认证失败，请检查JWT密钥和用户信息")
                elif response.status_code == 403:
                    raise AuthenticationError("权限不足")
                elif response.status_code == 404:
                    raise NotFoundError("请求的资源不存在")
                elif response.status_code == 422:
                    raise ValidationError(f"数据验证失败: {response.text}")
                elif response.status_code == 429:
                    raise RateLimitError("请求频率超限，请稍后重试")
                elif response.status_code >= 500:
                    if attempt < self.max_retries:
                        self.logger.warning(f"服务器错误 {response.status_code}，准备重试...")
                        continue
                    raise GuardrailsError(f"服务器内部错误: {response.status_code}")
                elif response.status_code >= 400:
                    raise GuardrailsError(f"请求失败 {response.status_code}: {response.text}")
                
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning(f"请求异常，准备重试: {e}")
                    continue
        
        # 所有重试都失败了
        raise GuardrailsError(f"请求失败，已重试{self.max_retries}次: {last_exception}")
    
    def _handle_response(self, response: requests.Response) -> Any:
        """
        处理API响应
        
        Args:
            response: requests.Response对象
            
        Returns:
            解析后的JSON数据
        """
        try:
            return response.json()
        except ValueError:
            raise GuardrailsError(f"响应不是有效的JSON格式: {response.text}")
    
    # ========== 内容检测接口 ==========
    
    def check_content(self, user_id: str, user_email: str,
                     messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        检测内容安全性
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            messages: 消息列表，每个消息包含role和content字段
            
        Returns:
            检测结果字典
            
        Example:
            result = client.check_content(
                user_id="user-uuid",
                user_email="user@example.com", 
                messages=[{
                    "role": "user",
                    "content": "要检测的内容"
                }]
            )
        """
        data = {"messages": messages}
        response = self._make_request("POST", "/v1/guardrails",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def get_available_models(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """获取可用模型列表"""
        response = self._make_request("GET", "/v1/guardrails/models",
                                    user_id, user_email)
        return self._handle_response(response)
    
    def health_check(self) -> Dict[str, Any]:
        """
        检测服务健康检查（不需要认证）
        
        Returns:
            健康状态信息
        """
        response = self.session.get(f"{self.api_base_url}/health", 
                                  timeout=self.timeout)
        return response.json()
    
    # ========== 黑名单管理接口 ==========
    
    def get_blacklists(self, user_id: str, user_email: str) -> List[Dict[str, Any]]:
        """
        获取用户黑名单列表
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            
        Returns:
            黑名单列表
        """
        response = self._make_request("GET", "/config/blacklist",
                                    user_id, user_email)
        return self._handle_response(response)
    
    def create_blacklist(self, user_id: str, user_email: str,
                        name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict[str, Any]:
        """
        创建黑名单
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            name: 黑名单名称
            keywords: 关键词列表
            description: 描述信息
            is_active: 是否启用
            
        Returns:
            创建结果
        """
        data = {
            "name": name,
            "keywords": keywords,
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("POST", "/config/blacklist",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def update_blacklist(self, user_id: str, user_email: str,
                        blacklist_id: int, name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict[str, Any]:
        """
        更新黑名单
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            blacklist_id: 黑名单ID
            name: 黑名单名称
            keywords: 关键词列表
            description: 描述信息
            is_active: 是否启用
            
        Returns:
            更新结果
        """
        data = {
            "name": name,
            "keywords": keywords,
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("PUT", f"/config/blacklist/{blacklist_id}",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def delete_blacklist(self, user_id: str, user_email: str,
                        blacklist_id: int) -> Dict[str, Any]:
        """
        删除黑名单
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            blacklist_id: 黑名单ID
            
        Returns:
            删除结果
        """
        response = self._make_request("DELETE", f"/config/blacklist/{blacklist_id}",
                                    user_id, user_email)
        return self._handle_response(response)
    
    # ========== 白名单管理接口 ==========
    
    def get_whitelists(self, user_id: str, user_email: str) -> List[Dict[str, Any]]:
        """获取用户白名单列表"""
        response = self._make_request("GET", "/config/whitelist",
                                    user_id, user_email)
        return self._handle_response(response)
    
    def create_whitelist(self, user_id: str, user_email: str,
                        name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict[str, Any]:
        """创建白名单"""
        data = {
            "name": name,
            "keywords": keywords,
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("POST", "/config/whitelist",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def update_whitelist(self, user_id: str, user_email: str,
                        whitelist_id: int, name: str, keywords: List[str],
                        description: str = "", is_active: bool = True) -> Dict[str, Any]:
        """更新白名单"""
        data = {
            "name": name,
            "keywords": keywords,
            "description": description,
            "is_active": is_active
        }
        response = self._make_request("PUT", f"/config/whitelist/{whitelist_id}",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def delete_whitelist(self, user_id: str, user_email: str,
                        whitelist_id: int) -> Dict[str, Any]:
        """删除白名单"""
        response = self._make_request("DELETE", f"/config/whitelist/{whitelist_id}",
                                    user_id, user_email)
        return self._handle_response(response)
    
    # ========== 代答模板管理接口 ==========
    
    def get_response_templates(self, user_id: str, user_email: str) -> List[Dict[str, Any]]:
        """获取用户代答模板列表"""
        response = self._make_request("GET", "/config/responses",
                                    user_id, user_email)
        return self._handle_response(response)
    
    def create_response_template(self, user_id: str, user_email: str,
                               category: str, risk_level: str,
                               template_content: str, is_default: bool = True,
                               is_active: bool = True) -> Dict[str, Any]:
        """
        创建代答模板
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            category: 风险类别代码 (S1-S12或default)
            risk_level: 风险等级 (无风险/低风险/中风险/高风险)
            template_content: 模板内容
            is_default: 是否为默认模板
            is_active: 是否启用
            
        Returns:
            创建结果
        """
        data = {
            "category": category,
            "risk_level": risk_level,
            "template_content": template_content,
            "is_default": is_default,
            "is_active": is_active
        }
        response = self._make_request("POST", "/config/responses",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def update_response_template(self, user_id: str, user_email: str,
                               template_id: int, category: str, risk_level: str,
                               template_content: str, is_default: bool = True,
                               is_active: bool = True) -> Dict[str, Any]:
        """更新代答模板"""
        data = {
            "category": category,
            "risk_level": risk_level,
            "template_content": template_content,
            "is_default": is_default,
            "is_active": is_active
        }
        response = self._make_request("PUT", f"/config/responses/{template_id}",
                                    user_id, user_email, json=data)
        return self._handle_response(response)
    
    def delete_response_template(self, user_id: str, user_email: str,
                               template_id: int) -> Dict[str, Any]:
        """删除代答模板"""
        response = self._make_request("DELETE", f"/config/responses/{template_id}",
                                    user_id, user_email)
        return self._handle_response(response)
    
    # ========== 系统信息接口 ==========
    
    def get_system_info(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """获取系统信息"""
        response = self._make_request("GET", "/config/system-info",
                                    user_id, user_email)
        return self._handle_response(response)
    
    def get_cache_info(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """获取缓存状态信息"""
        response = self._make_request("GET", "/config/cache-info",
                                    user_id, user_email)
        return self._handle_response(response)
    
    def refresh_cache(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """手动刷新缓存"""
        response = self._make_request("POST", "/config/cache/refresh",
                                    user_id, user_email)
        return self._handle_response(response)
    
    # ========== 批量操作辅助方法 ==========
    
    def batch_create_blacklists(self, user_id: str, user_email: str,
                               blacklists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量创建黑名单
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            blacklists: 黑名单定义列表
            
        Returns:
            创建结果列表
            
        Example:
            results = client.batch_create_blacklists(
                user_id="user-uuid",
                user_email="user@example.com",
                blacklists=[
                    {
                        "name": "敏感词1",
                        "keywords": ["词1", "词2"],
                        "description": "描述1"
                    },
                    {
                        "name": "敏感词2", 
                        "keywords": ["词3", "词4"],
                        "description": "描述2"
                    }
                ]
            )
        """
        results = []
        for blacklist_data in blacklists:
            try:
                result = self.create_blacklist(
                    user_id, user_email,
                    name=blacklist_data["name"],
                    keywords=blacklist_data["keywords"],
                    description=blacklist_data.get("description", ""),
                    is_active=blacklist_data.get("is_active", True)
                )
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "data": blacklist_data})
        
        return results
    
    def batch_check_content(self, user_id: str, user_email: str,
                           content_list: List[str]) -> List[Dict[str, Any]]:
        """
        批量检测内容
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱
            content_list: 要检测的内容列表
            
        Returns:
            检测结果列表
        """
        results = []
        for content in content_list:
            try:
                result = self.check_content(
                    user_id, user_email,
                    messages=[{"role": "user", "content": content}]
                )
                results.append({"success": True, "content": content, "result": result})
            except Exception as e:
                results.append({"success": False, "content": content, "error": str(e)})
        
        return results
    
    # ========== 上下文管理器支持 ==========
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，关闭会话"""
        self.session.close()
    
    def close(self):
        """关闭客户端连接"""
        self.session.close()


# ========== 辅助类和函数 ==========

class GuardrailsConfig:
    """护栏配置辅助类"""
    
    # 风险类别映射
    RISK_CATEGORIES = {
        'S1': {'name': '一般政治话题', 'level': '中风险'},
        'S2': {'name': '敏感政治话题', 'level': '高风险'},
        'S3': {'name': '损害国家形象', 'level': '高风险'},
        'S4': {'name': '伤害未成年人', 'level': '中风险'},
        'S5': {'name': '暴力犯罪', 'level': '高风险'},
        'S6': {'name': '违法犯罪', 'level': '中风险'},
        'S7': {'name': '色情', 'level': '中风险'},
        'S8': {'name': '歧视内容', 'level': '低风险'},
        'S9': {'name': '提示词攻击', 'level': '高风险'},
        'S10': {'name': '辱骂', 'level': '低风险'},
        'S11': {'name': '侵犯个人隐私', 'level': '低风险'},
        'S12': {'name': '商业违法违规', 'level': '低风险'},
        'default': {'name': '默认模板', 'level': '通用'}
    }
    
    @classmethod
    def get_category_name(cls, category_code: str) -> str:
        """根据类别代码获取类别名称"""
        return cls.RISK_CATEGORIES.get(category_code, {}).get('name', '未知类别')
    
    @classmethod
    def get_risk_level(cls, category_code: str) -> str:
        """根据类别代码获取风险等级"""
        return cls.RISK_CATEGORIES.get(category_code, {}).get('level', '未知')
    
    @classmethod
    def get_all_categories(cls) -> Dict[str, Dict[str, str]]:
        """获取所有风险类别"""
        return cls.RISK_CATEGORIES.copy()


def create_default_response_templates() -> List[Dict[str, Any]]:
    """
    创建默认代答模板列表
    
    Returns:
        默认模板配置列表
    """
    templates = []
    
    for code, info in GuardrailsConfig.RISK_CATEGORIES.items():
        if code == 'default':
            template_content = "很抱歉，我不能回答这个问题。如有疑问请联系客服。"
        elif info['level'] == '高风险':
            template_content = f"很抱歉，我不能提供涉及{info['name']}的内容。"
        elif info['level'] == '中风险':
            template_content = f"抱歉，我不能回答涉及{info['name']}的问题。"
        else:  # 低风险
            template_content = f"我理解您的问题，但不能提供涉及{info['name']}的具体回答。"
        
        templates.append({
            "category": code,
            "risk_level": info['level'],
            "template_content": template_content,
            "is_default": True,
            "is_active": True
        })
    
    return templates


# ========== 使用示例 ==========

if __name__ == "__main__":
    import logging
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 初始化客户端
    client = GuardrailsClient(
        api_base_url="http://localhost:5000",  # 替换为实际API地址
        jwt_secret="your-jwt-secret-key"       # 替换为实际JWT密钥
    )
    
    # 用户信息
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    user_email = "user@example.com"
    
    try:
        # 检查服务健康状态
        health = client.health_check()
        print(f"服务状态: {health}")
        
        # 创建黑名单
        blacklist_result = client.create_blacklist(
            user_id=user_id,
            user_email=user_email,
            name="测试黑名单",
            keywords=["敏感词1", "敏感词2"],
            description="Python SDK测试用黑名单"
        )
        print(f"创建黑名单: {blacklist_result}")
        
        # 获取黑名单列表
        blacklists = client.get_blacklists(user_id, user_email)
        print(f"黑名单列表: {blacklists}")
        
        # 创建默认代答模板
        templates = create_default_response_templates()
        for template in templates[:3]:  # 只创建前3个作为示例
            result = client.create_response_template(
                user_id=user_id,
                user_email=user_email,
                **template
            )
            print(f"创建模板: {result}")
        
        # 检测内容
        detection_result = client.check_content(
            user_id=user_id,
            user_email=user_email,
            messages=[{
                "role": "user",
                "content": "这是一个测试内容"
            }]
        )
        print(f"检测结果: {detection_result}")
        
        # 批量检测示例
        batch_results = client.batch_check_content(
            user_id=user_id,
            user_email=user_email,
            content_list=["内容1", "内容2", "内容3"]
        )
        print(f"批量检测结果: {batch_results}")
        
    except GuardrailsError as e:
        print(f"护栏系统错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
    
    finally:
        # 关闭客户端
        client.close()