#!/usr/bin/env python3
"""
简单的DeepSeek API使用示例
展示如何为Digital Twin SG项目调用API
"""

import requests
import json

def simple_deepseek_call():
    """简单的API调用示例"""
    print("🚀 调用DeepSeek API...")
    
    # 使用你的API密钥
    api_key = "sk-0854816410cf443fb2fe9cad0f44ebe2"
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 针对前端优化的具体问题
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "你是前端架构专家，正在优化Digital Twin SG项目的前端。项目有172,173个AI Agents，需要突出数学严谨性和透明度。"
            },
            {
                "role": "user",
                "content": "请为Digital Twin SG的dashboard.html设计一个数据透明度展示区域。要求：1) 显示172K样本规模 2) 显示99.9%置信度 3) 数据来源可追溯链接 4) 专业设计。请提供HTML/CSS代码片段。"
            }
        ],
        "temperature": 0.3,
        "max_tokens": 800
    }
    
    try:
        print("📡 发送请求...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            
            print("✅ API调用成功!")
            print("\n" + "="*60)
            print("🤖 DeepSeek生成的代码建议:")
            print("="*60)
            print(reply)
            
            # 保存结果
            with open("/Users/tigerli/Desktop/Digital Twins Singapore/data/deepseek_output.html", "w", encoding="utf-8") as f:
                f.write("<!-- DeepSeek API生成的数据透明度组件 -->\n")
                f.write("<!-- 生成时间: 2026-03-08 -->\n")
                f.write("<!-- 项目: Digital Twin SG -->\n\n")
                f.write(reply)
            
            print("\n" + "="*60)
            print("📄 代码已保存到: data/deepseek_output.html")
            
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🎯 DeepSeek API实战示例 - Digital Twin SG前端优化")
    print("="*60)
    print(f"🔑 使用API密钥: sk-08548...")
    print(f"🎯 目标: 生成数据透明度组件代码")
    print("="*60)
    
    if simple_deepseek_call():
        print("\n✅ 示例完成!")
        print("💡 这展示了如何用DeepSeek API:")
        print("   1. 解决具体的前端问题")
        print("   2. 生成专业的代码建议")
        print("   3. 保存结果供后续使用")
    else:
        print("\n❌ 示例失败")