"""
Persona prompt builder: constructs the LLM system prompt for each agent.

Three layers:
  Layer A — Statistical identity (hard facts, ~180 tokens)
  Layer B — NVIDIA narrative (soft persona, ~200 tokens, adults only)
  Layer C — Memories (~100 tokens, Phase 2)

Topic-aware injection: pass topic_tags to include domain-specific fields
(e.g. CPF balances for retirement topics) without bloating every prompt.
"""

# Maps topic tags to additional agent fields injected into Layer A.
# When a survey question is tagged with one or more topics, the
# corresponding fields are appended to the persona prompt.
TOPIC_FIELDS: dict[str, list[tuple[str, str]]] = {
    # tag -> list of (agent_key, display_label)
    "cpf": [
        ("cpf_oa", "CPF OA balance"),
        ("cpf_sa", "CPF SA balance"),
        ("cpf_ma", "CPF MA balance"),
        ("cpf_ra", "CPF RA balance"),
    ],
    "housing": [
        ("housing_value", "Property value"),
        ("monthly_savings", "Monthly savings"),
        ("total_debt", "Total debt"),
    ],
    "transport": [
        ("commute_mode", "Commute mode"),
    ],
    "health": [
        ("chronic_conditions", "Chronic conditions"),
        ("bmi_category", "BMI category"),
        ("smoking", "Smoker"),
    ],
    "media": [
        ("media_diet", "Primary news source"),
        ("social_media_usage", "Social media usage"),
    ],
}


def build_persona(
    agent: dict,
    memories: list | None = None,
    topic_tags: list[str] | None = None,
) -> str:
    """
    Build a persona prompt for LLM from an agent record.

    Args:
        agent: dict from Supabase agents table
        memories: list of memory dicts (Phase 2, currently unused)
        topic_tags: optional list of topic tags for domain-specific field injection

    Returns:
        Complete persona prompt string
    """
    parts = []

    # Layer A: Statistical identity
    parts.append(_build_layer_a(agent, topic_tags=topic_tags))

    # Layer B: NVIDIA narrative (only for adults with narratives)
    narrative = _build_layer_b(agent)
    if narrative:
        parts.append(narrative)

    # Layer C: Memories (Phase 2)
    if memories:
        parts.append(_build_layer_c(memories))

    return "\n\n".join(parts)


def _build_layer_a(agent: dict, topic_tags: list[str] | None = None) -> str:
    """Statistical identity layer — third-person neutral framing (Reformulated Prompting)."""
    age = agent.get("age", 30)
    gender = "male" if agent.get("gender") == "M" else "female"
    ethnicity = agent.get("ethnicity", "Chinese")
    education = agent.get("education_level", "").replace("_", " ")
    income = agent.get("monthly_income", 0)
    housing = agent.get("housing_type", "").replace("_", " ")
    area = agent.get("planning_area", "")
    marital = agent.get("marital_status", "Single").lower()
    health = agent.get("health_status", "Healthy").replace("_", " ").lower()
    residency = agent.get("residency_status", "Citizen")
    life_phase = agent.get("life_phase", "").replace("_", " ")
    occupation = agent.get("occupation", "")
    industry = agent.get("industry", "")
    religion = agent.get("religion", "")
    language = agent.get("primary_language", "")
    num_children = agent.get("num_children", 0)
    generation = agent.get("generation", "")
    ns_status = agent.get("ns_status", "")
    has_vehicle = agent.get("has_vehicle", False)

    # Personality summary
    big5 = _summarize_big5(agent)

    lines = [
        f"This respondent is a {age}-year-old {ethnicity} {gender} living in {area}, Singapore.",
    ]

    # Religion & language — high-impact for attitude simulation
    identity_parts = []
    if religion:
        identity_parts.append(f"religion: {religion}")
    if language:
        identity_parts.append(f"speaks {language} at home")
    if generation:
        identity_parts.append(f"{generation} generation")
    if identity_parts:
        lines.append(" ".join(s.capitalize() if i == 0 else s for i, s in enumerate(identity_parts)) + ".")

    lines.append(f"Education: {education}. Marital status: {marital}.")

    # Children
    if num_children and num_children > 0:
        lines.append(f"Has {num_children} {'child' if num_children == 1 else 'children'}.")

    if income > 0:
        lines.append(f"Monthly income: ${income:,}. Housing: {housing}.")
    else:
        lines.append(f"Housing: {housing}. No personal income.")

    if occupation:
        lines.append(f"Occupation: {occupation}.")
    if industry:
        lines.append(f"Industry: {industry}.")

    lines.append(f"Health: {health}. Residency: {residency}.")

    # NS status — relevant for male citizens/PRs
    if ns_status and ns_status not in ("Not_Applicable", ""):
        lines.append(f"National Service: {ns_status.replace('_', ' ').lower()}.")

    # Vehicle ownership
    if has_vehicle:
        lines.append("Owns a vehicle.")

    lines.append(f"Life stage: {life_phase}.")
    lines.append(f"Personality: {big5}")

    # Topic-aware dynamic injection
    if topic_tags:
        extras = []
        seen_keys: set[str] = set()
        for tag in topic_tags:
            for agent_key, label in TOPIC_FIELDS.get(tag, []):
                if agent_key in seen_keys:
                    continue
                seen_keys.add(agent_key)
                val = agent.get(agent_key)
                if val is None or val == "" or val == []:
                    continue
                if isinstance(val, bool):
                    extras.append(f"{label}: {'yes' if val else 'no'}")
                elif isinstance(val, list):
                    extras.append(f"{label}: {', '.join(str(v) for v in val)}")
                elif isinstance(val, (int, float)) and val > 0:
                    extras.append(f"{label}: ${val:,}" if "balance" in label or "value" in label or "debt" in label or "savings" in label else f"{label}: {val}")
                else:
                    extras.append(f"{label}: {str(val).replace('_', ' ')}")
        if extras:
            lines.append(" ".join(extras) + ".")

    return " ".join(lines)


def _build_layer_b(agent: dict) -> str:
    """NVIDIA narrative layer — rich persona text."""
    # Children (synthetic) have no narratives
    if agent.get("data_source") == "synthetic":
        return ""

    parts = []
    persona = agent.get("persona", "")
    if persona:
        # Truncate to ~200 tokens (~800 chars) to control cost
        parts.append(persona[:800])

    cultural = agent.get("cultural_background", "")
    if cultural:
        parts.append(cultural[:400])

    hobbies = agent.get("hobbies_and_interests", "")
    if hobbies:
        parts.append(f"Hobbies: {hobbies[:300]}")

    if not parts:
        return ""

    return "This respondent's background: " + " ".join(parts)


def _build_layer_c(memories: list) -> str:
    """Memory layer (Phase 2)."""
    if not memories:
        return ""

    lines = ["Recent memories:"]
    for m in memories[:10]:
        content = m.get("content", "")[:150]
        mtype = m.get("memory_type", "experience")
        lines.append(f"- [{mtype}] {content}")

    return "\n".join(lines)


def _summarize_big5(agent: dict) -> str:
    """Summarize Big Five traits into a brief natural language description."""
    o = float(agent.get("big5_o", 3.0))
    c = float(agent.get("big5_c", 3.0))
    e = float(agent.get("big5_e", 3.0))
    a = float(agent.get("big5_a", 3.0))
    n = float(agent.get("big5_n", 3.0))

    traits = []
    if o > 3.8:
        traits.append("curious and open-minded")
    elif o < 2.5:
        traits.append("practical and conventional")

    if c > 3.8:
        traits.append("disciplined and organized")
    elif c < 2.5:
        traits.append("spontaneous and flexible")

    if e > 3.8:
        traits.append("outgoing and sociable")
    elif e < 2.5:
        traits.append("reserved and introspective")

    if a > 3.8:
        traits.append("cooperative and trusting")
    elif a < 2.5:
        traits.append("competitive and skeptical")

    if n > 3.8:
        traits.append("emotionally sensitive")
    elif n < 2.5:
        traits.append("emotionally stable")

    if not traits:
        traits.append("moderate across personality dimensions")

    risk = float(agent.get("risk_appetite", 3.0))
    if risk > 3.8:
        traits.append("risk-tolerant")
    elif risk < 2.2:
        traits.append("risk-averse")

    return ", ".join(traits) + "."
