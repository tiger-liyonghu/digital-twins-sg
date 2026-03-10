"""
LLM client with sync and async support, exponential backoff, cost tracking.
Supports multiple providers via OpenAI-compatible API format:
  - DeepSeek (default, cheapest)
  - SEA-LION (AISG, best Singapore/SEA context)

Async mode uses aiohttp for concurrent requests (20-50x speedup).
"""

import json
import time
import random
import logging
import asyncio
from typing import Optional

import requests
import aiohttp

logger = logging.getLogger(__name__)

# ── Provider presets (all OpenAI-compatible) ──────────────────────
LLM_PROVIDERS = {
    "deepseek": {
        "api_key": "sk-82775a6709e44d19b0ba428e2245bb3e",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "cost_per_1k": 0.0007,
        "concurrency": 30,
    },
    "sealion": {
        "api_key": "sk-9qbNDeW4YdBCrkHm-ihqag",
        "base_url": "https://api.sea-lion.ai/v1",
        "model": "aisingapore/Gemma-SEA-LION-v4-27B-IT",
        "cost_per_1k": 0.0,  # free trial tier
        "concurrency": 5,    # 10 req/min rate limit on free tier
    },
}

DEEPSEEK_API_KEY = LLM_PROVIDERS["deepseek"]["api_key"]
DEEPSEEK_BASE_URL = LLM_PROVIDERS["deepseek"]["base_url"]
DEFAULT_MODEL = LLM_PROVIDERS["deepseek"]["model"]


class LLMClient:
    def __init__(
        self,
        api_key: str = DEEPSEEK_API_KEY,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 300,
        concurrency: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.concurrency = concurrency
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_calls = 0

    def ask(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        """Sync single call (used for small jobs)."""
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=30,
                )

                if resp.status_code == 200:
                    return self._parse_response(resp.json())
                elif resp.status_code == 429:
                    wait = 2 ** attempt + random.uniform(0, 1)
                    logger.warning(f"Rate limited, waiting {wait:.1f}s")
                    time.sleep(wait)
                else:
                    logger.warning(f"LLM API error {resp.status_code}: {resp.text[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)

            except requests.Timeout:
                logger.warning(f"LLM timeout (attempt {attempt+1})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except json.JSONDecodeError:
                return self._fallback()
            except Exception as e:
                logger.warning(f"LLM call failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)

        return self._fallback()

    async def ask_async(
        self,
        session: aiohttp.ClientSession,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        """Async single call for use with batch_async."""
        for attempt in range(max_retries):
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_response(data)
                    elif resp.status == 429:
                        wait = 2 ** attempt + random.uniform(0, 1)
                        logger.warning(f"Rate limited, waiting {wait:.1f}s")
                        await asyncio.sleep(wait)
                    else:
                        text = await resp.text()
                        logger.warning(f"LLM API error {resp.status}: {text[:200]}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)

            except asyncio.TimeoutError:
                logger.warning(f"LLM async timeout (attempt {attempt+1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except json.JSONDecodeError:
                return self._fallback()
            except Exception as e:
                logger.warning(f"LLM async call failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

        return self._fallback()

    async def batch_async(
        self,
        prompts: list[tuple[str, str]],
        on_progress: callable = None,
    ) -> list[dict]:
        """
        Run multiple LLM calls concurrently with semaphore-limited parallelism.

        Args:
            prompts: list of (system_prompt, user_prompt) tuples
            on_progress: callback(completed_count, total) called after each completion

        Returns:
            list of result dicts in same order as prompts
        """
        sem = asyncio.Semaphore(self.concurrency)
        results = [None] * len(prompts)
        completed = 0

        async def _call(idx, sys_p, usr_p):
            nonlocal completed
            async with sem:
                result = await self.ask_async(session, sys_p, usr_p)
                results[idx] = result
                completed += 1
                if on_progress:
                    on_progress(completed, len(prompts))
                return result

        connector = aiohttp.TCPConnector(limit=self.concurrency + 10)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [_call(i, sp, up) for i, (sp, up) in enumerate(prompts)]
            await asyncio.gather(*tasks, return_exceptions=True)

        # Replace any exceptions with fallback
        for i, r in enumerate(results):
            if r is None or isinstance(r, Exception):
                results[i] = self._fallback()

        return results

    def _parse_response(self, data: dict) -> dict:
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        # Look up cost rate from provider presets, fallback to DeepSeek rate
        cost_rate = 0.0007
        for p in LLM_PROVIDERS.values():
            if p["base_url"] in self.base_url:
                cost_rate = p["cost_per_1k"]
                break
        cost = tokens * cost_rate / 1000

        self.total_tokens += tokens
        self.total_cost += cost
        self.total_calls += 1

        result = json.loads(content)
        result["tokens_used"] = tokens
        result["cost_usd"] = round(cost, 6)
        result["model"] = self.model
        return result

    @classmethod
    def from_provider(cls, provider: str = "deepseek", **overrides) -> "LLMClient":
        """Create a client from a provider preset.

        Args:
            provider: one of "deepseek", "sealion"
            **overrides: any LLMClient __init__ kwargs to override

        Usage:
            client = LLMClient.from_provider("sealion", api_key="your-key")
        """
        import os
        preset = LLM_PROVIDERS.get(provider)
        if not preset:
            raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(LLM_PROVIDERS.keys())}")

        kwargs = {
            "api_key": preset["api_key"],
            "base_url": preset["base_url"],
            "model": preset["model"],
            "concurrency": preset["concurrency"],
        }

        # Allow env var override for API keys
        env_key = os.environ.get(f"{provider.upper()}_API_KEY")
        if env_key:
            kwargs["api_key"] = env_key

        kwargs.update(overrides)
        return cls(**kwargs)

    def _fallback(self) -> dict:
        return {
            "choice": "SKIPPED",
            "reasoning": "LLM unavailable",
            "confidence": 0.0,
            "tokens_used": 0,
            "cost_usd": 0.0,
            "model": "fallback",
        }
