"""
Layer 3: LLM Decision Engine — Persona-prompted reasoning for complex decisions.

Called only when:
1. Layer 1 (rules) has no deterministic answer
2. Layer 2 (probability) triggered an event that requires qualitative reasoning
3. Novel external event requires subjective response

Cost: $0.01-0.05 per call (DeepSeek/Claude API)
Expected: ~50-200 LLM calls per tick (out of 600-1400 active agents)

The LLM receives:
- Agent persona prompt (from Agent.to_persona_prompt())
- Current situation context
- Available action space (constrained by life phase ontology)
- Decision framework (expected to output structured JSON)

Mathematical aspects:
- Temperature sampling controls exploration vs exploitation
- Token budget constrains response length (cost control)
- Action space is enumerated, not free-form (prevents hallucination)
- Decision quality is logged for calibration feedback loop
"""

import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LLMDecisionEngine:
    """Layer 3: LLM-based decision engine for complex agent decisions."""

    def __init__(self, api_key: str = "", model: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com/v1",
                 temperature: float = 0.7, max_tokens: int = 300):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.total_calls = 0
        self.total_cost = 0.0

    def decide(self, persona_prompt: str, situation: str,
               action_space: List[str],
               constraints: Optional[List[str]] = None) -> dict:
        """
        Make a decision for an agent given a situation.

        Args:
            persona_prompt: agent's persona description
            situation: what happened / what decision is needed
            action_space: list of valid actions
            constraints: life phase constraints (blocked actions)

        Returns:
            {"action": str, "reasoning": str, "confidence": float,
             "emotion_delta": dict, "tokens_used": int, "cost_usd": float}
        """
        if not self.api_key:
            # Fallback: rule-based heuristic when LLM is unavailable
            return self._fallback_decision(action_space, persona_prompt, situation)

        # Build prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            persona_prompt, situation, action_space, constraints)

        # Call LLM API
        try:
            import requests

            response = requests.post(
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

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)

                # Estimate cost (DeepSeek pricing ~$0.001/1K tokens)
                cost = tokens * 0.001 / 1000

                self.total_calls += 1
                self.total_cost += cost

                # Parse structured response
                result = json.loads(content)
                result["tokens_used"] = tokens
                result["cost_usd"] = cost
                return result
            else:
                logger.warning(f"LLM API error {response.status_code}: {response.text}")
                return self._fallback_decision(action_space)

        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return self._fallback_decision(action_space)

    def _build_system_prompt(self) -> str:
        return """You are a behavioral analyst estimating what action a specific respondent would take given their situation. Estimate based on the respondent's demographic profile, personality, and circumstances.

CURRENT SINGAPORE CONTEXT (2026):
- Population: 6.11M (citizens 3.64M, PRs 0.56M, non-residents 1.91M)
- CPF wage ceiling: $8,000/month (raised from $6,800 in 2025)
- CPF rates (employee+employer): ≤55: 37%, 55-60: 34%, 60-65: 25%, 65-70: 17.5%, >70: 13%
- GST: 9% (since Jan 2024)
- Median monthly income (full-time employed residents): $5,775
- HDB classification: Standard/Plus/Prime (replaced mature/non-mature in 2024)
- Retirement age: 63, re-employment age: 68 (raised from 65/67 in Jul 2026)
- HDB resale levy abolished for Standard flats (2024)

Respond in JSON format:
{
    "action": "chosen_action",
    "reasoning": "brief 1-2 sentence explanation",
    "confidence": 0.0-1.0,
    "emotion_delta": {
        "happiness": -2 to +2,
        "anxiety": -2 to +2,
        "anger": -2 to +2
    }
}

Different respondent profiles should lead to different actions. Base your estimate on Singapore's social norms, economic constraints, and the respondent's personality traits, income level, and life phase."""

    def _build_user_prompt(self, persona: str, situation: str,
                           actions: List[str],
                           constraints: Optional[List[str]] = None) -> str:
        prompt = f"""RESPONDENT PROFILE:
{persona}

SITUATION:
{situation}

AVAILABLE ACTIONS:
{json.dumps(actions)}"""

        if constraints:
            prompt += f"""

CONSTRAINTS (you cannot do these):
{json.dumps(constraints)}"""

        return prompt

    def _fallback_decision(self, action_space: List[str],
                           persona: str = "", situation: str = "") -> dict:
        """
        Rule-based heuristic fallback when LLM is unavailable.
        Uses keyword matching on situation + persona to pick a plausible action.
        """
        import random

        sit_lower = situation.lower()
        persona_lower = persona.lower()

        # Extract rough income from persona
        income = 0
        if "income: $" in persona_lower:
            try:
                income = int(persona_lower.split("income: $")[1].split(".")[0].replace(",", ""))
            except (ValueError, IndexError):
                pass

        # Extract age from persona
        age = 30
        try:
            age = int(persona_lower.split("-year-old")[0].split()[-1])
        except (ValueError, IndexError):
            pass

        # Situation-based action scoring
        scores = {a: 0.0 for a in action_space}

        # --- Tax / cost of living events ---
        if any(kw in sit_lower for kw in ["gst", "tax", "cost of living", "cdc voucher"]):
            if income < 3000:
                scores["reduce_spending"] = scores.get("reduce_spending", 0) + 3.0
                scores["save_more"] = scores.get("save_more", 0) + 1.0
            elif income < 6000:
                scores["save_more"] = scores.get("save_more", 0) + 2.0
                scores["reduce_spending"] = scores.get("reduce_spending", 0) + 1.0
            else:
                scores["no_action"] = scores.get("no_action", 0) + 2.0
                scores["invest"] = scores.get("invest", 0) + 1.0

        # --- Housing / BTO events ---
        if any(kw in sit_lower for kw in ["bto", "hdb", "housing", "flat"]):
            if 25 <= age <= 35 and "single" in persona_lower:
                scores["apply_bto"] = scores.get("apply_bto", 0) + 3.0
            elif 25 <= age <= 40 and "married" in persona_lower:
                scores["apply_bto"] = scores.get("apply_bto", 0) + 2.0
                scores["upgrade_housing"] = scores.get("upgrade_housing", 0) + 1.5
            else:
                scores["no_action"] = scores.get("no_action", 0) + 1.0

        # --- Interest rate / mortgage events ---
        if any(kw in sit_lower for kw in ["interest rate", "mortgage", "sora", "absd"]):
            if "condo" in persona_lower or "landed" in persona_lower:
                scores["reduce_spending"] = scores.get("reduce_spending", 0) + 2.5
                scores["save_more"] = scores.get("save_more", 0) + 1.5
            else:
                scores["no_action"] = scores.get("no_action", 0) + 1.0

        # --- Employment / layoff events ---
        if any(kw in sit_lower for kw in ["layoff", "retrench", "job cut", "employment"]):
            scores["save_more"] = scores.get("save_more", 0) + 2.0
            scores["change_job"] = scores.get("change_job", 0) + 1.5
            scores["reduce_spending"] = scores.get("reduce_spending", 0) + 1.0

        # --- Transport / MRT events ---
        if any(kw in sit_lower for kw in ["mrt", "train", "bus", "transport", "erp"]):
            if "vehicle" in persona_lower or "car" in persona_lower:
                scores["reduce_spending"] = scores.get("reduce_spending", 0) + 1.5
            scores["no_action"] = scores.get("no_action", 0) + 1.0

        # --- Health / crisis events ---
        if any(kw in sit_lower for kw in ["covid", "lockdown", "circuit breaker", "pandemic"]):
            scores["reduce_spending"] = scores.get("reduce_spending", 0) + 3.0
            scores["save_more"] = scores.get("save_more", 0) + 2.0
            if income < 3000:
                scores["reduce_spending"] = scores.get("reduce_spending", 0) + 2.0
        if any(kw in sit_lower for kw in ["dengue", "health", "outbreak"]):
            scores["medical_checkup"] = scores.get("medical_checkup", 0) + 2.0
            if age > 60:
                scores["medical_checkup"] = scores.get("medical_checkup", 0) + 1.5

        # --- Retirement events ---
        if any(kw in sit_lower for kw in ["retirement", "cpf life", "re-employment"]):
            if age > 55:
                scores["plan_retirement"] = scores.get("plan_retirement", 0) + 2.5
                scores["part_time_work"] = scores.get("part_time_work", 0) + 1.5
            else:
                scores["save_more"] = scores.get("save_more", 0) + 1.0

        # --- CPF changes ---
        if any(kw in sit_lower for kw in ["cpf", "salary ceiling"]):
            scores["save_more"] = scores.get("save_more", 0) + 1.5
            if income > 6000:
                scores["invest"] = scores.get("invest", 0) + 1.0

        # --- Insurance ---
        if any(kw in sit_lower for kw in ["insurance", "medishield", "careshield"]):
            scores["buy_insurance"] = scores.get("buy_insurance", 0) + 2.0

        # --- Life events from probability layer ---
        if "life event: marital_transition" in sit_lower:
            scores["apply_bto"] = scores.get("apply_bto", 0) + 2.0
            scores["buy_insurance"] = scores.get("buy_insurance", 0) + 1.0
        if "life event: first_child" in sit_lower:
            scores["save_for_children"] = scores.get("save_for_children", 0) + 2.5
            scores["buy_insurance"] = scores.get("buy_insurance", 0) + 1.5
        if "life event: job_transition" in sit_lower:
            scores["save_more"] = scores.get("save_more", 0) + 2.0

        # Filter to only available actions and add small random noise
        available_scores = {
            a: scores.get(a, 0) + random.gauss(0, 0.3)
            for a in action_space
        }

        # If no clear signal, default to no_action
        max_score = max(available_scores.values())
        if max_score < 0.5:
            chosen = "no_action" if "no_action" in action_space else action_space[0]
        else:
            chosen = max(available_scores, key=available_scores.get)

        # Determine emotion based on event type
        emotion = {"happiness": 0, "anxiety": 0, "anger": 0}
        if any(kw in sit_lower for kw in ["covid", "lockdown", "layoff", "dengue"]):
            emotion = {"happiness": -1, "anxiety": 2, "anger": 0}
        elif any(kw in sit_lower for kw in ["gst", "tax", "interest rate"]):
            emotion = {"happiness": -1, "anxiety": 1, "anger": 1}
        elif any(kw in sit_lower for kw in ["bto", "voucher", "mrt"]):
            emotion = {"happiness": 1, "anxiety": 0, "anger": 0}

        return {
            "action": chosen,
            "reasoning": f"Heuristic fallback: {chosen} based on situation keywords",
            "confidence": min(0.7, max_score / 5.0) if max_score > 0 else 0.2,
            "emotion_delta": emotion,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }

    def get_stats(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_cost_per_call": round(
                self.total_cost / max(self.total_calls, 1), 4),
        }
