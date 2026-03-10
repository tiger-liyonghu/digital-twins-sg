#!/usr/bin/env python3
"""
验证DeepSeek API正常工作
"""

import requests
import json

def verify_api():
    print("🔍 验证DeepSeek API工作状态...")
    
    api_key = "sk-0854816410cf443fb2fe9cad0f44ebe2"
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 非常简单的测试
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "用一句话回答：Digital Twin SG项目有多少个AI Agents？"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print("📡 发送验证请求...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            
            print(f"✅ API工作正常!")
            print(f"🤖 回复: {reply}")
            
            # 显示使用统计
            if "usage" in result:
                usage = result["usage"]
                print(f"📈 Token使用:")
                print(f"  提示词: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  完成: {usage.get('completion_tokens', 'N/A')}")
                print(f"  总计: {usage.get('total_tokens', 'N/A')}")
            
            return True
        else:
            print(f"❌ API响应异常: {response.status_code}")
            print(f"错误: {response.text[:100]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("✅ DeepSeek API验证测试")
    print("="*50)
    
    if verify_api():
        print("\n" + "="*50)
        print("🎯 验证结果: API工作完全正常!")
        print("="*50)
        
        print("\n📋 验证项目:")
        print("✅ API密钥有效: sk-08548...")
        print("✅ 网络连接正常")
        print("✅ 服务响应正常")
        print("✅ Token计数正常")
        
        print("\n💡 这意味着:")
        print("• 可以安全使用DeepSeek API")
        print("• 你的API密钥配置正确")
        print("• 网络环境正常")
        print("• 可以开始实际开发工作")
        
        print("\n🚀 建议立即:")
        print("1. 继续前端优化工作")
        print("2. 使用API生成具体解决方案")
        print("3. 监控API使用成本")
        print("4. 定期测试API状态")
        
    else:
        print("\n❌ API验证失败")
        print("💡 请检查:")
        print("   1. API密钥是否正确")
        print("   2. 网络连接是否正常")
        print("   3. 账户余额是否充足")