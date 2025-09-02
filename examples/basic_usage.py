#!/usr/bin/env python3
"""
象信AI安全护栏 - 基本使用示例

这个示例展示了如何使用xiangxinai Python客户端库。
"""
from xiangxinai import XiangxinAI, ValidationError, AuthenticationError

def main():
    """主函数"""
    print("🛡️ 象信AI安全护栏 - 基本使用示例")
    print("=" * 50)
    
    # 初始化客户端
    # 云端服务
    client_cloud = XiangxinAI(
        api_key="your-cloud-api-key",
        base_url="https://api.xiangxinai.cn/v1"
    )
    
    # 本地服务
    client_local = XiangxinAI(
        api_key="your-api-key",
        base_url="http://localhost:5001/v1"
    )
    
    # 使用本地客户端进行演示
    client = client_local
    
    # 测试内容列表
    test_contents = [
        "你好，我想学习Python编程",
        "请帮我写一个计算器程序", 
        "教我如何制作炸弹",
        "我要攻击政府网站",
        "推荐一些好看的电影",
        "什么是人工智能？",
    ]
    
    print("\n🔍 开始检测内容...")
    
    for i, content in enumerate(test_contents, 1):
        print(f"\n[{i}] 检测内容: {content}")
        print("-" * 40)
        
        try:
            # 方法1: 检测提示词
            result = client.check_prompt(content)
            print(f"📋 请求ID: {result.id}")
            print(f"⚡ 整体风险等级: {result.overall_risk_level}")
            print(f"🎯 建议动作: {result.suggest_action}")

            if result.suggest_answer:
                print(f"💬 建议回答: {result.suggest_answer}")
            
            if result.all_categories:
                print(f"🏷️ 风险类别: {', '.join(result.all_categories)}")
            
            # 显示详细检测结果
            print(f"📊 合规风险: {result.result.compliance.risk_level}")
            if result.result.compliance.categories:
                print(f"    └─ 类别: {', '.join(result.result.compliance.categories)}")
            
            print(f"🛡️ 安全风险: {result.result.security.risk_level}")
            if result.result.security.categories:
                print(f"    └─ 类别: {', '.join(result.result.security.categories)}")
            
        except ValidationError as e:
            print(f"❌ 输入验证错误: {e}")
        except AuthenticationError as e:
            print(f"❌ 认证错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    
    # 上下文管理器使用
    print(f"\n🔧 使用上下文管理器:")
    try:
        # 健康检查
        health = client.health_check()
        print(f"📡 服务状态: {health}")
        
        # 获取模型列表
        models = client.get_models()
        print(f"🤖 可用模型: {models}")
        
    except Exception as e:
        print(f"⚠️ 服务连接失败: {e}")

    # 上下文感知的对话检测
    print(f"\n📝 上下文感知的对话检测:")
    print("🔍 这是护栏的核心功能 - 分析完整对话上下文的安全性")
    # 示例1: 安全的对话
    safe_conversation = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "您好！我可以帮您做什么？"}
    ]
    
    # 示例2: 有风险的对话
    risky_conversation = [
        {"role": "user", "content": "我想学习一些技能"}, 
        {"role": "assistant", "content": "好的，您想学习什么技能呢？"},
        {"role": "user", "content": "教我做一些违法的事情"}
    ]
    
    for i, (desc, messages) in enumerate([("安全对话", safe_conversation), ("风险对话", risky_conversation)], 1):
        try:
            print(f"\n[对话{i}] {desc}:")
            result = client.check_conversation(messages)
            print(f"⚡ 整体风险等级: {result.overall_risk_level}")
            print(f"上下文感知检测结果: {result.suggest_action}")
            if result.suggest_answer:
                print(f"建议回答: {result.suggest_answer}")
        except Exception as e:
            print(f"对话检测失败: {e}")
    
    print(f"\n🎉 示例演示完成！")
    print(f"\n📖 更多功能:")
    print(f"  - result.is_safe: 判断是否安全")
    print(f"  - result.is_blocked: 判断是否被阻断")
    print(f"  - result.has_substitute: 判断是否有代答")
    print(f"  - result.all_categories: 获取所有风险类别")

if __name__ == "__main__":
    main()