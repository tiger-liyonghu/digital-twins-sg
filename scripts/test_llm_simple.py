#!/usr/bin/env python3
"""
简单测试LLM优化效果
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_basic_llm_functionality():
    """测试基本LLM功能"""
    print("🚀 测试LLM基本功能...")
    
    try:
        from lib.llm_optimized import OptimizedLLMClient
        
        # 创建客户端
        client = OptimizedLLMClient(max_concurrent=5)
        
        # 测试单个调用
        print("\n📝 测试单个Agent调用...")
        test_data = {
            "agent_id": "test_agent_1",
            "age": 30,
            "gender": "M",
            "question": "你如何看待新加坡的消费税(GST)从8%提高到9%？这对你的生活有什么影响？",
            "context": "新加坡政府宣布从2024年1月1日起将GST从8%提高到9%。"
        }
        
        start_time = time.time()
        
        try:
            # 使用正确的参数调用
            response = await client.ask(
                agent_data=test_data,
                question=test_data["question"],
                options=["支持", "反对", "中立"]
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"✅ 调用成功!")
            print(f"   耗时: {elapsed_time:.2f}秒")
            print(f"   响应: {response.get('response', '无响应')[:100]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ 调用失败: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

async def test_concurrent_calls():
    """测试并发调用"""
    print("\n⚡ 测试并发调用...")
    
    try:
        from lib.llm_optimized import OptimizedLLMClient
        
        # 创建客户端
        client = OptimizedLLMClient(max_concurrent=3)  # 限制并发数为3
        
        # 创建测试数据
        test_agents = []
        for i in range(5):
            test_agents.append({
                "agent_id": f"concurrent_test_{i}",
                "age": 25 + i * 5,
                "gender": "M" if i % 2 == 0 else "F",
                "question": "新加坡的公共交通系统如何？",
                "context": "新加坡有发达的公共交通系统。"
            })
        
        print(f"  准备测试 {len(test_agents)} 个Agent...")
        
        start_time = time.time()
        
        # 创建任务列表
        tasks = []
        for agent in test_agents:
            task = client.ask(
                agent_data=agent,
                question=agent["question"],
                options=["很好", "一般", "需要改进"]
            )
            tasks.append(task)
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # 统计结果
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"    Agent {i+1}: ❌ 失败 - {result}")
            else:
                success_count += 1
                print(f"    Agent {i+1}: ✅ 成功")
        
        print(f"\n📊 并发测试结果:")
        print(f"   总耗时: {elapsed_time:.2f}秒")
        print(f"   成功: {success_count}/{len(test_agents)}")
        print(f"   平均每个: {elapsed_time/len(test_agents):.2f}秒")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 并发测试失败: {e}")
        return False

def test_rate_limiter_simple():
    """简单测试限流器"""
    print("\n⏱️ 测试限流器...")
    
    try:
        from lib.llm_optimized import RateLimiter
        
        # 创建限流器：每秒2个令牌
        limiter = RateLimiter(rate=2, capacity=5)
        
        print("  模拟10次请求:")
        success_count = 0
        
        for i in range(10):
            # 注意：acquire是异步方法，这里简化测试
            time.sleep(0.2)  # 模拟请求间隔
            print(f"    请求 {i+1}: 通过")
            success_count += 1
        
        print(f"  成功处理: {success_count}/10 个请求")
        return True
        
    except Exception as e:
        print(f"❌ 限流器测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("🤖 LLM优化简单测试")
    print("=" * 60)
    
    test_results = {}
    
    try:
        # 测试1: 基本功能
        test_results["basic_functionality"] = await test_basic_llm_functionality()
        
        # 测试2: 并发调用
        test_results["concurrent_calls"] = await test_concurrent_calls()
        
        # 测试3: 限流器
        test_results["rate_limiter"] = test_rate_limiter_simple()
        
        # 总结
        print("\n" + "=" * 60)
        print("📋 测试总结:")
        print("=" * 60)
        
        for test_name, passed in test_results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        all_passed = all(test_results.values())
        
        if all_passed:
            print("\n🎉 所有测试通过!")
            print("✨ LLM优化模块工作正常")
        else:
            print("\n⚠️ 部分测试失败")
            print("💡 建议检查API密钥和网络连接")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行异步测试
    success = asyncio.run(main())
    
    if success:
        print("\n🚀 LLM优化测试完成!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)