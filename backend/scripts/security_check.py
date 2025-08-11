#!/usr/bin/env python3
"""
安全检查和修复脚本
检查常见的安全配置问题并提供修复建议
"""

import os
import sys
import secrets
import hashlib
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config import settings

def generate_secure_jwt_key():
    """生成安全的JWT密钥"""
    return secrets.token_urlsafe(64)

def generate_secure_password(length=16):
    """生成安全的随机密码"""
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def check_jwt_security():
    """检查JWT配置安全性"""
    issues = []
    
    # 检查JWT密钥长度和复杂性
    if len(settings.jwt_secret_key) < 32:
        issues.append({
            'level': 'HIGH',
            'category': 'JWT',
            'issue': 'JWT密钥长度不足',
            'description': f'当前JWT密钥长度为{len(settings.jwt_secret_key)}字符，建议至少64字符',
            'fix': f'建议使用: {generate_secure_jwt_key()}'
        })
    
    # 检查是否使用默认密钥
    weak_keys = [
        'xiangxin-guardrails-jwt-secret-key-2024',
        'your-secret-key',
        'secret',
        'jwt-secret'
    ]
    
    if settings.jwt_secret_key in weak_keys:
        issues.append({
            'level': 'CRITICAL',
            'category': 'JWT',
            'issue': '使用了默认或弱JWT密钥',
            'description': '当前使用的是默认或已知的弱密钥',
            'fix': f'请立即更换为安全密钥: {generate_secure_jwt_key()}'
        })
    
    return issues

def check_admin_security():
    """检查管理员账户安全性"""
    issues = []
    
    # 检查默认管理员密码
    weak_passwords = [
        'admin',
        'password',
        '123456',
        'xiangxin@2024',
        'admin123'
    ]
    
    if settings.super_admin_password in weak_passwords:
        issues.append({
            'level': 'CRITICAL',
            'category': 'Admin',
            'issue': '使用了默认或弱管理员密码',
            'description': '当前管理员密码过于简单，容易被破解',
            'fix': f'建议更换为强密码: {generate_secure_password()}'
        })
    
    # 检查管理员用户名
    if settings.super_admin_username == 'admin':
        issues.append({
            'level': 'MEDIUM',
            'category': 'Admin',
            'issue': '使用了默认管理员用户名',
            'description': '使用默认用户名增加了被攻击的风险',
            'fix': '建议更换为自定义邮箱地址'
        })
    
    return issues

def check_database_security():
    """检查数据库安全性"""
    issues = []
    
    # 检查数据库URL是否包含弱密码
    db_url = settings.database_url
    if 'password' in db_url.lower() or '123456' in db_url:
        issues.append({
            'level': 'HIGH',
            'category': 'Database',
            'issue': '数据库密码可能过于简单',
            'description': '数据库连接字符串可能包含弱密码',
            'fix': '请使用强密码并考虑使用环境变量'
        })
    
    return issues

def check_cors_security():
    """检查CORS配置安全性"""
    issues = []
    
    if settings.cors_origins == "*":
        issues.append({
            'level': 'MEDIUM',
            'category': 'CORS',
            'issue': 'CORS配置过于宽松',
            'description': '允许所有来源访问可能带来安全风险',
            'fix': '建议配置具体的域名，如: https://yourdomain.com'
        })
    
    return issues

def check_debug_mode():
    """检查调试模式"""
    issues = []
    
    if settings.debug:
        issues.append({
            'level': 'MEDIUM',
            'category': 'Debug',
            'issue': '生产环境开启了调试模式',
            'description': '调试模式可能泄露敏感信息',
            'fix': '生产环境请设置 DEBUG=false'
        })
    
    return issues

def check_smtp_security():
    """检查SMTP配置安全性"""
    issues = []
    
    if settings.smtp_password and settings.smtp_password in ['your-email-password', 'password']:
        issues.append({
            'level': 'HIGH',
            'category': 'SMTP',
            'issue': '使用了默认SMTP密码',
            'description': 'SMTP密码未正确配置',
            'fix': '请配置正确的邮箱密码'
        })
    
    return issues

def check_file_permissions():
    """检查关键文件权限"""
    issues = []
    
    # 检查.env文件权限
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        stat_info = env_file.stat()
        # 检查是否对其他用户可读
        if stat_info.st_mode & 0o044:  # 其他用户或组可读
            issues.append({
                'level': 'HIGH',
                'category': 'File Permissions',
                'issue': '.env文件权限过于宽松',
                'description': '.env文件包含敏感信息，不应对其他用户可读',
                'fix': f'运行: chmod 600 {env_file}'
            })
    
    return issues

def check_api_key_security():
    """检查API密钥安全性"""
    issues = []
    
    if settings.guardrails_model_api_key == 'your-model-api-key':
        issues.append({
            'level': 'MEDIUM',
            'category': 'API Key',
            'issue': '模型API密钥未配置',
            'description': '使用默认占位符可能导致服务无法正常工作',
            'fix': '请配置正确的模型API密钥'
        })
    
    return issues

def generate_security_report():
    """生成安全检查报告"""
    print("=" * 60)
    print("象信AI安全护栏平台 - 安全检查报告")
    print("=" * 60)
    
    all_issues = []
    
    # 执行各项检查
    checks = [
        ('JWT安全性', check_jwt_security),
        ('管理员账户安全性', check_admin_security),
        ('数据库安全性', check_database_security),
        ('CORS配置', check_cors_security),
        ('调试模式', check_debug_mode),
        ('SMTP配置', check_smtp_security),
        ('文件权限', check_file_permissions),
        ('API密钥', check_api_key_security),
    ]
    
    for check_name, check_func in checks:
        print(f"\n📋 检查: {check_name}")
        issues = check_func()
        
        if not issues:
            print("✅ 未发现安全问题")
        else:
            for issue in issues:
                all_issues.append(issue)
                level_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                print(f"{level_emoji.get(issue['level'], '⚪')} {issue['level']}: {issue['issue']}")
                print(f"   描述: {issue['description']}")
                print(f"   修复建议: {issue['fix']}")
                print()
    
    # 统计报告
    print("\n" + "=" * 60)
    print("安全检查汇总")
    print("=" * 60)
    
    if not all_issues:
        print("🎉 恭喜！未发现安全问题。")
        return True
    
    critical_count = len([i for i in all_issues if i['level'] == 'CRITICAL'])
    high_count = len([i for i in all_issues if i['level'] == 'HIGH'])
    medium_count = len([i for i in all_issues if i['level'] == 'MEDIUM'])
    low_count = len([i for i in all_issues if i['level'] == 'LOW'])
    
    print(f"🔴 严重问题: {critical_count}")
    print(f"🟠 高风险问题: {high_count}")
    print(f"🟡 中风险问题: {medium_count}")
    print(f"🟢 低风险问题: {low_count}")
    print(f"📊 总计: {len(all_issues)} 个问题")
    
    if critical_count > 0:
        print("\n⚠️  警告：发现严重安全问题，请立即修复！")
        return False
    elif high_count > 0:
        print("\n⚠️  警告：发现高风险安全问题，建议尽快修复。")
        return False
    else:
        print("\n✅ 未发现严重安全问题，但建议修复中低风险问题以提高安全性。")
        return True

def generate_secure_env_template():
    """生成安全的.env模板"""
    print("\n" + "=" * 60)
    print("生成安全配置模板")
    print("=" * 60)
    
    template = f"""# 应用配置
APP_NAME=Xiangxin Guardrails
APP_VERSION=1.0.0
DEBUG=false

# 超级管理员配置
# ⚠️ 请务必修改默认管理员用户名和密码！
SUPER_ADMIN_USERNAME=admin@yourdomain.com
SUPER_ADMIN_PASSWORD={generate_secure_password(20)}

# 数据目录配置
DATA_DIR=~/xiangxin-guardrails-data

# 数据库配置
# ⚠️ 请使用强密码
DATABASE_URL=postgresql://xiangxin:YOUR_SECURE_DB_PASSWORD@localhost:54321/xiangxin_guardrails

# 模型配置
GUARDRAILS_MODEL_API_URL=http://localhost:58002/v1
GUARDRAILS_MODEL_API_KEY=your-actual-model-api-key
GUARDRAILS_MODEL_NAME=Xiangxin-Guardrails-Text

# API配置
# ⚠️ 生产环境请配置具体域名
CORS_ORIGINS=https://yourdomain.com

# 日志配置
LOG_LEVEL=INFO

# JWT配置
# ⚠️ 使用安全的随机密钥
JWT_SECRET_KEY={generate_secure_jwt_key()}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 邮箱配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-secure-email-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# 服务器配置
UVICORN_WORKERS=4
MAX_CONCURRENT_REQUESTS=100
"""
    
    print("🔐 安全的.env配置模板:")
    print(template)
    
    # 保存到文件
    template_file = Path(__file__).parent.parent / '.env.secure.template'
    with open(template_file, 'w') as f:
        f.write(template)
    
    print(f"✅ 模板已保存到: {template_file}")
    print("📋 请根据模板更新您的.env文件")

def main():
    print("🛡️  象信AI安全护栏平台 - 安全检查工具")
    print("此工具将检查常见的安全配置问题并提供修复建议\n")
    
    # 生成安全检查报告
    is_secure = generate_security_report()
    
    # 生成安全配置模板
    generate_secure_env_template()
    
    print("\n" + "=" * 60)
    print("安全建议")
    print("=" * 60)
    print("1. 🔐 定期更新JWT密钥和管理员密码")
    print("2. 🔒 使用HTTPS部署生产环境")
    print("3. 🌐 配置防火墙限制不必要的端口访问")
    print("4. 📊 启用访问日志监控")
    print("5. 🔄 定期备份数据库")
    print("6. 📱 考虑启用双因子认证（2FA）")
    print("7. 🛡️  定期运行此安全检查工具")
    
    if not is_secure:
        print("\n❌ 安全检查失败，请修复发现的问题后重新运行。")
        sys.exit(1)
    else:
        print("\n✅ 安全检查通过！")
        sys.exit(0)

if __name__ == "__main__":
    main()