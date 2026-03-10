#!/usr/bin/env python3
"""
测试DeepSeek API连接状态
"""

import requests
import time

def test_connection():
    print("🔍 测试DeepSeek API连接状态...")
    
    api_key = "sk-0854816410cf443fb2fe9cad0f44ebe2"
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 最小化的测试请求
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 5
    }
    
    try:
        print("📡 发送测试请求...")
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=10)
        end_time = time.time()
        
        print(f"⏱️ 响应时间: {(end_time - start_time):.2f}秒")
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API连接正常!")
            return True
        elif response.status_code == 401:
            print("❌ 认证失败 - API密钥无效")
            print(f"密钥: {api_key[:8]}...")
            return False
        elif response.status_code == 429:
            print("⚠️ 请求过多 - 需要等待")
            return False
        else:
            print(f"❌ 其他错误: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误 - 检查网络")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🔧 DeepSeek API连接测试")
    print("="*50)
    
    if test_connection():
        print("\n✅ 连接测试通过")
        print("💡 API密钥有效，可以正常使用")
    else:
        print("\n❌ 连接测试失败")
        print("💡 请检查:")
        print("   1. API密钥是否正确")
        print("   2. 网络连接是否正常")
        print("   3. API服务状态")