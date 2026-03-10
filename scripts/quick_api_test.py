#!/usr/bin/env python3
"""
快速DeepSeek API测试
"""

import requests
import json
from datetime import datetime

def quick_test():
    print("🔍 快速DeepSeek API测试...")
    
    api_key = "sk-0854816410cf443fb2fe9cad0f44ebe2"
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "Hello, test API connection. Reply with 'API connection successful!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print("📡 发送测试请求...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            print(f"✅ 成功! 回复: {reply}")
            
            # 显示token使用
            if "usage" in result:
                usage = result["usage"]
                print(f"📊 Token使用: {usage.get('total_tokens', 'N/A')}")
            
            return True
        else:
            print(f"❌ 失败: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 DeepSeek API快速测试")
    print("=" * 50)
    
    if quick_test():
        print("\n✅ API测试通过!")
        print("🔑 密钥: sk-08548... 有效")
        print("📅 时间:", datetime.now().strftime("%H:%M:%S"))
    else:
        print("\n❌ API测试失败")