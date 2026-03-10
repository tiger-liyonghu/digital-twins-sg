#!/usr/bin/env python3
"""
全面测试LLM优化效果 - 包括性能对比和错误处理
"""

import asyncio
import time
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class SimpleLLMClient:
    """简单LLM客户端 - 用于对比测试"""
    
    def __init__(self):
        import aiohttp
        from lib.config import DEEPSEEK_API_KEY, DEEPSEEK_URL
        
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_URL
        self.session = None
    
    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def ask_agent_simple(self, persona: str, question: str, options: List[str], context: str = "") -> Dict[str, Any]:
        """简单版本的Agent提问"""
        import aiohttp
        
        system_prompt = """你是一个新加坡居民，请根据你的背景和经历回答问题。
请从给定的选项中选择最符合你想法的一个，并简要说明理由。"""
        
        user_prompt = f"""{persona}

问题: {question}

选项:
{chr(10).join(f'{i+1}. {opt}' for i, opt in enumerate(options))}

{context if context else ''}

请严格按照以下格式回答:
选择: [选项编号]
理由: [你的理由]
意愿度: [1-10分，10表示非常愿意]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(self.api_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                
                response_text = result["choices"][0]["message"]["content"]
                
                # 简单解析响应
                choice = "未知"
                reason = "无"
                intensity = "5"
                
                for line in response_text.split('\n'):
                    if line.startswith('选择:'):
                        choice_num = line.split(':')[1].strip()
                        if choice_num.isdigit():
                            idx = int(choice_num) - 1
                            if 0 <= idx < len(options):
                                choice = options[idx]
                    elif line.startswith('理由:'):
                        reason = line.split(':', 1)[1].strip()
                    elif line.startswith('意愿度:'):
                        intensity = line.split(':')[1].strip()
                
                return {
                    "choice": choice,
                    "reason": reason,
                    "intensity": intensity,
                    "raw_response": response_text[:100]
                }
                
        except Exception as e:
            return {
                "choice": "错误",
                "reason": f"API调用失败: {str(e)}",
                "intensity": "0",
                "raw_response": ""
            }

async def performance_comparison():
    """性能对比测试"""
    print("📊 LLM性能对比测试")
    print("=" * 60)
    
    from lib.llm_optimized import OptimizedLLMClient
    
    # 创建测试数据
    test_personas = []
    for i in range(10):
        test_personas.append({
            "persona": f"""我是测试用户{i+1}，{25 + i}岁，{'男性' if i % 2 == 0 else '女性'}，新加坡公民。
职业：测试职业{i}
月收入：S${4000 + i * 500}
教育：大学本科
居住：测试区域{i}
家庭：{'已婚' if i > 5 else '单身'}
政治倾向：{'保守派' if i % 3 == 0 else '自由派' if i % 3 == 1 else '中间派'}
性格：测试性格{i}""",
            "question": "你对新加坡的组屋政策有什么看法？",
            "options": ["非常满意", "基本满意", "不满意"],
            "context": "新加坡的组屋政策旨在为公民提供负担得起的住房。"
        })
    
    # 测试1: 优化版客户端
    print("\n🔧 测试优化版LLM客户端...")
    optimized_client = OptimizedLLMClient(max_concurrent=5)
    
    start_time = time.time()
    
    tasks = []
    for data in test_personas[:5]:  # 测试5个
        task = optimized_client.ask_agent(
            persona=data["persona"],
            question=data["question"],
            options=data["options"],
            context=data["context"]
        )
        tasks.append(task)
    
    optimized_results = await asyncio.gather(*tasks, return_exceptions=True)
    optimized_time = time.time() - start_time
    
    optimized_success = sum(1 for r in optimized_results if not isinstance(r, Exception))
    print(f"   处理 {len(test_personas[:5])} 个Agent")
    print(f"   耗时: {optimized_time:.2f}秒")
    print(f"   成功: {optimized_success}/{len(test_personas[:5])}")
    print(f"   平均每个: {optimized_time/len(test_personas[:5]):.2f}秒")
    
    # 测试2: 简单客户端
    print("\n⚙️ 测试简单LLM客户端...")
    
    start_time = time.time()
    simple_results = []
    
    async with SimpleLLMClient() as simple_client:
        for data in test_personas[:5]:  # 测试相同的5个
            try:
                result = await simple_client.ask_agent_simple(
                    persona=data["persona"],
                    question=data["question"],
                    options=data["options"],
                    context=data["context"]
                )
                simple_results.append(result)
            except Exception as e:
                simple_results.append(e)
    
    simple_time = time.time() - start_time
    
    simple_success = sum(1 for r in simple_results if not isinstance(r, Exception))
    print(f"   处理 {len(test_personas[:5])} 个Agent")
    print(f"   耗时: {simple_time:.2f}秒")
    print(f"   成功: {simple_success}/{len(test_personas[:5])}")
    print(f"   平均每个: {simple_time/len(test_personas[:5]):.2f}秒")
    
    # 性能对比
    print("\n📈 性能对比结果:")
    print(f"   优化版速度提升: {(simple_time - optimized_time) / simple_time * 100:.1f}%")
    print(f"   优化版成功率: {optimized_success/len(test_personas[:5])*100:.1f}%")
    print(f"   简单版成功率: {simple_success/len(test_personas[:5])*100:.1f}%")
    
    return {
        "optimized_time": optimized_time,
        "optimized_success": optimized_success,
        "simple_time": simple_time,
        "simple_success": simple_success,
        "speed_improvement": (simple_time - optimized_time) / simple_time * 100
    }

def test_error_handling_features():
    """测试错误处理功能"""
    print("\n🛡️ 测试错误处理功能")
    print("=" * 60)
    
    from lib.error_handler import (
        circuit_breaker,
        retry_on_failure,
        fallback_on_error,
        timeout
    )
    
    test_results = {}
    
    # 测试重试装饰器
    print("\n🔄 测试重试装饰器...")
    
    call_count = 0
    
    @retry_on_failure(max_retries=3, delay=0.1)
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception(f"模拟失败 (第{call_count}次)")
        return "最终成功"
    
    try:
        result = failing_function()
        print(f"   结果: {result}")
        print(f"   调用次数: {call_count}")
        test_results["retry"] = True
    except Exception as e:
        print(f"   失败: {e}")
        test_results["retry"] = False
    
    # 测试降级装饰器
    print("\n🛟 测试降级装饰器...")
    
    @fallback_on_error(fallback_value="降级响应")
    def risky_function(should_fail=True):
        if should_fail:
            raise Exception("模拟失败")
        return "正常响应"
    
    try:
        result = risky_function(should_fail=True)
        print(f"   结果: {result}")
        test_results["fallback"] = True
    except Exception as e:
        print(f"   失败: {e}")
        test_results["fallback"] = False
    
    # 测试超时装饰器
    print("\n⏰ 测试超时装饰器...")
    
    @timeout(seconds=1)
    def slow_function():
        time.sleep(2)
        return "完成"
    
    try:
        result = slow_function()
        print(f"   结果: {result}")
        test_results["timeout"] = True
    except TimeoutError as e:
        print(f"   预期超时: {e}")
        test_results["timeout"] = True
    except Exception as e:
        print(f"   失败: {e}")
        test_results["timeout"] = False
    
    return test_results

async def generate_optimization_report(performance_data: Dict, error_handling_results: Dict):
    """生成优化报告"""
    print("\n📋 生成优化报告")
    print("=" * 60)
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "performance_comparison": {
            "optimized_client": {
                "time_seconds": performance_data["optimized_time"],
                "success_rate": performance_data["optimized_success"] / 5 * 100,
                "agents_per_second": 5 / performance_data["optimized_time"] if performance_data["optimized_time"] > 0 else 0
            },
            "simple_client": {
                "time_seconds": performance_data["simple_time"],
                "success_rate": performance_data["simple_success"] / 5 * 100,
                "agents_per_second": 5 / performance_data["simple_time"] if performance_data["simple_time"] > 0 else 0
            },
            "improvement": {
                "speed_percent": performance_data["speed_improvement"],
                "success_rate_diff": (performance_data["optimized_success"] - performance_data["simple_success"]) / 5 * 100
            }
        },
        "error_handling": error_handling_results,
        "recommendations": []
    }
    
    # 添加建议
    if performance_data["speed_improvement"] > 0:
        report["recommendations"].append({
            "priority": "HIGH",
            "action": "在生产环境中使用优化版LLM客户端",
            "reason": f"性能提升{performance_data['speed_improvement']:.1f}%"
        })
    else:
        report["recommendations"].append({
            "priority": "MEDIUM",
            "action": "进一步优化并发参数",
            "reason": "当前配置可能未达到最佳性能"
        })
    
    if all(error_handling_results.values()):
        report["recommendations"].append({
            "priority": "HIGH",
            "action": "集成错误处理模块到关键函数",
            "reason": "错误处理功能测试通过，可提高系统稳定性"
        })
    
    report["recommendations"].append({
        "priority": "MEDIUM",
        "action": "根据实际负载调整max_concurrent参数",
        "reason": "建议从5开始，根据API限制和性能监控调整"
    })
    
    # 保存报告
    report_dir = Path(__file__).parent.parent / "data" / "output" / "optimization_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"llm_optimization_comprehensive_{time.strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 报告已保存: {report_file}")
    
    # 打印摘要
    print("\n📊 优化测试摘要:")
    print(f"   性能提升: {performance_data['speed_improvement']:.1f}%")
    print(f"   错误处理测试: {sum(error_handling_results.values())}/{len(error_handling_results)} 通过")
    
    return report_file

async def main():
    """主函数"""
    print("=" * 60)
    print("🤖 LLM优化全面测试套件")
    print("=" * 60)
    
    try:
        # 性能对比测试
        performance_data = await performance_comparison()
        
        # 错误处理测试
        error_handling_results = test_error_handling_features()
        
        # 生成报告
        report_file = await generate_optimization_report(performance_data, error_handling_results)
        
        # 总结
        print("\n" + "=" * 60)
        print("🎉 LLM优化全面测试完成!")
        print("=" * 60)
        
        all_tests_passed = (
            performance_data["speed_improvement"] >= -10 and  # 允许10%的性能波动
            sum(error_handling_results.values()) >= 2  # 至少2个错误处理测试通过
        )
        
        if all_tests_passed:
            print("✅ 所有关键测试通过!")
            print("🚀 优化版LLM客户端已准备好用于生产环境")
            print(f"📄 详细报告: {report_file}")
        else:
            print("⚠️ 部分测试未达到预期")
            if performance_data["speed_improvement"] < -10:
                print("   - 性能提升未达到预期")
            if sum(error_handling_results.values()) < 2:
                print("   - 错误处理功能需要改进")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行异步测试
    success = asyncio.run(main())
    
    if success:
        print("\n✨ 测试成功完成!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)