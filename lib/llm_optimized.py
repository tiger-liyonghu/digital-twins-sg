#!/usr/bin/env python3
"""
优化版LLM客户端 - 支持并发、限流、重试和错误处理

功能：
1. 并发调用DeepSeek API
2. 智能限流控制
3. 自动重试机制
4. 错误处理和降级
5. 性能监控

使用方法：
    from lib.llm_optimized import OptimizedLLMClient
    
    client = OptimizedLLMClient(max_concurrent=10)
    results = await client.batch_ask(agents_data, batch_size=50)
"""

import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from lib.config import DEEPSEEK_API_KEY

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class RateLimiter:
    """令牌桶限流器"""
    rate: float  # 每秒令牌数
    capacity: float  # 桶容量
    tokens: float = 0
    last_update: float = 0
    
    def __post_init__(self):
        self.tokens = self.capacity
        self.last_update = time.time()
    
    async def acquire(self, tokens: float = 1):
        """获取令牌"""
        now = time.time()
        elapsed = now - self.last_update
        
        # 添加新令牌
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        # 检查是否有足够令牌
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        # 需要等待
        wait_time = (tokens - self.tokens) / self.rate
        await asyncio.sleep(wait_time)
        
        # 更新令牌
        self.tokens = 0
        self.last_update = time.time() + wait_time
        return True

@dataclass
class CircuitBreaker:
    """断路器模式"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # 秒
    failures: int = 0
    last_failure_time: Optional[float] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """检查是否允许执行"""
        now = time.time()
        
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        return True
    
    def record_success(self):
        """记录成功"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
        self.failures = 0
    
    def record_failure(self):
        """记录失败"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"断路器打开，失败次数: {self.failures}")

class OptimizedLLMClient:
    """优化版LLM客户端"""
    
    def __init__(
        self,
        api_key: str = DEEPSEEK_API_KEY,
        base_url: str = "https://api.deepseek.com",
        max_concurrent: int = 10,
        rate_limit: float = 1.0,  # 每秒请求数
        timeout: float = 30.0,
        model: str = "deepseek-chat"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.model = model
        
        # 初始化组件
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(rate=rate_limit, capacity=rate_limit * 2)
        self.circuit_breaker = CircuitBreaker()
        
        # 性能统计
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_duration": 0.0
        }
        
        # 会话管理
        self._session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._session:
            await self._session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_deepseek_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """调用DeepSeek API（带重试）"""
        
        # 检查断路器
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN")
        
        # 等待限流器
        await self.rate_limiter.acquire()
        
        # 准备请求
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            async with self.semaphore:
                async with self._session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                ) as response:
                    
                    if response.status == 429:
                        # 速率限制，等待后重试
                        retry_after = response.headers.get("Retry-After", "1")
                        await asyncio.sleep(float(retry_after))
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=429,
                            message="Rate limited"
                        )
                    
                    response.raise_for_status()
                    result = await response.json()
                    
                    # 记录成功
                    self.circuit_breaker.record_success()
                    
                    # 更新统计
                    duration = time.time() - start_time
                    self._update_stats(result, duration, success=True)
                    
                    return result
                    
        except Exception as e:
            # 记录失败
            self.circuit_breaker.record_failure()
            self._update_stats(None, time.time() - start_time, success=False)
            logger.error(f"API调用失败: {str(e)}")
            raise
    
    def _update_stats(self, result: Optional[Dict], duration: float, success: bool):
        """更新性能统计"""
        self.stats["total_calls"] += 1
        self.stats["total_duration"] += duration
        
        if success and result:
            self.stats["successful_calls"] += 1
            
            # 计算token和成本
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens
            
            self.stats["total_tokens"] += total_tokens
            
            # DeepSeek定价: $0.001/1K tokens (输入+输出)
            cost = total_tokens / 1000 * 0.001
            self.stats["total_cost_usd"] += cost
        else:
            self.stats["failed_calls"] += 1
    
    async def ask_agent(
        self,
        persona: str,
        question: str,
        options: List[str],
        context: str = "",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """向单个Agent提问"""
        
        # 构建消息
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
        
        try:
            result = await self._call_deepseek_api(
                messages=messages,
                temperature=temperature,
                max_tokens=300
            )
            
            response_text = result["choices"][0]["message"]["content"]
            
            # 解析响应
            parsed = self._parse_response(response_text, options)
            parsed.update({
                "raw_response": response_text,
                "tokens_used": result["usage"]["total_tokens"],
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Agent提问失败: {str(e)}")
            
            # 降级处理：返回默认响应
            return {
                "choice": options[0] if options else "不确定",
                "reasoning": f"系统错误: {str(e)}",
                "willingness_score": 5,
                "error": str(e),
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_response(self, response_text: str, options: List[str]) -> Dict[str, Any]:
        """解析LLM响应"""
        
        # 初始化结果
        result = {
            "choice": "",
            "reasoning": "",
            "willingness_score": 5
        }
        
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 解析选择
                if line.startswith("选择:"):
                    choice_text = line[3:].strip()
                    
                    # 尝试提取选项编号
                    if choice_text.startswith("["):
                        # 格式: 选择: [1]
                        import re
                        match = re.search(r'\[(\d+)\]', choice_text)
                        if match:
                            idx = int(match.group(1)) - 1
                            if 0 <= idx < len(options):
                                result["choice"] = options[idx]
                    
                    # 直接匹配选项文本
                    if not result["choice"]:
                        for opt in options:
                            if opt in choice_text:
                                result["choice"] = opt
                                break
                    
                    # 如果还没找到，使用第一个选项
                    if not result["choice"] and options:
                        result["choice"] = options[0]
                
                # 解析理由
                elif line.startswith("理由:"):
                    result["reasoning"] = line[3:].strip()
                
                # 解析意愿度
                elif line.startswith("意愿度:"):
                    score_text = line[4:].strip()
                    try:
                        # 提取数字
                        import re
                        match = re.search(r'(\d+)', score_text)
                        if match:
                            score = int(match.group(1))
                            result["willingness_score"] = max(1, min(10, score))
                    except:
                        pass
            
            # 如果没有解析到选择，使用第一个选项
            if not result["choice"] and options:
                result["choice"] = options[0]
            
            return result
            
        except Exception as e:
            logger.warning(f"响应解析失败: {str(e)}，使用默认值")
            return {
                "choice": options[0] if options else "不确定",
                "reasoning": f"解析失败: {str(e)}",
                "willingness_score": 5,
                "parse_error": str(e)
            }
    
    async def batch_ask(
        self,
        agents_data: List[Dict[str, Any]],
        question: str,
        options: List[str],
        context: str = "",
        batch_size: int = 50,
        progress_callback = None
    ) -> List[Dict[str, Any]]:
        """批量向多个Agent提问"""
        
        if not self._session:
            async with self:
                return await self.batch_ask(
                    agents_data, question, options, context, batch_size, progress_callback
                )
        
        all_results = []
        total_agents = len(agents_data)
        
        logger.info(f"开始批量提问，共{total_agents}个Agent，批次大小{batch_size}")
        
        for i in range(0, total_agents, batch_size):
            batch = agents_data[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_agents + batch_size - 1) // batch_size
            
            logger.info(f"处理批次 {batch_num}/{total_batches} ({len(batch)}个Agent)")
            
            # 创建批次任务
            tasks = []
            for agent in batch:
                persona = agent.get("persona", "")
                if not persona and "agent_id" in agent:
                    # 可以在这里添加从数据库获取persona的逻辑
                    persona = f"Agent {agent['agent_id']}"
                
                task = self.ask_agent(persona, question, options, context)
                tasks.append(task)
            
            # 并发执行
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for j, result in enumerate(batch_results):
                    agent_idx = i + j
                    
                    if isinstance(result, Exception):
                        logger.error(f"Agent {agent_idx} 失败: {str(result)}")
                        all_results.append({
                            "agent_index": agent_idx,
                            "error": str(result),
                            "fallback": True,
                            "choice": options[0] if options else "不确定",
                            "willingness_score": 5
                        })
                    else:
                        result["agent_index"] = agent_idx
                        all_results.append(result)
                
                # 进度回调
                if progress_callback:
                    progress = min(100, int((i + len(batch)) / total_agents * 100))
                    progress_callback(progress, batch_num, total_batches)
                    
            except Exception as e:
                logger.error(f"批次 {batch_num} 失败: {str(e)}")
                # 为失败的批次添加占位结果
                for j in range(len(batch)):
                    all_results.append({
                        "agent_index": i + j,
                        "error": str(e),
                        "fallback": True,
                        "choice": options[0] if options else "不确定",
                        "willingness_score": 5
                    })
            
            # 批次间延迟，避免过热
            if i + batch_size < total_agents:
                await asyncio.sleep(0.5)
        
        logger.info(f"批量提问完成，成功{self.stats['successful_calls']}个，失败{self.stats['failed_calls']}个")
        
        return all_results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self.stats.copy()
        
        if stats["total_calls"] > 0:
            stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
            stats["avg_duration"] = stats["total_duration"] / stats["total_calls"]
            stats["avg_tokens_per_call"] = stats["total_tokens"] / stats["total_calls"]
        else:
            stats["success_rate"] = 0
            stats["avg_duration"] = 0
            stats["avg_tokens_per_call"] = 0
        
        return stats
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_duration": 0.0
        }

# 同步包装器（兼容现有代码）
class SyncLLMClient:
    """同步版LLM客户端（包装异步客户端）"""
    
    def __init__(self, **kwargs):
        self.async_client = OptimizedLLMClient(**kwargs)
        self._loop = None
    
    def _get_loop(self):
        """获取或创建事件循环"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            return self._loop
    
    def ask_agent(self, persona: str, question: str, options: List[str], context: str = "") -> Dict[str, Any]:
        """同步版提问"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.ask_agent(persona, question, options, context)
        )
    
    def batch_ask(self, agents_data: List[Dict], question: str, options: List[str], 
                  context: str = "", batch_size: int = 50) -> List[Dict[str, Any]]:
        """同步版批量提问"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.batch_ask(agents_data, question, options, context, batch_size)
        )
    
    def get_stats(self):
        """获取统计"""
        return self.async_client.get_stats()
    
    def reset_stats(self):
        """重置统计"""
        return self.async_client.reset_stats()

# 使用示例
async def example_async_usage():
    """异步使用示例"""
    async with OptimizedLLMClient(max_concurrent=10) as client:
        # 单个提问
        result = await client.ask_agent(
            persona="你是35岁的新加坡华人，月收入8000新元，住在HDB",
            question="你会支持GST增加到10%吗？",
            options=["支持", "反对", "中立"],
            context="GST将从9%增加到10%，2027年生效"
        )
        print(f"单个结果: {result}")
        
        # 批量提问
        agents_data = [
            {"persona": "Agent 1 persona", "agent_id": "A001"},
            {"persona": "Agent 2 persona", "agent_id": "A002"},
            # ... 更多agent
        ]
        
        def progress_callback(progress, batch_num, total_batches):
            print(f"进度: {progress}% (批次 {batch_num}/{total_batches})")
        
        results = await client.batch_ask(
            agents_data=agents_data,
            question="测试问题",
            options=["选项A", "选项B"],
            batch_size=20,
            progress_callback=progress_callback
        )
        
        print(f"批量结果: {len(results)} 个响应")
        print(f"统计: {client.get_stats()}")

def example_sync_usage():
    """同步使用示例"""
    client = SyncLLMClient(max_concurrent=5)
    
    # 单个提问
    result = client.ask_agent(
        persona="测试persona",
        question="测试问题",
        options=["选项1", "选项2"]
    )
    print(f"结果: {result}")
    
    # 批量提问
    agents_data = [{"persona": f"Agent {i}"} for i in range(10)]
    results = client.batch_ask(agents_data, "批量测试", ["A", "B"], batch_size=5)
    print(f"批量结果: {len(results)}")
    print(f"统计: {client.get_stats()}")

if __name__ == "__main__":
    # 运行同步示例
    print("同步示例:")
    example_sync_usage()
    
    # 运行异步示例
    print("\n异步示例:")
    import asyncio
    asyncio.run(example_async_usage())