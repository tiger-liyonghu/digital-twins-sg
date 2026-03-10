#!/usr/bin/env python3
"""
测试Tiger的DeepSeek API密钥
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_deepseek_api():
    """测试DeepSeek API连接"""
    print("🔑 测试Tiger的DeepSeek API密钥...")
    print("=" * 60)
    
    try:
        # 从.env文件读取配置
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_url = "https://api.deepseek.com/v1/chat/completions"
        
        print(f"📋 API配置信息:")
        print(f"   密钥前8位: {api_key[:8]}...")
        print(f"   密钥长度: {len(api_key)} 字符")
        print(f"   API地址: {api_url}")
        
        if not api_key:
            print("❌ 未找到DEEPSEEK_API_KEY环境变量")
            return False
        
        # 测试API连接
        print("\n🚀 测试API连接...")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "请回复'API测试成功'来确认连接正常。"}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(api_url, json=payload, headers=headers) as response:
                    print(f"   状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        response_text = result["choices"][0]["message"]["content"]
                        print(f"   ✅ API测试成功!")
                        print(f"   响应: {response_text}")
                        
                        # 显示使用情况
                        if "usage" in result:
                            usage = result["usage"]
                            print(f"\n📊 API使用情况:")
                            print(f"   提示token: {usage.get('prompt_tokens', 'N/A')}")
                            print(f"   完成token: {usage.get('completion_tokens', 'N/A')}")
                            print(f"   总token: {usage.get('total_tokens', 'N/A')}")
                        
                        return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ API请求失败: {response.status}")
                        print(f"   错误信息: {error_text[:200]}")
                        return False
                        
            except aiohttp.ClientError as e:
                print(f"   ❌ 网络连接错误: {e}")
                return False
            except Exception as e:
                print(f"   ❌ 其他错误: {e}")
                return False
                
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_optimized_llm_client():
    """测试优化版LLM客户端使用新密钥"""
    print("\n🔧 测试优化版LLM客户端...")
    print("=" * 60)
    
    try:
        from lib.llm_optimized import OptimizedLLMClient
        
        # 创建客户端
        client = OptimizedLLMClient(max_concurrent=2)
        
        # 测试数据
        persona = """我是测试用户，用于验证API密钥。
这是一个简单的测试，确认系统工作正常。"""
        
        question = "这个测试是否成功？"
        options = ["成功", "失败", "不确定"]
        
        print("📝 发送测试请求...")
        
        try:
            result = await client.ask_agent(
                persona=persona,
                question=question,
                options=options,
                context="API密钥验证测试",
                temperature=0.7
            )
            
            print(f"   ✅ LLM客户端测试成功!")
            print(f"   选择: {result.get('choice', '无')}")
            print(f"   理由: {result.get('reason', '无')[:50]}...")
            
            # 显示统计信息
            stats = client.get_stats()
            print(f"\n📊 客户端统计:")
            print(f"   总调用次数: {stats['total_calls']}")
            print(f"   成功调用: {stats['successful_calls']}")
            print(f"   总成本: ${stats['total_cost_usd']:.6f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ LLM客户端测试失败: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入LLM客户端失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_api_key_report():
    """创建API密钥使用报告"""
    print("\n📋 创建API密钥配置报告...")
    
    try:
        from dotenv import load_dotenv
        import os
        
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
        
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        report = {
            "timestamp": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_status": "CONFIGURED" if api_key else "MISSING",
            "api_key_prefix": api_key[:8] + "..." if api_key else "",
            "key_length": len(api_key) if api_key else 0,
            "project": "Digital Twin SG",
            "environment": "Development",
            "configuration_files": [
                str(env_path),
                str(Path(__file__).parent.parent / "lib/config.py")
            ],
            "recommendations": [
                "定期轮换API密钥",
                "监控API使用成本",
                "设置使用限额告警",
                "备份密钥配置"
            ]
        }
        
        # 保存报告
        report_dir = Path(__file__).parent.parent / "data" / "output" / "api_tests"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"api_key_test_{__import__('time').strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ API密钥报告已保存: {report_file}")
        
        return report_file
        
    except Exception as e:
        print(f"❌ 创建报告失败: {e}")
        return None

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🔑 Tiger's DeepSeek API密钥验证测试")
    print("=" * 60)
    
    # 测试1: 基础API连接
    api_test_passed = await test_deepseek_api()
    
    # 测试2: LLM客户端测试
    llm_test_passed = False
    if api_test_passed:
        llm_test_passed = await test_optimized_llm_client()
    
    # 创建报告
    report_file = create_api_key_report()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    all_passed = api_test_passed and llm_test_passed
    
    if all_passed:
        print("✅ 所有测试通过!")
        print("🎉 Tiger的DeepSeek API密钥配置成功!")
        print("🚀 可以正常用于Digital Twin SG项目")
        
        print("\n💡 下一步建议:")
        print("  1. 运行完整的优化测试套件")
        print("  2. 监控API使用成本")
        print("  3. 设置使用限额告警")
        
        if report_file:
            print(f"\n📄 详细报告: {report_file}")
        
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败")
        
        if not api_test_passed:
            print("  - API基础连接测试失败")
        
        if not llm_test_passed:
            print("  - LLM客户端测试失败")
        
        print("\n🔧 故障排除建议:")
        print("  1. 检查API密钥是否正确")
        print("  2. 验证网络连接")
        print("  3. 检查API配额和限制")
        print("  4. 确认.env文件配置正确")
        
        sys.exit(1)

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())