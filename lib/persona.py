"""
Agent persona generation — Reformulated Prompting (third-person neutral framing).

Converts agent demographic data to natural language persona descriptions
for LLM survey simulation.
"""


def agent_to_persona(a):
    """
    Convert an agent dict to a third-person persona description.
    Uses Reformulated Prompting: neutral framing to reduce social desirability bias.
    """
    inc = a.get("monthly_income", 0) or 0
    inc_desc = "unemployed" if inc == 0 else f"earning ${int(inc):,}/month"

    traits = []
    o = float(a.get("big5_o", 3) or 3)
    c = float(a.get("big5_c", 3) or 3)
    e = float(a.get("big5_e", 3) or 3)
    ag = float(a.get("big5_a", 3) or 3)
    n = float(a.get("big5_n", 3) or 3)

    if o > 3.8: traits.append("curious and open-minded")
    elif o < 2.5: traits.append("practical and conventional")
    if c > 3.8: traits.append("disciplined and organized")
    elif c < 2.5: traits.append("spontaneous and flexible")
    if e > 3.8: traits.append("outgoing and sociable")
    elif e < 2.5: traits.append("reserved and introspective")
    if ag > 3.8: traits.append("cooperative and trusting")
    elif ag < 2.5: traits.append("competitive and skeptical")
    if n > 3.8: traits.append("emotionally sensitive")
    elif n < 2.5: traits.append("emotionally stable")
    if not traits:
        traits.append("moderate across personality dimensions")

    risk = float(a.get("risk_appetite", 3) or 3)
    if risk > 3.8: traits.append("risk-tolerant")
    elif risk < 2.2: traits.append("risk-averse")

    personality = ", ".join(traits)

    return (
        f"This respondent is a {a['age']}-year-old {a['gender']} {a['ethnicity']} resident of Singapore.\n"
        f"Lives in {a.get('planning_area', 'Singapore')}, in a {a.get('housing_type', 'HDB')} flat.\n"
        f"Education: {a.get('education_level', 'Secondary')}, currently {inc_desc}.\n"
        f"Marital status: {a.get('marital_status', 'Single')}. Health: {a.get('health_status', 'Healthy')}.\n"
        f"Life phase: {a.get('life_phase', 'establishment')}.\n"
        f"Personality: {personality}."
    )


def agent_response_meta(agent):
    """Extract demographic metadata from agent dict for response records."""
    return {
        "agent_id": agent.get("agent_id", ""),
        "agent_age": agent.get("age", 0),
        "agent_gender": agent.get("gender", ""),
        "agent_ethnicity": agent.get("ethnicity", ""),
        "agent_income": agent.get("monthly_income", 0) or 0,
        "agent_housing": agent.get("housing_type", ""),
        "agent_education": agent.get("education_level", ""),
        "agent_area": agent.get("planning_area", ""),
    }
