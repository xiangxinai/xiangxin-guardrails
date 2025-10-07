import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from config import settings

def generate_verification_code(length: int = 6) -> str:
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=length))

def get_email_template(language: str, verification_code: str) -> tuple[str, str]:
    """
    Get email template based on language
    Returns (subject, html_body) tuple
    """
    if language == 'zh':
        subject = "象信AI安全护栏平台 - 邮箱验证码"
        html_body = f"""
        <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                        <h1 style="color: #1890ff; margin: 0;">象信AI安全护栏平台</h1>
                    </div>
                    <div style="padding: 30px 20px;">
                        <h2 style="color: #333;">邮箱验证</h2>
                        <p style="color: #666; line-height: 1.6;">
                            您好！感谢您注册象信AI安全护栏平台。
                        </p>
                        <p style="color: #666; line-height: 1.6;">
                            您的验证码是：
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="background-color: #1890ff; color: white; padding: 15px 30px; font-size: 24px; font-weight: bold; border-radius: 5px; letter-spacing: 5px;">
                                {verification_code}
                            </span>
                        </div>
                        <p style="color: #666; line-height: 1.6;">
                            验证码有效期为10分钟，请及时使用。
                        </p>
                        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #999; font-size: 14px;">
                                象信AI安全护栏平台 - 保护AI应用安全
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
    else:  # Default to English
        subject = "Xiangxin AI Guardrails - Email Verification Code"
        html_body = f"""
        <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                        <h1 style="color: #1890ff; margin: 0;">Xiangxin AI Guardrails</h1>
                    </div>
                    <div style="padding: 30px 20px;">
                        <h2 style="color: #333;">Email Verification</h2>
                        <p style="color: #666; line-height: 1.6;">
                            Hello! Thank you for registering with Xiangxin AI Guardrails Platform.
                        </p>
                        <p style="color: #666; line-height: 1.6;">
                            Your verification code is:
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="background-color: #1890ff; color: white; padding: 15px 30px; font-size: 24px; font-weight: bold; border-radius: 5px; letter-spacing: 5px;">
                                {verification_code}
                            </span>
                        </div>
                        <p style="color: #666; line-height: 1.6;">
                            This verification code is valid for 10 minutes. Please use it promptly.
                        </p>
                        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #999; font-size: 14px;">
                                Xiangxin AI Guardrails - Securing AI Applications
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

    return subject, html_body

def send_verification_email(email: str, verification_code: str, language: str = 'en') -> bool:
    """
    Send verification email

    Args:
        email: Recipient email address
        verification_code: Verification code
        language: Language code ('zh' for Chinese, 'en' for English)
    """
    if not settings.smtp_username or not settings.smtp_password:
        raise Exception("SMTP configuration is not set")

    try:
        # Get email template based on language
        subject, html_body = get_email_template(language, verification_code)
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.smtp_username
        msg['To'] = email
        
        # 添加HTML内容
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 发送邮件
        if settings.smtp_use_ssl:
            # 使用SSL连接
            with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
        else:
            # 使用TLS连接
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def get_verification_expiry() -> datetime:
    """获取验证码过期时间（10分钟后）"""
    return datetime.utcnow() + timedelta(minutes=10)