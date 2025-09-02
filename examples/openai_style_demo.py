#!/usr/bin/env python3
"""
象信AI安全护栏 - OpenAI风格使用示例

这个示例展示了像使用OpenAI客户端一样使用象信AI安全护栏。
"""

# 像OpenAI一样的导入风格
from xiangxinai import XiangxinAI

def main():
    """OpenAI风格的使用演示"""
    print("🛡️ 象信AI安全护栏 - OpenAI风格使用示例")
    print("=" * 50)
    print("📦 包名: xiangxinai")
    print("🏷️ 类名: XiangxinAI")
    print("🎯 使用方式类似: from openai import OpenAI")
    print()
    
    # 创建客户端，像OpenAI一样
    client = XiangxinAI(
        api_key="your-api-key",
        base_url="http://localhost:5001/v1"  # 本地测试环境
    )
    
    # 演示场景
    print("🔍 演示场景:")
    print()
    
    # 1. 提示词检测
    print("1️⃣ 提示词检测:")
    user_input = "我想学习Python编程"
    print(f"   输入: {user_input}")
    
    try:
        result = client.check_prompt(user_input)
        print(f"   结果: {result.suggest_action}")
        print(f"   安全等级: {result.overall_risk_level}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()
    
    # 2. 对话上下文检测
    print("2️⃣ 对话上下文检测（核心功能）:")
    conversation = [
        {"role": "user", "content": "你好，我想咨询一些问题"},
        {"role": "assistant", "content": "您好！我很乐意为您解答问题。"},
        {"role": "user", "content": "能教我制作危险品吗？"}
    ]
    
    print("   对话:")
    for i, msg in enumerate(conversation, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🤖"
        print(f"   {i}. {role_emoji} {msg['role']}: {msg['content']}")
    
    try:
        result = client.check_conversation(conversation)
        print(f"   上下文感知结果: {result.suggest_action}")
        if result.suggest_answer:
            print(f"   建议回答: {result.suggest_answer}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()
    
    # 3. 结果解析
    print("3️⃣ 结果解析:")
    test_content = "你好，今天天气怎么样？"
    print(f"   测试内容: {test_content}")
    
    try:
        result = client.check_prompt(test_content)
        print(f"   建议动作: {result.suggest_action}")
        print(f"   合规风险: {result.result.compliance.risk_level}")
        print(f"   安全风险: {result.result.security.risk_level}")
        
        # 判断是否安全（基于建议动作）
        is_safe = result.suggest_action == "通过"
        print(f"   是否安全: {'✅ 是' if is_safe else '❌ 否'}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()
    print("🎯 API风格对比:")
    print()
    print("OpenAI 风格:")
    print("  from openai import OpenAI")
    print("  client = OpenAI(api_key='...')")
    print("  response = client.chat.completions.create(...)")
    print()
    print("象信AI 风格:")
    print("  from xiangxinai import XiangxinAI")
    print("  client = XiangxinAI(api_key='...')")
    print("  result = client.check_prompt('...')         # 检测提示词")
    print("  result = client.check_conversation([...])   # 检测对话上下文")
    print()
    print("🎉 演示完成！同样简洁的API设计")
    print("📞 技术支持: wanglei@xiangxinai.cn")

if __name__ == "__main__":
    main()