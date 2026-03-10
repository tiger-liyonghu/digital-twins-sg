"""
LLM survey simulation — Verbalized Sampling + Reformulated Prompting (VS+RP).

Shared by all simulation scripts: backtests, client simulations, policy analysis.
"""

import json
import time
import random
import requests
import concurrent.futures
from lib.config import DEEPSEEK_API_KEY, DEEPSEEK_URL

CONCURRENCY = 20  # parallel LLM calls


VS_RP_SYSTEM = (
    "You are a survey research analyst estimating how a specific respondent would answer a question. "
    "You do NOT know the outcome of any real-world event. "
    "Estimate based ONLY on the respondent's demographic profile, personality, and life circumstances.\n\n"
    "Respond in JSON:\n"
    '{"probabilities": {"option_text": 0.XX, ...}, "reasoning": "1-2 sentences"}\n\n'
    "Rules:\n"
    "- Assign a probability (0.00 to 1.00) to EVERY option. Probabilities must sum to 1.00.\n"
    "- Different respondent profiles SHOULD produce different distributions.\n"
    "- Base your estimate on the respondent's age, ethnicity, income, education, personality traits, and life phase.\n"
    "- Do NOT default to the most popular or socially desirable answer.\n"
    "- There is no correct answer. Real populations show diverse opinions."
)


def ask_agent(persona, question, options, context="", max_retries=5):
    """
    Query LLM with VS+RP method for a single agent.

    Returns dict with: choice, reasoning, probabilities
    """
    user = f"RESPONDENT PROFILE:\n{persona}\n\n"
    if context:
        user += f"CONTEXT:\n{context}\n\n"
    user += (
        f"SURVEY QUESTION:\n{question}\n\n"
        f"OPTIONS:\n{json.dumps(options, ensure_ascii=False)}\n\n"
        "Estimate the probability distribution over these options for this specific respondent."
    )

    for attempt in range(max_retries):
        try:
            resp = requests.post(DEEPSEEK_URL, headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            }, json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": VS_RP_SYSTEM},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
                "max_tokens": 300,
                "response_format": {"type": "json_object"},
            }, timeout=60)

            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                result = json.loads(content)
                return _sample_from_probs(result, options)
            elif resp.status_code == 429:
                time.sleep(2 * (attempt + 1))
                continue
        except Exception as e:
            print(f"  LLM error (attempt {attempt + 1}): {e}")
            time.sleep(2 * (attempt + 1))

    return {"choice": random.choice(options), "reasoning": "API error", "probabilities": {}}


def _sample_from_probs(result, options):
    """Verbalized Sampling: sample a single choice from LLM's probability distribution."""
    probs = result.get("probabilities", {})
    if not probs:
        return result

    matched = {}
    for opt in options:
        opt_lower = opt.lower().strip()
        best_p = 0.0
        for k, v in probs.items():
            k_lower = k.lower().strip()
            try:
                p = float(v)
            except (ValueError, TypeError):
                p = 0.0
            # Require minimum 3-char overlap for substring matching to avoid false positives
            if k_lower == opt_lower:
                best_p = max(best_p, p)
            elif len(k_lower) >= 3 and len(opt_lower) >= 3:
                if k_lower in opt_lower or opt_lower in k_lower:
                    best_p = max(best_p, p)
        matched[opt] = best_p

    # If only 1 option matched and others are 0, fall back to uniform —
    # this means matching failed rather than a genuine single-option prediction
    n_matched = sum(1 for v in matched.values() if v > 0)
    total = sum(matched.values())
    if n_matched <= 1 and len(options) > 2:
        weights = [1.0 / len(options)] * len(options)
    elif total > 0:
        weights = [matched[opt] / total for opt in options]
    else:
        weights = [1.0 / len(options)] * len(options)

    chosen = random.choices(options, weights=weights, k=1)[0]
    return {
        "choice": chosen,
        "reasoning": result.get("reasoning", ""),
        "probabilities": matched,
    }


def ask_agents_batch(agents, question, options, context="", on_progress=None):
    """
    High-concurrency batch LLM survey. 20 parallel calls.

    Args:
        agents: list of (index, agent_dict, persona_str) tuples
        question, options, context: survey params
        on_progress: callback(completed_count, total) for progress reporting

    Returns:
        list of result dicts (same order as input)
    """
    total = len(agents)
    results = [None] * total
    counter = [0]  # mutable for closure

    def _call(item):
        idx, agent, persona = item
        return idx, ask_agent(persona, question, options, context)

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = {ex.submit(_call, item): item for item in agents}
        for future in concurrent.futures.as_completed(futures):
            idx, result = future.result()
            results[idx] = result
            counter[0] += 1
            if on_progress and counter[0] % 50 == 0:
                on_progress(counter[0], total)

    return results


def redistribute_non_candidate(pcts):
    """Redistribute abstention/spoil votes proportionally to actual candidates."""
    abstain_kw = ["not vote", "spoil vote", "undecided", "abstain", "would not"]
    abstain_keys = []
    candidate_keys = []
    for k in pcts:
        if any(kw in k.lower() for kw in abstain_kw):
            abstain_keys.append(k)
        else:
            candidate_keys.append(k)

    if not abstain_keys or not candidate_keys:
        return None

    abstain_total = sum(pcts[k] for k in abstain_keys)
    if abstain_total < 0.1:
        return None

    candidate_total = sum(pcts[k] for k in candidate_keys)
    if candidate_total <= 0:
        return None

    adjusted = {}
    for k in candidate_keys:
        share = pcts[k] / candidate_total
        adjusted[k] = round(pcts[k] + abstain_total * share, 1)
    return adjusted
