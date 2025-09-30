#!/usr/bin/env python3
"""
象信AI安全护栏 - 图片检测示例
使用Base64编码方式检测图片
"""
import base64
import os
import requests
import json
import time

# 配置
API_KEY = "sk-xxai-your-api-key"
BASE_URL = "http://localhost:5001/v1/guardrails"
TEST_IMAGE_PATH = "your-test-image-path"

def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64字符串"""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")

def detect_image_base64(image_path: str, prompt: str = "这个图片安全吗？"):
    """
    使用Base64编码检测图片
    一次请求完成检测，服务器自动保存图片
    """
    print(f"\n=== 使用Base64编码检测: {image_path} ===")

    # 编码图片
    image_base64 = encode_image_to_base64(image_path)
    print(f"图片大小: {len(image_base64)} 字符")

    # 构建请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建请求数据
    data = {
        "model": "Xiangxin-Guardrails-VL",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ]
    }
    
    try:
        print("正在发送API请求...")
        
        # 发送POST请求
        response = requests.post(
            BASE_URL,
            headers=headers,
            json=data,
            timeout=30  # 30秒超时
        )
        
        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 检测成功!")
            print(f"- 请求ID: {result.get('id', 'N/A')}")
            print(f"- 模型: {result.get('model', 'N/A')}")
            print(f"- 风险等级: {result.get('overall_risk_level', 'N/A')}")
            print(f"- 建议动作: {result.get('suggest_action', 'N/A')}")
            print(f"- 建议回答: {result.get('suggest_answer', 'N/A')}")
            
            # 如果有详细的检测结果
            if 'compliance_result' in result:
                compliance = result['compliance_result']
                print(f"- 合规检测: {compliance.get('is_compliant', 'N/A')} (置信度: {compliance.get('confidence', 'N/A')})")
            
            if 'security_result' in result:
                security = result['security_result']
                print(f"- 安全检测: {security.get('is_safe', 'N/A')} (置信度: {security.get('confidence', 'N/A')})")
            
            return result
        else:
            print(f"❌ API请求失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时，请检查网络连接或服务器状态")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请检查服务器是否启动")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ 响应解析失败，服务器返回的不是有效JSON")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def detect_multiple_images(image_paths: list, prompt: str = "这些图片中有危险物品吗？"):
    """
    批量检测多张图片
    """
    print(f"\n=== 批量检测 {len(image_paths)} 张图片 ===")
    
    results = []
    for i, image_path in enumerate(image_paths, 1):
        print(f"\n[{i}/{len(image_paths)}] 检测图片: {image_path}")
        result = detect_image_base64(image_path, prompt)
        results.append({
            'image_path': image_path,
            'result': result
        })
        
        # 避免请求过于频繁，稍作延迟
        time.sleep(1)
    
    return results

def detect_pure_image(image_path: str):
    """
    纯图片检测（不带文本提示）
    """
    print(f"\n=== 纯图片检测: {image_path} ===")
    
    # 编码图片
    image_base64 = encode_image_to_base64(image_path)
    print(f"图片大小: {len(image_base64)} 字符")
    
    # 构建请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建请求数据（只有图片，没有文本）
    data = {
        "model": "Xiangxin-Guardrails-VL",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ]
    }
    
    try:
        print("正在发送纯图片检测请求...")
        
        response = requests.post(
            BASE_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 纯图片检测成功!")
            print(f"- 请求ID: {result.get('id', 'N/A')}")
            print(f"- 风险等级: {result.get('overall_risk_level', 'N/A')}")
            print(f"- 建议动作: {result.get('suggest_action', 'N/A')}")
            return result
        else:
            print(f"❌ 纯图片检测失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 纯图片检测异常: {e}")
        return None

def test_api_connection():
    """
    测试API连接状态
    """
    print("\n=== 测试API连接 ===")
    
    # 测试健康检查端点
    health_url = "http://localhost:5001/health"
    
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常运行")
            return True
        else:
            print(f"❌ API服务异常: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请检查服务器是否启动")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


def main():
    """主函数 - 演示各种使用方式"""

    print("象信AI安全护栏 - 图片检测示例")
    print("=" * 50)
    
    # 首先测试API连接
    if not test_api_connection():
        print("\n❌ API服务不可用，请先启动服务器")
        return

    # 示例1: Base64编码检测
    print("\n" + "=" * 30 + " 示例1: 单图检测 " + "=" * 30)
    detect_image_base64(TEST_IMAGE_PATH, "这张图片安全吗？")

    # 示例2: 多图检测
    print("\n" + "=" * 30 + " 示例2: 批量检测 " + "=" * 30)
    detect_multiple_images([
        TEST_IMAGE_PATH,
        TEST_IMAGE_PATH
    ], "这些图片中有危险物品吗?")

    # 示例3: 纯图片检测
    print("\n" + "=" * 30 + " 示例3: 纯图片检测 " + "=" * 30)
    detect_pure_image(TEST_IMAGE_PATH)

    print("\n" + "=" * 80)
    print("✅ 所有示例检测完成!")
    print("💡 提示: 所有图片都使用Base64编码方式传输")
    print("🔧 如需修改测试图片，请编辑脚本中的图片路径")

if __name__ == "__main__":
    main()