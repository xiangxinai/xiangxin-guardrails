from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from typing import Optional
import uuid
import os
from pathlib import Path
from config import settings
from utils.logger import setup_logger
from utils.url_signature import (
    verify_media_url_signature,
    generate_signed_media_url
)

logger = setup_logger()
router = APIRouter(tags=["Media"])

# 导入认证依赖（用于上传、删除、列表等需要认证的接口）
# 注意：这里不能直接从main导入，因为会产生循环依赖
# 我们在每个需要认证的路由上单独添加认证逻辑

# 允许的图片文件类型
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif",
    "image/bmp", "image/webp", "image/tiff"
}

# 最大文件大小：10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/media/upload/image")
async def upload_image(
    request: Request,
    file: UploadFile = File(...)
):
    """
    上传图片文件

    用户上传的图片将存储在 /mnt/data/xiangxin-guardrails-data/media/{user_id}/ 目录下
    返回图片的相对路径，可用于后续的检测请求
    """
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")

        # 验证文件类型
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}. 支持的类型: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        # 读取文件内容
        file_content = await file.read()

        # 验证文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制: {len(file_content)} bytes > {MAX_FILE_SIZE} bytes (10MB)"
            )

        # 验证文件不为空
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="文件内容为空")

        # 创建用户媒体目录
        user_media_dir = Path(settings.media_dir) / user_id
        user_media_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一的文件名
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = user_media_dir / unique_filename

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"Image uploaded successfully: {file_path}")

        # 生成带签名的访问URL
        signed_url = generate_signed_media_url(
            user_id=user_id,
            filename=unique_filename,
            expires_in_seconds=86400  # 24小时有效期
        )

        # 返回文件路径（相对路径和绝对路径）
        return {
            "success": True,
            "file_path": str(file_path),
            "relative_path": f"{user_id}/{unique_filename}",
            "filename": unique_filename,
            "size": len(file_content),
            "content_type": file.content_type,
            "url": signed_url  # 带签名的访问URL
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.delete("/media/image/{filename}")
async def delete_image(
    request: Request,
    filename: str
):
    """
    删除用户上传的图片
    """
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")

        # 构建文件路径
        file_path = Path(settings.media_dir) / user_id / filename

        # 安全检查：确保文件在用户目录下
        if not str(file_path).startswith(str(Path(settings.media_dir) / user_id)):
            raise HTTPException(status_code=403, detail="无权访问此文件")

        # 删除文件
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Image deleted successfully: {file_path}")
            return {"success": True, "message": "文件已删除"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image delete error: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.get("/media/images")
async def list_images(request: Request):
    """
    列出用户上传的所有图片
    """
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")

        # 用户媒体目录
        user_media_dir = Path(settings.media_dir) / user_id

        # 如果目录不存在，返回空列表
        if not user_media_dir.exists():
            return {"images": []}

        # 列出所有图片文件
        images = []
        for file_path in user_media_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                # 生成带签名的访问URL
                signed_url = generate_signed_media_url(
                    user_id=user_id,
                    filename=file_path.name,
                    expires_in_seconds=86400  # 24小时有效期
                )
                images.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "relative_path": f"{user_id}/{file_path.name}",
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "url": signed_url  # 带签名的访问URL
                })

        return {"images": images}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List images error: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")

@router.get("/media/image/{user_id}/{filename}")
async def get_image(
    user_id: str,
    filename: str,
    token: str = Query(..., description="签名token"),
    expires: int = Query(..., description="过期时间戳")
):
    """
    获取图片文件（需要签名验证）

    根据用户ID和文件名返回图片，需要提供有效的签名token和过期时间
    图片存储路径: /mnt/data/xiangxin-guardrails-data/media/{user_id}/{filename}

    Query参数:
        - token: 签名token
        - expires: 过期时间戳
    """
    try:
        # 验证签名
        if not verify_media_url_signature(user_id, filename, token, expires):
            raise HTTPException(
                status_code=403,
                detail="签名无效或已过期"
            )

        # 构建文件路径
        file_path = Path(settings.media_dir) / user_id / filename

        # 安全检查：确保文件在media目录下
        if not str(file_path).startswith(str(Path(settings.media_dir))):
            raise HTTPException(status_code=403, detail="无权访问此文件")

        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 根据文件扩展名动态设置media_type
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".tiff": "image/tiff"
        }
        file_extension = Path(filename).suffix.lower()
        media_type = media_type_map.get(file_extension, "image/jpeg")

        # 返回图片文件
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get image error: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")