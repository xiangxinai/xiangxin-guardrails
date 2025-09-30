"""
图片处理工具类
仅支持base64编码格式，确保安全性
"""
import base64
import uuid
import re
from pathlib import Path
from typing import Tuple, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

class ImageUtils:
    """图片处理工具类 - 仅支持base64编码"""

    @staticmethod
    def is_base64_image(url: str) -> bool:
        """
        判断是否为base64编码的图片
        格式: data:image/jpeg;base64,{base64_string}
        """
        return url.startswith("data:image/") and ";base64," in url

    @staticmethod
    def extract_base64_data(url: str) -> Tuple[Optional[str], Optional[bytes]]:
        """
        从data URL中提取图片格式和base64数据

        Returns:
            (image_format, binary_data) - 例如 ('jpeg', b'...')
        """
        try:
            # 格式: data:image/jpeg;base64,/9j/4AAQSkZJRg...
            match = re.match(r'data:image/([^;]+);base64,(.+)', url)
            if not match:
                logger.error(f"Invalid base64 image format: {url[:50]}...")
                return None, None

            image_format = match.group(1)  # jpeg, png, etc.
            base64_data = match.group(2)

            # 解码base64
            image_bytes = base64.b64decode(base64_data)

            return image_format, image_bytes

        except Exception as e:
            logger.error(f"Failed to extract base64 data: {e}")
            return None, None

    @staticmethod
    def save_base64_image(url: str, user_id: str) -> Optional[str]:
        """
        保存base64编码的图片到用户目录

        Args:
            url: base64 data URL
            user_id: 用户UUID

        Returns:
            保存后的文件绝对路径，失败返回None
        """
        try:
            # 提取图片数据
            image_format, image_bytes = ImageUtils.extract_base64_data(url)
            if not image_bytes:
                return None

            # 创建用户媒体目录
            user_media_dir = Path(settings.media_dir) / user_id
            user_media_dir.mkdir(parents=True, exist_ok=True)

            # 生成唯一文件名
            file_extension = f".{image_format}" if image_format else ".jpg"
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = user_media_dir / unique_filename

            # 保存图片
            with open(file_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Saved base64 image to: {file_path}, size: {len(image_bytes)} bytes")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save base64 image: {e}")
            return None

    @staticmethod
    def process_image_url(url: str, user_id: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        处理图片URL - 仅支持base64编码格式

        Args:
            url: 图片URL（必须是base64格式）
            user_id: 用户UUID（保存base64图片时需要）

        Returns:
            (processed_url, saved_file_path)
            - processed_url: 原始base64 URL
            - saved_file_path: 保存后的文件路径

        Raises:
            ValueError: 如果不是base64格式
        """
        # 只支持Base64图片
        if ImageUtils.is_base64_image(url):
            saved_path = None
            if user_id:
                saved_path = ImageUtils.save_base64_image(url, user_id)
            return url, saved_path  # 返回原始base64 URL给模型使用
        else:
            raise ValueError(f"仅支持base64编码格式的图片，格式应为: data:image/[jpeg|png|...];base64,{{base64_string}}")

    @staticmethod
    def encode_file_to_base64(file_bytes: bytes, image_format: str = 'jpeg') -> str:
        """
        将文件字节编码为base64 data URL

        Args:
            file_bytes: 文件字节数据
            image_format: 图片格式 (jpeg, png, gif, etc.)

        Returns:
            data:image/jpeg;base64,{base64_string} 格式的URL
        """
        try:
            # 编码为base64
            base64_string = base64.b64encode(file_bytes).decode('utf-8')
            return f"data:image/{image_format};base64,{base64_string}"
        except Exception as e:
            logger.error(f"Failed to encode bytes to base64: {e}")
            raise

    @staticmethod
    def validate_image_size(base64_url: str, max_size_mb: int = 10) -> bool:
        """
        验证base64图片大小

        Args:
            base64_url: base64图片URL
            max_size_mb: 最大允许大小（MB）

        Returns:
            是否符合大小限制
        """
        try:
            _, image_bytes = ImageUtils.extract_base64_data(base64_url)
            if image_bytes:
                size_mb = len(image_bytes) / (1024 * 1024)
                return size_mb <= max_size_mb
            return False
        except Exception as e:
            logger.error(f"Failed to validate image size: {e}")
            return False

# 创建全局实例
image_utils = ImageUtils()