"""
API Server — Digital Twin Singapore
Serves the frontend and handles client survey submissions.

Usage:
    python3 scripts/api_server.py
    # Then open http://localhost:3456
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import threading
import concurrent.futures
import logging
import requests
import numpy as np
import pandas as pd
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# CONCURRENCY CONTROLS
# ============================================================
# Global semaphore: max 30 parallel LLM calls across ALL jobs
# (DeepSeek rate limit ~60 RPM, leave headroom)
_llm_semaphore = threading.Semaphore(30)

# Thread-safe lock for jobs dict
_jobs_lock = threading.Lock()

# ============================================================
# CONFIG — loaded from .env via lib.config
# ============================================================
from lib.config import (
    SUPABASE_URL, SUPABASE_KEY, DEEPSEEK_API_KEY, DEEPSEEK_URL,
    NVIDIA_API_KEY, NVIDIA_REWARD_URL, NVIDIA_REWARD_MODEL,
)

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store (protected by _jobs_lock)
jobs = {}  # job_id -> { status, progress, total, result, error, created_at }
MAX_CONCURRENT_JOBS = 5  # max simultaneous running jobs
MAX_JOBS_HISTORY = 50    # keep last N completed jobs

# Cache agents
_agents_cache = None


# ============================================================
# AGENT LOADING
# ============================================================
def load_all_agents() -> pd.DataFrame:
    global _agents_cache
    if _agents_cache is not None:
        return _agents_cache

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    all_agents = []
    offset = 0
    page_size = 1000
    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents",
            headers={**headers, "Range": f"{offset}-{offset + page_size - 1}"},
            params={"select": "*"},
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        all_agents.extend(data)
        if len(data) < page_size:
            break
        offset += page_size

    _agents_cache = pd.DataFrame(all_agents)
    logger.info(f"Cached {len(_agents_cache)} agents")
    return _agents_cache


def stratified_sample(df: pd.DataFrame, n: int, seed: int,
                      age_min=None, age_max=None, gender=None,
                      housing=None, income_min=None, income_max=None,
                      marital=None, education=None, life_phase=None,
                      has_income=None) -> tuple:
    """Stratified sample with optional filters. Returns (sample_df, eligible_count, total)."""
    total = len(df)
    mask = pd.Series(True, index=df.index)
    if age_min is not None:
        mask &= df["age"] >= int(age_min)
    if age_max is not None:
        mask &= df["age"] <= int(age_max)
    if gender and gender != "all":
        mask &= df["gender"] == gender
    if housing and housing != "all":
        mask &= df["housing_type"] == housing
    if income_min is not None:
        mask &= df["monthly_income"] >= float(income_min)
    if income_max is not None:
        mask &= df["monthly_income"] <= float(income_max)
    if marital and marital != "all":
        mask &= df["marital_status"] == marital
    if education and education != "all":
        mask &= df["education_level"] == education
    if life_phase and life_phase != "all":
        mask &= df["life_phase"] == life_phase
    if has_income:
        mask &= df["monthly_income"] > 0

    filtered = df[mask]
    eligible_count = len(filtered)
    if eligible_count == 0:
        return filtered, 0, total

    actual_n = min(n, eligible_count)
    rng = np.random.default_rng(seed)

    # Stratify by age group × gender
    age_bins = [(0, 17), (18, 34), (35, 54), (55, 74), (75, 100)]
    indices = []
    for lo, hi in age_bins:
        for g in ["M", "F"]:
            sub = filtered[(filtered["age"] >= lo) & (filtered["age"] <= hi) & (filtered["gender"] == g)]
            if len(sub) == 0:
                continue
            target_n = max(1, int(round(len(sub) / len(filtered) * actual_n)))
            chosen = rng.choice(sub.index, size=min(target_n, len(sub)), replace=False)
            indices.extend(chosen.tolist())

    rng.shuffle(indices)
    if len(indices) > actual_n:
        indices = indices[:actual_n]
    elif len(indices) < actual_n:
        remaining = [i for i in filtered.index if i not in indices]
        if remaining:
            extra = rng.choice(remaining, size=min(actual_n - len(indices), len(remaining)), replace=False)
            indices.extend(extra.tolist())

    return df.loc[indices].reset_index(drop=True), eligible_count, total


# ============================================================
# LLM SURVEY — delegated to lib.persona + lib.llm
# ============================================================
from lib.persona import agent_to_persona
from lib.llm import ask_agent as _ask_agent_core


def ask_agent(persona, question, options, context=""):
    """Wrapper adding API-server-specific fields (tokens, cost, willingness).
    Uses global semaphore to limit total concurrent LLM calls."""
    _llm_semaphore.acquire()
    try:
        result = _ask_agent_core(persona, question, options, context)
    finally:
        _llm_semaphore.release()
    probs = result.get("probabilities", {})
    chosen = result.get("choice", "")
    result.setdefault("tokens_used", 0)
    result.setdefault("cost_usd", 0)
    result.setdefault("willingness_score", int(probs.get(chosen, 0.5) * 10) if probs else 5)
    result.setdefault("key_concern", "VS")
    return result


def score_response_quality(user_prompt: str, assistant_response: str) -> float:
    """
    Score response quality using NVIDIA Llama-3.1-Nemotron-70B-Reward.

    Returns a single reward score (float, typically -30 to 0, higher = better).
    Empirical thresholds from testing:
      > -5   : high quality — thoughtful, persona-consistent, specific reasoning
      -5~-15 : acceptable — correct but generic
      < -15  : low quality — lazy, contradictory, or off-topic

    On failure returns None (does not block the survey pipeline).
    """
    try:
        resp = requests.post(NVIDIA_REWARD_URL, headers={
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json",
        }, json={
            "model": NVIDIA_REWARD_MODEL,
            "messages": [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response},
            ],
        }, timeout=15)

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            # Format: "reward:-2.609375"
            score = float(content.split(":")[-1])
            return score
    except Exception as e:
        logger.warning(f"Reward model error: {e}")

    return None


def _compute_quality_summary(responses: list) -> dict:
    """Compute quality summary from Nemotron reward scores."""
    reward_scores = [r.get("reward_score") for r in responses if r.get("reward_score") is not None]
    if not reward_scores:
        return {"available": False}

    scores = np.array(reward_scores)
    # Thresholds from empirical testing:
    #   > -5   : high quality (thoughtful, persona-consistent)
    #   -5~-15 : acceptable (correct but generic)
    #   < -15  : low quality (lazy, contradictory)
    high = int((scores > -5).sum())
    acceptable = int(((scores >= -15) & (scores <= -5)).sum())
    low = int((scores < -15).sum())
    total = len(scores)

    return {
        "available": True,
        "model": "nvidia/llama-3.1-nemotron-70b-reward",
        "n_scored": total,
        "mean_reward": round(float(scores.mean()), 2),
        "median_reward": round(float(np.median(scores)), 2),
        "min_reward": round(float(scores.min()), 2),
        "max_reward": round(float(scores.max()), 2),
        "high_quality": high,
        "high_quality_pct": round(high / total * 100, 1),
        "acceptable": acceptable,
        "acceptable_pct": round(acceptable / total * 100, 1),
        "low_quality": low,
        "low_quality_pct": round(low / total * 100, 1),
    }


def run_survey_job(job_id: str, params: dict):
    """Run survey in background thread."""
    try:
        jobs[job_id]["status"] = "sampling"
        df = load_all_agents()
        seed = hash(job_id) % (2**31)
        sample, eligible_count, total_pop = stratified_sample(
            df, n=params["sample_size"], seed=seed,
            age_min=params.get("age_min"), age_max=params.get("age_max"),
            gender=params.get("gender"), housing=params.get("housing"),
            income_min=params.get("income_min"), income_max=params.get("income_max"),
            marital=params.get("marital"), education=params.get("education"),
            life_phase=params.get("life_phase"), has_income=params.get("has_income"),
        )
        jobs[job_id]["eligible_count"] = eligible_count
        jobs[job_id]["total_population"] = total_pop

        if len(sample) == 0:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "No agents match filters"
            return

        actual_n = len(sample)
        jobs[job_id]["total"] = actual_n
        jobs[job_id]["status"] = "running"

        # Build work items: (index, agent_dict, persona_str)
        work_items = []
        for i in range(actual_n):
            agent = sample.iloc[i].to_dict()
            persona = agent_to_persona(agent)
            work_items.append((i, agent, persona))

        responses = [None] * actual_n
        completed = [0]  # mutable for closure

        def _process_agent(item):
            idx, agent, persona = item
            result = ask_agent(persona, params["question"], params["options"], params.get("context", ""))
            result["agent_age"] = agent["age"]
            result["agent_gender"] = agent["gender"]
            result["agent_ethnicity"] = agent.get("ethnicity", "")
            result["agent_income"] = agent.get("monthly_income", 0)
            result["agent_housing"] = agent.get("housing_type", "")

            # Reward model quality scoring (non-blocking)
            user_prompt = f"PERSONA:\n{persona}\n\nQUESTION:\n{params['question']}\n\nOPTIONS:\n{json.dumps(params['options'])}\n\nAnswer as this person."
            assistant_text = json.dumps({
                "choice": result.get("choice", ""),
                "reasoning": result.get("reasoning", ""),
                "willingness_score": result.get("willingness_score", 5),
            }, ensure_ascii=False)
            reward = score_response_quality(user_prompt, assistant_text)
            result["reward_score"] = reward
            return idx, result

        CONCURRENCY = 20  # parallel LLM calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = {executor.submit(_process_agent, item): item for item in work_items}
            for future in concurrent.futures.as_completed(futures):
                idx, result = future.result()
                responses[idx] = result
                completed[0] += 1
                jobs[job_id]["progress"] = completed[0]

        # Analyze
        positive_options = params["options"][:2]
        choices = [r["choice"] for r in responses]
        choice_counts = Counter(choices)
        scores = [r.get("willingness_score", 5) for r in responses]
        positive_count = sum(1 for c in choices if c in positive_options)

        # Breakdowns
        age_groups = {"18-29": (18, 29), "30-44": (30, 44), "45-59": (45, 59), "60+": (60, 100)}
        by_age = {}
        for label, (lo, hi) in age_groups.items():
            group = [r for r in responses if lo <= r["agent_age"] <= hi]
            if not group:
                continue
            gp = sum(1 for r in group if r["choice"] in positive_options)
            by_age[label] = {
                "n": len(group),
                "positive_rate": round(gp / len(group), 2),
                "avg_willingness": round(np.mean([r.get("willingness_score", 5) for r in group]), 1),
            }

        income_groups = {"<$3K": (0, 2999), "$3K-$7K": (3000, 6999), "$7K-$15K": (7000, 14999), "$15K+": (15000, 999999)}
        by_income = {}
        for label, (lo, hi) in income_groups.items():
            group = [r for r in responses if lo <= r["agent_income"] <= hi]
            if not group:
                continue
            gp = sum(1 for r in group if r["choice"] in positive_options)
            by_income[label] = {"n": len(group), "positive_rate": round(gp / len(group), 2)}

        total_tokens = sum(r.get("tokens_used", 0) for r in responses)
        total_cost = sum(r.get("cost_usd", 0) for r in responses)

        report = {
            "client_name": params["client_name"],
            "question": params["question"],
            "options": params["options"],
            "total_population": total_pop,
            "eligible_count": eligible_count,
            "n_respondents": actual_n,
            "timestamp": str(datetime.now()),
            "overall": {
                "choice_distribution": dict(choice_counts),
                "avg_willingness": round(float(np.mean(scores)), 1),
                "positive_rate": round(positive_count / actual_n, 2),
            },
            "breakdowns": {"by_age": by_age, "by_income": by_income},
            "concerns": [r.get("key_concern", "") for r in responses[:10]],
            "reasoning_samples": [r.get("reasoning", "") for r in responses[:5]],
            "agent_log": [
                {
                    "age": r["agent_age"], "gender": r["agent_gender"],
                    "ethnicity": r["agent_ethnicity"],
                    "income": r["agent_income"], "housing": r["agent_housing"],
                    "choice": r["choice"],
                    "willingness": r.get("willingness_score", 5),
                    "concern": r.get("key_concern", ""),
                    "reward": r.get("reward_score"),
                }
                for r in responses
            ],
            "quality": _compute_quality_summary(responses),
            "cost": {
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "cost_per_agent": round(total_cost / max(actual_n, 1), 4),
            },
        }

        # Save to file
        fname = f"survey_{job_id}.json"
        with open(OUTPUT_DIR / fname, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = report

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ============================================================
# A/B TEST JOB
# ============================================================
def run_abtest_job(job_id: str, params: dict):
    """Run A/B test: same population, two scenarios, compare results."""
    try:
        jobs[job_id]["status"] = "sampling"
        df = load_all_agents()
        sample, eligible_count, total_pop = stratified_sample(
            df, n=params["sample_size"], seed=42,
            age_min=params.get("age_min"), age_max=params.get("age_max"),
            gender=params.get("gender"), has_income=params.get("has_income"),
        )
        jobs[job_id]["eligible_count"] = eligible_count
        jobs[job_id]["total_population"] = total_pop

        if len(sample) == 0:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "No agents match filters"
            return

        actual_n = len(sample)
        jobs[job_id]["total"] = actual_n * 2  # two scenarios
        jobs[job_id]["status"] = "running"

        results_a = []
        results_b = []

        for i in range(actual_n):
            agent = sample.iloc[i].to_dict()
            persona = agent_to_persona(agent)

            # Scenario A
            ra = ask_agent(persona, params["question"], params["options"], params["context_a"])
            ra["agent_age"] = agent["age"]
            ra["agent_gender"] = agent["gender"]
            ra["agent_income"] = agent.get("monthly_income", 0)
            results_a.append(ra)
            jobs[job_id]["progress"] = i * 2 + 1

            # Scenario B
            rb = ask_agent(persona, params["question"], params["options"], params["context_b"])
            rb["agent_age"] = agent["age"]
            rb["agent_gender"] = agent["gender"]
            rb["agent_income"] = agent.get("monthly_income", 0)
            results_b.append(rb)
            jobs[job_id]["progress"] = i * 2 + 2

            time.sleep(0.1)

        def analyze_arm(responses, options):
            choices = [r["choice"] for r in responses]
            counts = Counter(choices)
            scores = [r.get("willingness_score", 5) for r in responses]
            positive_options = options[:2]
            pos_count = sum(1 for c in choices if c in positive_options)
            n = len(responses)
            return {
                "n": n,
                "choice_distribution": dict(counts),
                "positive_rate": round(pos_count / n, 4) if n > 0 else 0,
                "avg_willingness": round(float(np.mean(scores)), 2),
            }

        arm_a = analyze_arm(results_a, params["options"])
        arm_b = analyze_arm(results_b, params["options"])

        # Two-proportion z-test
        pa = arm_a["positive_rate"]
        pb = arm_b["positive_rate"]
        na = arm_a["n"]
        nb = arm_b["n"]
        p_pool = (pa * na + pb * nb) / (na + nb) if (na + nb) > 0 else 0
        se = np.sqrt(p_pool * (1 - p_pool) * (1/na + 1/nb)) if p_pool > 0 and p_pool < 1 else 0.001
        z_stat = (pa - pb) / se if se > 0 else 0
        # Two-tailed p-value
        from scipy.stats import norm
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))

        report = {
            "question": params["question"],
            "options": params["options"],
            "scenario_a": {"label": params["label_a"], "context": params["context_a"], **arm_a},
            "scenario_b": {"label": params["label_b"], "context": params["context_b"], **arm_b},
            "significance_test": {
                "test": "two-proportion z-test",
                "z_statistic": round(float(z_stat), 4),
                "p_value": round(float(p_value), 6),
                "significant": bool(p_value < 0.05),
                "effect_size_pp": round((pa - pb) * 100, 2),
            },
            "total_population": total_pop,
            "eligible_count": eligible_count,
            "n_per_arm": actual_n,
            "timestamp": str(datetime.now()),
        }

        fname = f"abtest_{job_id}.json"
        with open(OUTPUT_DIR / fname, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = report

    except Exception as e:
        logger.exception(f"A/B test job {job_id} failed")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ============================================================
# CONJOINT ANALYSIS JOB
# ============================================================
def run_conjoint_job(job_id: str, params: dict):
    """Run conjoint analysis: present attribute profiles, measure preferences."""
    try:
        jobs[job_id]["status"] = "sampling"
        df = load_all_agents()
        sample, eligible_count, total_pop = stratified_sample(
            df, n=params["sample_size"], seed=42,
            age_min=params.get("age_min"), age_max=params.get("age_max"),
            gender=params.get("gender"), has_income=params.get("has_income"),
        )
        jobs[job_id]["eligible_count"] = eligible_count
        jobs[job_id]["total_population"] = total_pop

        if len(sample) == 0:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "No agents match filters"
            return

        profiles = params["profiles"]  # list of {name, attributes: {attr: value}}
        actual_n = len(sample)
        n_profiles = len(profiles)
        jobs[job_id]["total"] = actual_n * n_profiles
        jobs[job_id]["status"] = "running"

        # For each agent, ask them to rank/choose among profiles
        question = params["question"]
        profile_names = [p["name"] for p in profiles]
        # Build profile descriptions
        profile_descs = []
        for p in profiles:
            desc_parts = [f"{k}: {v}" for k, v in p["attributes"].items()]
            profile_descs.append(f"{p['name']} — " + ", ".join(desc_parts))

        options = profile_names + [params.get("none_option", "None of these")]
        context = params.get("context", "") + "\n\nProduct profiles:\n" + "\n".join(profile_descs)

        responses = []
        for i in range(actual_n):
            agent = sample.iloc[i].to_dict()
            persona = agent_to_persona(agent)
            result = ask_agent(persona, question, options, context)
            result["agent_age"] = agent["age"]
            result["agent_gender"] = agent["gender"]
            result["agent_income"] = agent.get("monthly_income", 0)
            result["agent_housing"] = agent.get("housing_type", "")
            responses.append(result)
            jobs[job_id]["progress"] = i + 1
            time.sleep(0.15)

        # Analyze profile preferences
        choices = [r["choice"] for r in responses]
        counts = Counter(choices)
        scores = {}
        for pname in profile_names:
            choosers = [r for r in responses if r["choice"] == pname]
            scores[pname] = {
                "count": len(choosers),
                "share": round(len(choosers) / actual_n * 100, 1),
                "avg_willingness": round(np.mean([r.get("willingness_score", 5) for r in choosers]), 1) if choosers else 0,
            }

        # Breakdowns by income
        inc_groups = {"<$3K": (0, 2999), "$3K-$7K": (3000, 6999), "$7K+": (7000, 999999)}
        by_income = {}
        for label, (lo, hi) in inc_groups.items():
            group = [r for r in responses if lo <= r["agent_income"] <= hi]
            if not group:
                continue
            gc = Counter(r["choice"] for r in group)
            by_income[label] = {pn: round(gc.get(pn, 0) / len(group) * 100, 1) for pn in profile_names}
            by_income[label]["n"] = len(group)

        # Breakdowns by age
        age_groups = {"18-29": (18, 29), "30-44": (30, 44), "45-59": (45, 59), "60+": (60, 100)}
        by_age = {}
        for label, (lo, hi) in age_groups.items():
            group = [r for r in responses if lo <= r["agent_age"] <= hi]
            if not group:
                continue
            gc = Counter(r["choice"] for r in group)
            by_age[label] = {pn: round(gc.get(pn, 0) / len(group) * 100, 1) for pn in profile_names}
            by_age[label]["n"] = len(group)

        report = {
            "question": question,
            "profiles": profiles,
            "profile_scores": scores,
            "choice_distribution": dict(counts),
            "breakdowns": {"by_income": by_income, "by_age": by_age},
            "reasoning_samples": [{"choice": r["choice"], "reasoning": r.get("reasoning", "")} for r in responses[:8]],
            "total_population": total_pop,
            "eligible_count": eligible_count,
            "n_respondents": actual_n,
            "timestamp": str(datetime.now()),
        }

        fname = f"conjoint_{job_id}.json"
        with open(OUTPUT_DIR / fname, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = report

    except Exception as e:
        logger.exception(f"Conjoint job {job_id} failed")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ============================================================
# SOCIAL SIMULATION JOB (7-Day 3-Round ABM)
# ============================================================
def _assign_cluster(agent):
    """Housing × age → demographic cluster ID."""
    age = agent.get("age", 30)
    housing = str(agent.get("housing_type", "HDB 4-room"))
    if age < 35:
        age_tier = "young"
    elif age < 55:
        age_tier = "mid"
    else:
        age_tier = "senior"
    h = housing.lower()
    if any(x in h for x in ["condo", "private", "landed", "semi-d", "bungalow", "terrace"]):
        housing_tier = "private"
    elif "5" in h or "executive" in h:
        housing_tier = "hdb_large"
    elif "4" in h:
        housing_tier = "hdb_mid"
    else:
        housing_tier = "hdb_small"
    return f"{housing_tier}_{age_tier}"


def _choice_to_score(choice, options):
    """Map option text to opinion score: +2 to -2 (first=most positive)."""
    n = len(options)
    for i, opt in enumerate(options):
        if choice == opt:
            if n <= 3:
                return [1, 0, -1][min(i, 2)]
            elif n <= 5:
                return [2, 1, 0, -1, -2][min(i, 4)]
            else:
                # Scale linearly
                return round(2 - (4 * i / (n - 1)))
    return 0


def _compute_cluster_stats(agents, score_key):
    """Compute opinion stats per cluster."""
    from collections import defaultdict
    clusters = defaultdict(list)
    for a in agents:
        clusters[a["cluster"]].append(a[score_key])
    stats = {}
    for c, scores in clusters.items():
        n = len(scores)
        support = sum(1 for s in scores if s > 0)
        oppose = sum(1 for s in scores if s < 0)
        neutral = sum(1 for s in scores if s == 0)
        avg = sum(scores) / n
        stats[c] = {
            "n": n, "avg": round(avg, 2),
            "support_pct": round(support / n * 100),
            "oppose_pct": round(oppose / n * 100),
            "neutral_pct": round(neutral / n * 100),
            "majority": "support" if support > oppose else "oppose" if oppose > support else "mixed",
        }
    return stats


PEER_QUOTES_GENERIC = {
    "support": [
        "I think this is the right direction. We need to adapt to changing times.",
        "The data supports this. It makes sense long-term.",
        "Other countries have done this successfully. We should too.",
    ],
    "oppose": [
        "They keep changing the rules. When does it end?",
        "Not everyone is in the same situation. One size doesn't fit all.",
        "This will hurt the people who can least afford it.",
    ],
    "mixed": [
        "I can see both sides, but the implementation needs to be fair.",
        "Maybe a compromise would work better.",
        "I'm okay with it IF they address the concerns of vulnerable groups.",
    ],
}


def _build_social_context(cluster_stats, cluster_id, day, peer_quotes=None):
    """Build per-agent social context string for Day 3, Day 5, or Day 7."""
    import random
    quotes = peer_quotes or PEER_QUOTES_GENERIC
    s = cluster_stats[cluster_id]
    rng = random.Random(hash(cluster_id) + day)

    if day == 3:
        majority = s["majority"]
        return (
            f"\n\nSOCIAL CONTEXT (Day 3 — early discussions are starting):\n"
            f"You've started to hear others talk about this. In your community, "
            f"about {s['support_pct']}% support and {s['oppose_pct']}% oppose.\n"
            f"A friend casually mentioned their view."
        )
    elif day == 5:
        majority = s["majority"]
        quote = rng.choice(quotes.get(majority, quotes["mixed"]))
        peer_type = rng.choice(["neighbour", "colleague", "relative", "old classmate"])
        return (
            f"\n\nSOCIAL CONTEXT (Day 5 — discussions are intensifying):\n"
            f"In your social circle, about {s['support_pct']}% support, "
            f"{s['oppose_pct']}% oppose, and {s['neutral_pct']}% are undecided.\n"
            f"A {peer_type} you often talk to said: \"{quote}\"\n"
            f"Several WhatsApp groups and coffee shop conversations have been about this topic."
        )
    elif day == 7:
        majority = s["majority"]
        q1 = rng.choice(quotes.get(majority, quotes["mixed"]))
        if s["support_pct"] > 70:
            echo = "Almost everyone you know supports this change."
            counter = ""
        elif s["oppose_pct"] > 70:
            echo = "Almost everyone you know is against this change."
            counter = ""
        else:
            echo = f"Opinions are divided — about {s['support_pct']}% support, {s['oppose_pct']}% oppose."
            minority = "support" if s["majority"] == "oppose" else "oppose"
            counter_quote = rng.choice(quotes.get(minority, quotes["mixed"]))
            counter = f'\nBut you also heard someone say: "{counter_quote}"'
        return (
            f"\n\nSOCIAL CONTEXT (Day 7 — after a full week of public debate):\n"
            f"{echo}\n"
            f"The dominant view around you: \"{q1}\"{counter}\n"
            f"Social media has been intense. Government held a press conference.\n"
            f"Some people have changed their minds. Others feel even more strongly.\n"
            f"What is this respondent's position NOW, after a week of discussion and social pressure?"
        )
    return ""


def run_simulation_job(job_id: str, params: dict):
    """Run 7-day 4-round social simulation."""
    try:
        jobs[job_id]["status"] = "sampling"
        df = load_all_agents()
        sample, eligible_count, total_pop = stratified_sample(
            df, n=params["sample_size"], seed=42,
            age_min=params.get("age_min"), age_max=params.get("age_max"),
            gender=params.get("gender"), housing=params.get("housing"),
        )
        jobs[job_id]["eligible_count"] = eligible_count
        jobs[job_id]["total_population"] = total_pop

        if len(sample) == 0:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "No agents match filters"
            return

        actual_n = len(sample)
        total_calls = actual_n * 4  # 4 rounds
        jobs[job_id]["total"] = total_calls
        jobs[job_id]["status"] = "running"

        question = params["question"]
        options = params["options"]
        context = params.get("context", "")
        peer_quotes = params.get("peer_quotes") or PEER_QUOTES_GENERIC

        # Build agent list with clusters
        agents = []
        for i in range(actual_n):
            a = sample.iloc[i].to_dict()
            a["cluster"] = _assign_cluster(a)
            a["persona_base"] = agent_to_persona(a)
            agents.append(a)

        completed = [0]

        def _run_round(batch_items, round_label):
            """Run one round of LLM calls with concurrency."""
            results = [None] * len(batch_items)
            CONCURRENCY = 20

            def _call(item):
                idx, persona, q, opts, ctx = item
                result = ask_agent(persona, q, opts, ctx)
                return idx, result

            with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
                futures = {executor.submit(_call, item): item for item in batch_items}
                for future in concurrent.futures.as_completed(futures):
                    idx, result = future.result()
                    results[idx] = result
                    completed[0] += 1
                    jobs[job_id]["progress"] = completed[0]
                    # Update current round info
                    jobs[job_id]["current_round"] = round_label

            return results

        # ═══ ROUND 1 — Day 1: Cold Reaction ═══
        jobs[job_id]["current_round"] = "day1"
        batch_r1 = [(i, agents[i]["persona_base"], question, options, context) for i in range(actual_n)]
        results_r1 = _run_round(batch_r1, "day1")

        for i, r in enumerate(results_r1):
            if r is None:
                r = {"choice": options[len(options) // 2], "reasoning": "error"}
            agents[i]["day1_choice"] = r.get("choice", options[len(options) // 2])
            agents[i]["day1_score"] = _choice_to_score(agents[i]["day1_choice"], options)
            agents[i]["day1_reasoning"] = r.get("reasoning", "")

        cluster_stats_d1 = _compute_cluster_stats(agents, "day1_score")

        # Save interim Day 1 results
        day1_dist = Counter(a["day1_choice"] for a in agents)
        jobs[job_id]["rounds_done"] = 1
        jobs[job_id]["interim_results"] = {
            "day1": {"distribution": dict(day1_dist), "cluster_stats": cluster_stats_d1}
        }

        # ═══ ROUND 2 — Day 3: Early Discussion ═══
        jobs[job_id]["current_round"] = "day3"
        batch_r2 = []
        for i, a in enumerate(agents):
            social_ctx = _build_social_context(cluster_stats_d1, a["cluster"], day=3, peer_quotes=peer_quotes)
            persona_r2 = a["persona_base"] + social_ctx
            batch_r2.append((i, persona_r2, question, options, context))

        results_r2 = _run_round(batch_r2, "day3")

        for i, r in enumerate(results_r2):
            if r is None:
                r = {"choice": options[len(options) // 2], "reasoning": "error"}
            agents[i]["day3_choice"] = r.get("choice", options[len(options) // 2])
            agents[i]["day3_score"] = _choice_to_score(agents[i]["day3_choice"], options)
            agents[i]["day3_reasoning"] = r.get("reasoning", "")

        cluster_stats_d3 = _compute_cluster_stats(agents, "day3_score")

        day3_dist = Counter(a["day3_choice"] for a in agents)
        jobs[job_id]["rounds_done"] = 2
        jobs[job_id]["interim_results"]["day3"] = {"distribution": dict(day3_dist), "cluster_stats": cluster_stats_d3}

        # ═══ ROUND 3 — Day 5: Peer Influence ═══
        jobs[job_id]["current_round"] = "day5"
        batch_r3 = []
        for i, a in enumerate(agents):
            social_ctx = _build_social_context(cluster_stats_d3, a["cluster"], day=5, peer_quotes=peer_quotes)
            persona_r3 = a["persona_base"] + social_ctx
            batch_r3.append((i, persona_r3, question, options, context))

        results_r3 = _run_round(batch_r3, "day5")

        for i, r in enumerate(results_r3):
            if r is None:
                r = {"choice": options[len(options) // 2], "reasoning": "error"}
            agents[i]["day5_choice"] = r.get("choice", options[len(options) // 2])
            agents[i]["day5_score"] = _choice_to_score(agents[i]["day5_choice"], options)
            agents[i]["day5_reasoning"] = r.get("reasoning", "")

        cluster_stats_d5 = _compute_cluster_stats(agents, "day5_score")

        day5_dist = Counter(a["day5_choice"] for a in agents)
        jobs[job_id]["rounds_done"] = 3
        jobs[job_id]["interim_results"]["day5"] = {"distribution": dict(day5_dist), "cluster_stats": cluster_stats_d5}

        # ═══ ROUND 4 — Day 7: Echo Chamber ═══
        jobs[job_id]["current_round"] = "day7"
        batch_r4 = []
        for i, a in enumerate(agents):
            social_ctx = _build_social_context(cluster_stats_d5, a["cluster"], day=7, peer_quotes=peer_quotes)
            persona_r4 = a["persona_base"] + social_ctx
            batch_r4.append((i, persona_r4, question, options, context))

        results_r4 = _run_round(batch_r4, "day7")

        for i, r in enumerate(results_r4):
            if r is None:
                r = {"choice": options[len(options) // 2], "reasoning": "error"}
            agents[i]["day7_choice"] = r.get("choice", options[len(options) // 2])
            agents[i]["day7_score"] = _choice_to_score(agents[i]["day7_choice"], options)
            agents[i]["day7_reasoning"] = r.get("reasoning", "")

        cluster_stats_d7 = _compute_cluster_stats(agents, "day7_score")
        day7_dist = Counter(a["day7_choice"] for a in agents)

        # ═══ ANALYSIS ═══
        import statistics
        d1_scores = [a["day1_score"] for a in agents]
        d3_scores = [a["day3_score"] for a in agents]
        d5_scores = [a["day5_score"] for a in agents]
        d7_scores = [a["day7_score"] for a in agents]

        changed_total = sum(1 for i in range(actual_n) if d1_scores[i] != d7_scores[i])
        moved_support = sum(1 for i in range(actual_n) if d7_scores[i] > d1_scores[i])
        moved_oppose = sum(1 for i in range(actual_n) if d7_scores[i] < d1_scores[i])

        pol_d1 = statistics.stdev(d1_scores) if len(d1_scores) > 1 else 0
        pol_d7 = statistics.stdev(d7_scores) if len(d7_scores) > 1 else 0

        def echo_strength(agents_list, score_key):
            from collections import defaultdict
            clusters = defaultdict(list)
            for a in agents_list:
                clusters[a["cluster"]].append(a[score_key])
            stds = [statistics.stdev(v) for v in clusters.values() if len(v) > 1]
            return statistics.mean(stds) if stds else 0

        echo_d1 = echo_strength(agents, "day1_score")
        echo_d7 = echo_strength(agents, "day7_score")

        support_d1 = sum(1 for s in d1_scores if s > 0) / actual_n * 100
        oppose_d1 = sum(1 for s in d1_scores if s < 0) / actual_n * 100
        support_d7 = sum(1 for s in d7_scores if s > 0) / actual_n * 100
        oppose_d7 = sum(1 for s in d7_scores if s < 0) / actual_n * 100

        # Demographic breakdowns
        age_bins = {"18-34": (18, 34), "35-54": (35, 54), "55+": (55, 100)}
        demo_shifts = {}
        for label, (lo, hi) in age_bins.items():
            group = [a for a in agents if lo <= a.get("age", 30) <= hi]
            if not group:
                continue
            d1_s = sum(1 for a in group if a["day1_score"] > 0) / len(group) * 100
            d7_s = sum(1 for a in group if a["day7_score"] > 0) / len(group) * 100
            d1_o = sum(1 for a in group if a["day1_score"] < 0) / len(group) * 100
            d7_o = sum(1 for a in group if a["day7_score"] < 0) / len(group) * 100
            demo_shifts[label] = {
                "n": len(group),
                "support_d1": round(d1_s, 1), "support_d7": round(d7_s, 1),
                "oppose_d1": round(d1_o, 1), "oppose_d7": round(d7_o, 1),
            }

        report = {
            "question": question,
            "options": options,
            "event_name": params.get("event_name", "Social Simulation"),
            "sample_size": actual_n,
            "total_population": total_pop,
            "eligible_count": eligible_count,
            "total_llm_calls": actual_n * 4,
            "timestamp": str(datetime.now()),
            "summary": {
                "day1_support_pct": round(support_d1, 1),
                "day1_oppose_pct": round(oppose_d1, 1),
                "day7_support_pct": round(support_d7, 1),
                "day7_oppose_pct": round(oppose_d7, 1),
                "opinion_changed_pct": round(changed_total / actual_n * 100, 1),
                "moved_support": moved_support,
                "moved_oppose": moved_oppose,
                "polarization_d1": round(pol_d1, 3),
                "polarization_d7": round(pol_d7, 3),
                "echo_chamber_d1": round(echo_d1, 3),
                "echo_chamber_d7": round(echo_d7, 3),
            },
            "rounds": {
                "day1": {"distribution": dict(day1_dist)},
                "day3": {"distribution": dict(day3_dist)},
                "day5": {"distribution": dict(day5_dist)},
                "day7": {"distribution": dict(day7_dist)},
            },
            "cluster_evolution": {
                c: {
                    "n": cluster_stats_d1[c]["n"],
                    "day1_avg": cluster_stats_d1[c]["avg"],
                    "day1_majority": cluster_stats_d1[c]["majority"],
                    "day3_avg": cluster_stats_d3.get(c, {}).get("avg", 0),
                    "day5_avg": cluster_stats_d5.get(c, {}).get("avg", 0),
                    "day7_avg": cluster_stats_d7.get(c, {}).get("avg", 0),
                    "day7_majority": cluster_stats_d7.get(c, {}).get("majority", "mixed"),
                }
                for c in sorted(cluster_stats_d1.keys())
            },
            "demographic_shifts": demo_shifts,
            "opinion_journeys": [
                {
                    "age": a.get("age"), "gender": a.get("gender"),
                    "ethnicity": a.get("ethnicity"), "housing": a.get("housing_type"),
                    "income": a.get("monthly_income"), "cluster": a["cluster"],
                    "day1_choice": a["day1_choice"], "day3_choice": a["day3_choice"], "day5_choice": a["day5_choice"], "day7_choice": a["day7_choice"],
                    "day1_score": a["day1_score"], "day3_score": a["day3_score"], "day5_score": a["day5_score"], "day7_score": a["day7_score"],
                    "day1_reasoning": a.get("day1_reasoning", "")[:200],
                    "day7_reasoning": a.get("day7_reasoning", "")[:200],
                    "changed": a["day1_score"] != a["day7_score"],
                }
                for a in agents
            ],
        }

        fname = f"simulation_{job_id}.json"
        with open(OUTPUT_DIR / fname, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["rounds_done"] = 4
        jobs[job_id]["result"] = report

    except Exception as e:
        logger.exception(f"Simulation job {job_id} failed")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ============================================================
# HTTP HANDLER
# ============================================================
class APIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        if self.path == "/api/survey":
            self._handle_survey_submit(body)
        elif self.path == "/api/eligible":
            self._handle_eligible_count(body)
        elif self.path == "/api/abtest":
            self._handle_abtest_submit(body)
        elif self.path == "/api/conjoint":
            self._handle_conjoint_submit(body)
        elif self.path == "/api/social-simulation":
            self._handle_simulation_submit(body)
        else:
            self._json_response(404, {"error": "Not found"})

    def do_GET(self):
        if self.path.startswith("/api/job/"):
            job_id = self.path.split("/api/job/")[1].split("?")[0]
            self._handle_job_status(job_id)
        elif self.path == "/api/results":
            self._handle_results_list()
        elif self.path.startswith("/api/results/"):
            filename = self.path.split("/api/results/")[1].split("?")[0]
            self._handle_result_detail(filename)
        else:
            super().do_GET()

    def _handle_eligible_count(self, body):
        """Count eligible agents matching filters, return demographics summary."""
        try:
            df = load_all_agents()
            mask = pd.Series(True, index=df.index)
            age_min = body.get("age_min")
            age_max = body.get("age_max")
            gender = body.get("gender")
            housing = body.get("housing")
            income_min = body.get("income_min")
            income_max = body.get("income_max")
            marital = body.get("marital")
            education = body.get("education")
            life_phase = body.get("life_phase")
            has_income = body.get("has_income")

            if age_min is not None:
                mask &= df["age"] >= int(age_min)
            if age_max is not None:
                mask &= df["age"] <= int(age_max)
            if gender and gender != "all":
                mask &= df["gender"] == gender
            if housing and housing != "all":
                mask &= df["housing_type"] == housing
            if income_min is not None:
                mask &= df["monthly_income"] >= float(income_min)
            if income_max is not None:
                mask &= df["monthly_income"] <= float(income_max)
            if marital and marital != "all":
                mask &= df["marital_status"] == marital
            if education and education != "all":
                mask &= df["education_level"] == education
            if life_phase and life_phase != "all":
                mask &= df["life_phase"] == life_phase
            if has_income:
                mask &= df["monthly_income"] > 0

            eligible = df[mask]
            n = len(eligible)
            total = len(df)

            # Demographics summary of eligible pool
            summary = {}
            if n > 0:
                summary["age_mean"] = round(float(eligible["age"].mean()), 1)
                summary["age_range"] = f"{int(eligible['age'].min())}-{int(eligible['age'].max())}"
                summary["income_median"] = round(float(eligible["monthly_income"].median()), 0)
                summary["gender_dist"] = eligible["gender"].value_counts().to_dict()
                summary["housing_top3"] = eligible["housing_type"].value_counts().head(3).to_dict()
                summary["ethnicity_dist"] = eligible["ethnicity"].value_counts().to_dict()

            self._json_response(200, {
                "total_population": total,
                "eligible_count": n,
                "eligible_pct": round(n / total * 100, 1) if total > 0 else 0,
                "summary": summary,
            })
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_abtest_submit(self, body):
        """Launch an A/B test job."""
        if self._check_concurrent_limit():
            self._json_response(429, {"error": "Server busy. Please try again in a few minutes.", "max_concurrent": MAX_CONCURRENT_JOBS})
            return

        question = body.get("question", "").strip()
        options = body.get("options", [])
        if not question or len(options) < 2:
            self._json_response(400, {"error": "Need question + at least 2 options"})
            return

        sample_size = min(int(body.get("sample_size", 100)), 2000)
        job_id = "ab_" + datetime.now().strftime("%Y%m%d%H%M%S") + f"_{id(body) % 10000:04d}"
        with _jobs_lock:
            jobs[job_id] = {"status": "queued", "progress": 0, "total": sample_size * 2, "result": None, "error": None, "created_at": time.time()}

        params = {
            "question": question, "options": options,
            "label_a": body.get("label_a", "Scenario A"),
            "label_b": body.get("label_b", "Scenario B"),
            "context_a": body.get("context_a", ""),
            "context_b": body.get("context_b", ""),
            "sample_size": sample_size,
            "age_min": body.get("age_min"),
            "age_max": body.get("age_max"),
            "gender": body.get("gender"),
            "has_income": body.get("has_income"),
        }

        thread = threading.Thread(target=run_abtest_job, args=(job_id, params), daemon=True)
        thread.start()
        self._json_response(200, {"job_id": job_id, "status": "queued"})

    def _handle_conjoint_submit(self, body):
        """Launch a conjoint analysis job."""
        if self._check_concurrent_limit():
            self._json_response(429, {"error": "Server busy. Please try again in a few minutes.", "max_concurrent": MAX_CONCURRENT_JOBS})
            return

        question = body.get("question", "").strip()
        profiles = body.get("profiles", [])
        if not question or len(profiles) < 2:
            self._json_response(400, {"error": "Need question + at least 2 profiles"})
            return

        sample_size = min(int(body.get("sample_size", 100)), 2000)
        job_id = "cj_" + datetime.now().strftime("%Y%m%d%H%M%S") + f"_{id(body) % 10000:04d}"
        with _jobs_lock:
            jobs[job_id] = {"status": "queued", "progress": 0, "total": sample_size, "result": None, "error": None, "created_at": time.time()}

        params = {
            "question": question, "profiles": profiles,
            "context": body.get("context", ""),
            "none_option": body.get("none_option", "None of these"),
            "sample_size": sample_size,
            "age_min": body.get("age_min"),
            "age_max": body.get("age_max"),
            "gender": body.get("gender"),
            "has_income": body.get("has_income"),
        }

        thread = threading.Thread(target=run_conjoint_job, args=(job_id, params), daemon=True)
        thread.start()
        self._json_response(200, {"job_id": job_id, "status": "queued"})

    def _handle_simulation_submit(self, body):
        """Launch a social simulation job."""
        if self._check_concurrent_limit():
            self._json_response(429, {"error": "Server busy. Please try again in a few minutes.", "max_concurrent": MAX_CONCURRENT_JOBS})
            return

        question = body.get("question", "").strip()
        options = body.get("options", [])
        if not question or len(options) < 2:
            self._json_response(400, {"error": "Need question + at least 2 options"})
            return

        sample_size = min(int(body.get("sample_size", 100)), 2000)
        job_id = "sim_" + datetime.now().strftime("%Y%m%d%H%M%S") + f"_{id(body) % 10000:04d}"
        with _jobs_lock:
            jobs[job_id] = {
                "status": "queued", "progress": 0, "total": sample_size * 3,
                "result": None, "error": None, "rounds_done": 0,
                "current_round": None, "interim_results": {},
                "created_at": time.time(),
            }

        params = {
            "question": question, "options": options,
            "context": body.get("context", ""),
            "event_name": body.get("event_name", "Social Simulation"),
            "peer_quotes": body.get("peer_quotes"),
            "sample_size": sample_size,
            "age_min": body.get("age_min"),
            "age_max": body.get("age_max"),
            "gender": body.get("gender"),
            "housing": body.get("housing"),
        }

        thread = threading.Thread(target=run_simulation_job, args=(job_id, params), daemon=True)
        thread.start()
        self._json_response(200, {"job_id": job_id, "status": "queued"})

    def _check_concurrent_limit(self):
        """Check if too many jobs are running. Returns True if over limit."""
        with _jobs_lock:
            running = sum(1 for j in jobs.values() if j["status"] in ("queued", "sampling", "running"))
            return running >= MAX_CONCURRENT_JOBS

    def _cleanup_old_jobs(self):
        """Remove old completed jobs to prevent memory leak."""
        with _jobs_lock:
            done_jobs = [(k, v) for k, v in jobs.items() if v["status"] in ("done", "error")]
            done_jobs.sort(key=lambda x: x[1].get("created_at", 0))
            while len(done_jobs) > MAX_JOBS_HISTORY:
                old_id, _ = done_jobs.pop(0)
                del jobs[old_id]

    def _handle_survey_submit(self, body):
        # Check concurrent limit
        if self._check_concurrent_limit():
            self._json_response(429, {"error": "Server busy. Please try again in a few minutes.", "max_concurrent": MAX_CONCURRENT_JOBS})
            return

        # Validate
        question = body.get("question", "").strip()
        options = body.get("options", [])
        client_name = body.get("client_name", "Anonymous")
        sample_size = min(int(body.get("sample_size", 30)), 5000)

        if not question or len(options) < 2:
            self._json_response(400, {"error": "Need question + at least 2 options"})
            return

        job_id = datetime.now().strftime("%Y%m%d%H%M%S") + f"_{id(body) % 10000:04d}"
        with _jobs_lock:
            jobs[job_id] = {"status": "queued", "progress": 0, "total": sample_size, "result": None, "error": None, "created_at": time.time()}

        params = {
            "client_name": client_name,
            "question": question,
            "options": [o.strip() for o in options if o.strip()],
            "context": body.get("context", ""),
            "sample_size": sample_size,
            "age_min": body.get("age_min"),
            "age_max": body.get("age_max"),
            "gender": body.get("gender"),
            "housing": body.get("housing"),
            "income_min": body.get("income_min"),
            "income_max": body.get("income_max"),
            "marital": body.get("marital"),
            "education": body.get("education"),
            "life_phase": body.get("life_phase"),
            "has_income": body.get("has_income"),
        }

        self._cleanup_old_jobs()
        thread = threading.Thread(target=run_survey_job, args=(job_id, params), daemon=True)
        thread.start()

        self._json_response(200, {"job_id": job_id, "status": "queued"})

    def _handle_job_status(self, job_id):
        job = jobs.get(job_id)
        if not job:
            self._json_response(404, {"error": "Job not found"})
            return
        resp = {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "total": job["total"],
            "eligible_count": job.get("eligible_count"),
            "total_population": job.get("total_population"),
            "result": job["result"],
            "error": job["error"],
        }
        # Simulation-specific fields
        if "rounds_done" in job:
            resp["rounds_done"] = job.get("rounds_done", 0)
            resp["current_round"] = job.get("current_round")
            resp["interim_results"] = job.get("interim_results", {})
        self._json_response(200, resp)

    def _handle_results_list(self):
        """List all saved result files."""
        try:
            files = []
            for f in sorted(OUTPUT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
                name = f.name
                if name.startswith("survey_"):
                    ftype = "survey"
                elif name.startswith("simulation_") or name.startswith("sim_"):
                    ftype = "simulation"
                elif name.startswith("abtest_") or name.startswith("ab_"):
                    ftype = "abtest"
                elif name.startswith("conjoint_") or name.startswith("cj_"):
                    ftype = "conjoint"
                else:
                    ftype = "other"
                stat = f.stat()
                files.append({
                    "filename": name,
                    "type": ftype,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            self._json_response(200, files)
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_result_detail(self, filename):
        """Return content of a specific result file."""
        try:
            filepath = OUTPUT_DIR / filename
            if not filepath.exists() or not filepath.suffix == ".json":
                self._json_response(404, {"error": "File not found"})
                return
            with open(filepath) as f:
                data = json.load(f)
            self._json_response(200, data)
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _json_response(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        if "/api/" in (args[0] if args else ""):
            logger.info(f"{self.address_string()} {format % args}")


# ============================================================
# THREADED HTTP SERVER (handles concurrent requests)
# ============================================================
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in a new thread."""
    daemon_threads = True


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3456))
    # Pre-load agents in background
    threading.Thread(target=load_all_agents, daemon=True).start()

    server = ThreadedHTTPServer(("", port), APIHandler)
    logger.info(f"Server running on port {port} (threaded)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.server_close()
