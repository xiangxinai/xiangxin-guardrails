"""
数据安全服务 - 基于正则表达式的敏感数据检测和脱敏
"""
import re
import hashlib
import random
import string
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from database.models import DataSecurityEntityType
from utils.logger import setup_logger

logger = setup_logger()

# 风险等级映射
RISK_LEVEL_MAPPING = {
    'low': 'low_risk',
    'medium': 'medium_risk',
    'high': 'high_risk'
}

class DataSecurityService:
    """数据安全服务 - 敏感数据检测和脱敏"""

    def __init__(self, db: Session):
        self.db = db

    async def detect_sensitive_data(
        self,
        text: str,
        tenant_id: str,  # tenant_id，为向后兼容保持参数名为 tenant_id
        direction: str = "input"  # input 或 output
    ) -> Dict[str, Any]:
        """
        检测文本中的敏感数据

        Args:
            text: 待检测的文本
            tenant_id: 租户ID（实际是tenant_id，参数名为向后兼容）
            direction: 检测方向，input表示输入检测，output表示输出检测

        Returns:
            检测结果，包含风险等级、检测到的类别和脱敏后的文本
        """
        # 获取租户的敏感数据定义
        entity_types = self._get_user_entity_types(tenant_id, direction)

        if not entity_types:
            return {
                'risk_level': 'no_risk',
                'categories': [],
                'detected_entities': [],
                'anonymized_text': text
            }

        # 检测敏感数据
        detected_entities = []
        highest_risk_level = 'no_risk'
        detected_categories = set()

        for entity_type in entity_types:
            matches = self._match_pattern(text, entity_type)
            if matches:
                detected_entities.extend(matches)
                detected_categories.add(entity_type['entity_type'])

                # 更新最高风险等级
                entity_risk = entity_type.get('risk_level', 'medium')
                if self._compare_risk_level(entity_risk, highest_risk_level) > 0:
                    highest_risk_level = RISK_LEVEL_MAPPING.get(entity_risk, 'medium_risk')

        # 脱敏处理
        anonymized_text = self._anonymize_text(text, detected_entities, entity_types)

        return {
            'risk_level': highest_risk_level,
            'categories': list(detected_categories),
            'detected_entities': detected_entities,
            'anonymized_text': anonymized_text
        }

    def _get_user_entity_types(self, tenant_id: str, direction: str) -> List[Dict[str, Any]]:
        """获取租户的敏感数据类型配置

        注意：为保持向后兼容，函数名保持为 _get_user_entity_types，参数名保持为 tenant_id，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        try:
            # 获取全局配置和租户自定义配置
            query = self.db.query(DataSecurityEntityType).filter(
                and_(
                    DataSecurityEntityType.is_active == True,
                    (DataSecurityEntityType.tenant_id == tenant_id) | (DataSecurityEntityType.is_global == True)
                )
            )

            entity_types_orm = query.all()
            logger.info(f"Found {len(entity_types_orm)} entity types for tenant {tenant_id}")
            entity_types = []

            for et in entity_types_orm:
                # 检查是否启用了对应方向的检测
                recognition_config = et.recognition_config or {}
                if direction == "input" and not recognition_config.get('check_input', True):
                    continue
                if direction == "output" and not recognition_config.get('check_output', True):
                    continue

                entity_types.append({
                    'entity_type': et.entity_type,
                    'display_name': et.display_name,
                    'risk_level': et.category,  # 使用category字段存储风险等级
                    'pattern': recognition_config.get('pattern', ''),
                    'anonymization_method': et.anonymization_method,
                    'anonymization_config': et.anonymization_config or {}
                })

            return entity_types
        except Exception as e:
            logger.error(f"Error getting entity types: {e}")
            return []

    def _match_pattern(self, text: str, entity_type: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用正则表达式匹配敏感数据"""
        matches = []
        pattern = entity_type.get('pattern', '')

        if not pattern:
            return matches

        try:
            regex = re.compile(pattern)
            for match in regex.finditer(text):
                matches.append({
                    'entity_type': entity_type['entity_type'],
                    'display_name': entity_type['display_name'],
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(),
                    'risk_level': entity_type['risk_level'],
                    'anonymization_method': entity_type['anonymization_method'],
                    'anonymization_config': entity_type['anonymization_config']
                })
        except re.error as e:
            logger.error(f"Invalid regex pattern for {entity_type['entity_type']}: {e}")

        return matches

    def _anonymize_text(
        self,
        text: str,
        detected_entities: List[Dict[str, Any]],
        entity_types: List[Dict[str, Any]]
    ) -> str:
        """对文本进行脱敏处理"""
        if not detected_entities:
            return text

        # 按照位置倒序排列，从后往前替换，避免位置偏移
        sorted_entities = sorted(detected_entities, key=lambda x: x['start'], reverse=True)

        anonymized_text = text
        for entity in sorted_entities:
            method = entity.get('anonymization_method', 'replace')
            config = entity.get('anonymization_config', {})
            original_text = entity['text']

            # 根据脱敏方法处理
            if method == 'replace':
                # 替换为占位符
                replacement = config.get('replacement', f"<{entity['entity_type']}>")
            elif method == 'mask':
                # 掩码
                mask_char = config.get('mask_char', '*')
                keep_prefix = config.get('keep_prefix', 0)
                keep_suffix = config.get('keep_suffix', 0)
                replacement = self._mask_string(original_text, mask_char, keep_prefix, keep_suffix)
            elif method == 'hash':
                # 哈希
                replacement = self._hash_string(original_text)
            elif method == 'encrypt':
                # 加密（简化实现，实际应使用真实加密）
                replacement = f"<ENCRYPTED_{hashlib.md5(original_text.encode()).hexdigest()[:8]}>"
            elif method == 'shuffle':
                # 重排
                replacement = self._shuffle_string(original_text)
            elif method == 'random':
                # 随机替换
                replacement = self._random_replacement(original_text)
            else:
                # 默认替换
                replacement = f"<{entity['entity_type']}>"

            # 替换文本
            anonymized_text = anonymized_text[:entity['start']] + replacement + anonymized_text[entity['end']:]

        return anonymized_text

    def _mask_string(self, text: str, mask_char: str = '*', keep_prefix: int = 0, keep_suffix: int = 0) -> str:
        """掩码字符串"""
        if len(text) <= keep_prefix + keep_suffix:
            return text

        prefix = text[:keep_prefix] if keep_prefix > 0 else ''
        suffix = text[-keep_suffix:] if keep_suffix > 0 else ''
        middle_length = len(text) - keep_prefix - keep_suffix

        return prefix + mask_char * middle_length + suffix

    def _hash_string(self, text: str) -> str:
        """哈希字符串"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _shuffle_string(self, text: str) -> str:
        """重排字符串"""
        chars = list(text)
        random.shuffle(chars)
        return ''.join(chars)

    def _random_replacement(self, text: str) -> str:
        """随机替换"""
        # 保持长度，随机替换字符
        replacement = ''
        for char in text:
            if char.isdigit():
                replacement += random.choice(string.digits)
            elif char.isalpha():
                if char.isupper():
                    replacement += random.choice(string.ascii_uppercase)
                else:
                    replacement += random.choice(string.ascii_lowercase)
            else:
                replacement += char
        return replacement

    def _compare_risk_level(self, level1: str, level2: str) -> int:
        """比较风险等级，返回 1 如果 level1 > level2，-1 如果 level1 < level2，0 如果相等"""
        risk_order = {'no_risk': 0, 'low': 1, 'low_risk': 1, 'medium': 2, 'medium_risk': 2, 'high': 3, 'high_risk': 3}
        score1 = risk_order.get(level1, 0)
        score2 = risk_order.get(level2, 0)

        if score1 > score2:
            return 1
        elif score1 < score2:
            return -1
        else:
            return 0

    def create_entity_type(
        self,
        tenant_id: str,  # tenant_id，为向后兼容保持参数名为 tenant_id
        entity_type: str,
        display_name: str,
        risk_level: str,
        pattern: str,
        anonymization_method: str = 'replace',
        anonymization_config: Optional[Dict[str, Any]] = None,
        check_input: bool = True,
        check_output: bool = True,
        is_global: bool = False
    ) -> DataSecurityEntityType:
        """创建敏感数据类型配置

        注意：参数名保持为 tenant_id 以向后兼容，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        recognition_config = {
            'pattern': pattern,
            'check_input': check_input,
            'check_output': check_output
        }

        entity_type_obj = DataSecurityEntityType(
            tenant_id=tenant_id,  # 数据库字段名保持为 tenant_id，实际存储的是 tenant_id
            entity_type=entity_type,
            display_name=display_name,
            category=risk_level,  # 使用category字段存储风险等级
            recognition_method='regex',
            recognition_config=recognition_config,
            anonymization_method=anonymization_method,
            anonymization_config=anonymization_config or {},
            is_global=is_global
        )

        self.db.add(entity_type_obj)
        self.db.commit()
        self.db.refresh(entity_type_obj)

        return entity_type_obj

    def update_entity_type(
        self,
        entity_type_id: str,
        tenant_id: str,  # tenant_id，为向后兼容保持参数名为 tenant_id
        **kwargs
    ) -> Optional[DataSecurityEntityType]:
        """更新敏感数据类型配置

        注意：参数名保持为 tenant_id 以向后兼容，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        entity_type = self.db.query(DataSecurityEntityType).filter(
            and_(
                DataSecurityEntityType.id == entity_type_id,
                (DataSecurityEntityType.tenant_id == tenant_id) | (DataSecurityEntityType.is_global == True)
            )
        ).first()

        if not entity_type:
            return None

        # 更新字段
        if 'display_name' in kwargs:
            entity_type.display_name = kwargs['display_name']
        if 'risk_level' in kwargs:
            entity_type.category = kwargs['risk_level']
        if 'pattern' in kwargs:
            recognition_config = entity_type.recognition_config or {}
            recognition_config['pattern'] = kwargs['pattern']
            entity_type.recognition_config = recognition_config
        if 'check_input' in kwargs or 'check_output' in kwargs:
            recognition_config = entity_type.recognition_config or {}
            if 'check_input' in kwargs:
                recognition_config['check_input'] = kwargs['check_input']
            if 'check_output' in kwargs:
                recognition_config['check_output'] = kwargs['check_output']
            entity_type.recognition_config = recognition_config
        if 'anonymization_method' in kwargs:
            entity_type.anonymization_method = kwargs['anonymization_method']
        if 'anonymization_config' in kwargs:
            entity_type.anonymization_config = kwargs['anonymization_config']
        if 'is_active' in kwargs:
            entity_type.is_active = kwargs['is_active']

        entity_type.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity_type)

        return entity_type

    def delete_entity_type(self, entity_type_id: str, tenant_id: str) -> bool:
        """删除敏感数据类型配置

        注意：参数名保持为 tenant_id 以向后兼容，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        entity_type = self.db.query(DataSecurityEntityType).filter(
            and_(
                DataSecurityEntityType.id == entity_type_id,
                DataSecurityEntityType.tenant_id == tenant_id
            )
        ).first()

        if not entity_type:
            return False

        self.db.delete(entity_type)
        self.db.commit()

        return True

    def get_entity_types(
        self,
        tenant_id: str,  # tenant_id，为向后兼容保持参数名为 tenant_id
        risk_level: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[DataSecurityEntityType]:
        """获取敏感数据类型配置列表

        注意：参数名保持为 tenant_id 以向后兼容，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        query = self.db.query(DataSecurityEntityType).filter(
            (DataSecurityEntityType.tenant_id == tenant_id) | (DataSecurityEntityType.is_global == True)
        )

        if risk_level:
            query = query.filter(DataSecurityEntityType.category == risk_level)
        if is_active is not None:
            query = query.filter(DataSecurityEntityType.is_active == is_active)

        return query.order_by(DataSecurityEntityType.created_at.desc()).all()


def create_user_default_entity_types(db: Session, tenant_id: str) -> int:
    """为新租户创建默认实体类型配置

    注意：为保持向后兼容，函数名保持为 create_user_default_entity_types，参数名保持为 tenant_id，但实际处理的是 tenant_id
    """
    tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
    service = DataSecurityService(db)

    # 定义默认实体类型
    default_entity_types = [
        {
            'entity_type': 'ID_CARD_NUMBER',
            'display_name': '身份证号',
            'risk_level': 'high',
            'pattern': r'[1-8]\d{5}(19|20)\d{2}((0[1-9])|(1[0-2]))((0[1-9])|([12]\d)|(3[01]))\d{3}[\dxX]',
            'anonymization_method': 'mask',
            'anonymization_config': {'mask_char': '*', 'keep_prefix': 3, 'keep_suffix': 4},
            'check_input': True,
            'check_output': True
        },
        {
            'entity_type': 'PHONE_NUMBER',
            'display_name': '手机号',
            'risk_level': 'medium',
            'pattern': r'1[3-9]\d{9}',
            'anonymization_method': 'mask',
            'anonymization_config': {'mask_char': '*', 'keep_prefix': 3, 'keep_suffix': 4},
            'check_input': True,
            'check_output': True
        },
        {
            'entity_type': 'EMAIL',
            'display_name': '电子邮箱',
            'risk_level': 'low',
            'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'anonymization_method': 'mask',
            'anonymization_config': {'mask_char': '*', 'keep_prefix': 2, 'keep_suffix': 0},
            'check_input': True,
            'check_output': True
        },
        {
            'entity_type': 'BANK_CARD_NUMBER',
            'display_name': '银行卡号',
            'risk_level': 'high',
            'pattern': r'\d{16,19}',
            'anonymization_method': 'mask',
            'anonymization_config': {'mask_char': '*', 'keep_prefix': 4, 'keep_suffix': 4},
            'check_input': True,
            'check_output': True
        },
        {
            'entity_type': 'PASSPORT_NUMBER',
            'display_name': '护照号',
            'risk_level': 'high',
            'pattern': r'[EGP]\d{8}',
            'anonymization_method': 'mask',
            'anonymization_config': {'mask_char': '*', 'keep_prefix': 1, 'keep_suffix': 2},
            'check_input': True,
            'check_output': True
        },
        {
            'entity_type': 'IP_ADDRESS',
            'display_name': 'IP地址',
            'risk_level': 'low',
            'pattern': r'(?:\d{1,3}\.){3}\d{1,3}',
            'anonymization_method': 'replace',
            'anonymization_config': {'replacement': '<IP_ADDRESS>'},
            'check_input': True,
            'check_output': True
        }
    ]

    created_count = 0
    for entity_data in default_entity_types:
        try:
            # 检查是否已存在
            existing = db.query(DataSecurityEntityType).filter(
                and_(
                    DataSecurityEntityType.entity_type == entity_data['entity_type'],
                    DataSecurityEntityType.tenant_id == tenant_id
                )
            ).first()

            if not existing:
                service.create_entity_type(
                    tenant_id=tenant_id, 
                    entity_type=entity_data['entity_type'],
                    display_name=entity_data['display_name'],
                    risk_level=entity_data['risk_level'],
                    pattern=entity_data['pattern'],
                    anonymization_method=entity_data['anonymization_method'],
                    anonymization_config=entity_data['anonymization_config'],
                    check_input=entity_data['check_input'],
                    check_output=entity_data['check_output'],
                    is_global=True  # 系统默认的初始化数据标记为系统来源
                )
                created_count += 1
        except Exception as e:
            logger.error(f"创建默认实体类型 {entity_data['entity_type']} 失败: {e}")

    return created_count

