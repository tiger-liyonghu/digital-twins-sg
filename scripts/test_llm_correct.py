#!/usr/bin/env python3
"""
正确测试LLM优化模块
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_llm_optimized():
    """测试优化版LLM客户端"""
    print("🚀 测试优化版LLM客户端...")
    
    try:
        from lib.llm_optimized import OptimizedLLMClient
        
        # 创建客户端
        client = OptimizedLLMClient(max_concurrent=3)
        
        # 测试1: 单个Agent调用
        print("\n📝 测试单个Agent调用...")
        
        persona = """我是张伟，35岁，男性，新加坡公民。
职业：软件工程师
月收入：S$8,000
教育：大学本科
居住：淡滨尼，HDB四房式
家庭：已婚，有一个孩子
政治倾向：中间偏右
宗教信仰：佛教
性格：外向、尽责、开放"""
        
        question = "你如何看待新加坡的消费税(GST)从8%提高到9%？"
        options = ["支持", "反对", "中立"]
        context = "新加坡政府宣布从2024年1月1日起将GST从8%提高到9%。"
        
        start_time = time.time()
        
        try:
            result = await client.ask_agent(
                persona=persona,
                question=question,
                options=options,
                context=context,
                temperature=0.7
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"✅ 调用成功!")
            print(f"   耗时: {elapsed_time:.2f}秒")
            print(f"   选择: {result.get('choice', '无')}")
            print(f"   理由: {result.get('reason', '无')[:80]}...")
            print(f"   意愿度: {result.get('intensity', '无')}")
            
            single_test_passed = True
            
        except Exception as e:
            print(f"❌ 调用失败: {e}")
            single_test_passed = False
        
        # 测试2: 并发调用
        print("\n⚡ 测试并发调用...")
        
        test_personas = [
            """我是李明，28岁，男性，新加坡PR。
职业：市场营销
月收入：S$5,500
教育：大学本科
居住：裕廊东，公寓
家庭：单身
政治倾向：自由派
宗教信仰：无
性格：外向、随和""",
            
            """我是陈美玲，42岁，女性，新加坡公民。
职业：教师
月收入：S$6,800
教育：硕士
居住：大巴窑，HDB五房式
家庭：已婚，有两个孩子
政治倾向：保守派
宗教信仰：基督教
性格：内向、尽责""",
            
            """我是阿都拉，33岁，男性，新加坡公民。
职业：商人
月收入：S$9,500
教育：大学本科
居住：武吉知马，有地住宅
家庭：已婚，有三个孩子
政治倾向：中间派
宗教信仰：伊斯兰教
性格：外向、开放"""
        ]
        
        tasks = []
        for i, persona in enumerate(test_personas):
            task = client.ask_agent(
                persona=persona,
                question="新加坡的公共交通系统如何？需要改进吗？",
                options=["很好，不需要改进", "一般，需要小改进", "较差，需要大改进"],
                context="新加坡的公共交通包括地铁、巴士和出租车。",
                temperature=0.7
            )
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed_time = time.time() - start_time
        
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"    Agent {i+1}: ❌ 失败 - {result}")
            else:
                success_count += 1
                print(f"    Agent {i+1}: ✅ 成功 - 选择: {result.get('choice', '无')}")
        
        print(f"\n📊 并发测试结果:")
        print(f"   总耗时: {elapsed_time:.2f}秒")
        print(f"   成功: {success_count}/{len(test_personas)}")
        print(f"   平均每个: {elapsed_time/len(test_personas):.2f}秒")
        
        concurrent_test_passed = success_count > 0
        
        # 测试3: 查看统计信息
        print("\n📈 查看性能统计...")
        stats = client.get_stats()
        print(f"   总调用次数: {stats['total_calls']}")
        print(f"   成功调用: {stats['successful_calls']}")
        print(f"   失败调用: {stats['failed_calls']}")
        print(f"   总token数: {stats['total_tokens']}")
        print(f"   总成本: ${stats['total_cost_usd']:.4f}")
        print(f"   平均响应时间: {stats['total_duration']/max(stats['total_calls'], 1):.2f}秒")
        
        # 总结
        print("\n" + "=" * 60)
        print("📋 LLM优化测试总结:")
        print("=" * 60)
        
        all_passed = single_test_passed and concurrent_test_passed
        
        if all_passed:
            print("✅ 所有测试通过!")
            print("✨ 优化版LLM客户端工作正常")
            print("🚀 可以用于生产环境")
        else:
            print("⚠️ 部分测试失败")
            if not single_test_passed:
                print("   - 单个Agent调用失败")
            if not concurrent_test_passed:
                print("   - 并发调用失败")
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("🤖 LLM优化模块测试")
    print("=" * 60)
    
    success = await test_llm_optimized()
    
    if success:
        print("\n🎉 测试成功完成!")
        print("💡 建议下一步:")
        print("  1. 在生产代码中使用OptimizedLLMClient")
        print("  2. 根据实际需求调整max_concurrent参数")
        print("  3. 监控API使用成本和性能")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        print("🔧 需要调试的问题:")
        print("  1. 检查DEEPSEEK_API_KEY配置")
        print("  2. 检查网络连接")
        print("  3. 检查API配额和限制")
        sys.exit(1)

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())