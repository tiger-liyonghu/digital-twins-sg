"""
Social graph generator: build relationships from agent attributes.

Three relationship layers:
  - Family: same planning_area + compatible age/marital (algorithmically clustered)
  - Neighbors: same planning_area + age proximity
  - Weak ties: random cross-area connections (social media)

No external graph DB needed — works on the sampled subset (200-500 agents).
"""

import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def build_social_graph(agents: list[dict], avg_family: int = 3, avg_friends: int = 5, avg_weak: int = 3) -> dict:
    """
    Build a social graph from sampled agents.

    Returns:
        {agent_id: [{"target": id, "type": str, "strength": float}, ...]}
    """
    agent_map = {a["agent_id"]: a for a in agents}
    graph = {a["agent_id"]: [] for a in agents}

    # Index by planning_area for fast lookup
    by_area = defaultdict(list)
    for a in agents:
        by_area[a.get("planning_area", "Unknown")].append(a)

    # Step 1: Generate family clusters
    families = _build_families(agents)
    for family in families:
        for i, a_id in enumerate(family):
            for j, b_id in enumerate(family):
                if i != j:
                    graph[a_id].append({"target": b_id, "type": "family", "strength": 0.8})

    # Step 2: Neighbor/friend connections (same area, age proximity)
    existing = {a_id: {c["target"] for c in conns} for a_id, conns in graph.items()}
    for area, area_agents in by_area.items():
        for agent in area_agents:
            candidates = [
                a for a in area_agents
                if a["agent_id"] != agent["agent_id"]
                and a["agent_id"] not in existing[agent["agent_id"]]
                and abs(a.get("age", 30) - agent.get("age", 30)) < 15
            ]
            n_friends = min(avg_friends, len(candidates))
            if n_friends > 0:
                friends = random.sample(candidates, n_friends)
                for f in friends:
                    # Strength based on age proximity and same ethnicity
                    age_sim = 1.0 - abs(f.get("age", 30) - agent.get("age", 30)) / 15
                    eth_bonus = 0.1 if f.get("ethnicity") == agent.get("ethnicity") else 0
                    strength = round(0.2 + age_sim * 0.2 + eth_bonus, 2)
                    graph[agent["agent_id"]].append({"target": f["agent_id"], "type": "friend", "strength": strength})
                    existing[agent["agent_id"]].add(f["agent_id"])

    # Step 3: Weak ties (random cross-area, social media)
    all_ids = [a["agent_id"] for a in agents]
    for agent in agents:
        a_id = agent["agent_id"]
        candidates = [i for i in all_ids if i != a_id and i not in existing[a_id]]
        n_weak = min(avg_weak, len(candidates))
        if n_weak > 0:
            weak = random.sample(candidates, n_weak)
            for w_id in weak:
                graph[a_id].append({"target": w_id, "type": "social_media", "strength": 0.1})

    total_edges = sum(len(v) for v in graph.values())
    logger.info(f"Social graph: {len(agents)} agents, {total_edges} edges, "
                f"{len(families)} families")
    return graph


def _build_families(agents: list[dict]) -> list[list[str]]:
    """
    Algorithmically cluster agents into family units.
    Uses planning_area + marital_status + age compatibility.
    """
    families = []
    assigned = set()

    # Group married adults by area
    by_area = defaultdict(list)
    for a in agents:
        if a["agent_id"] not in assigned:
            by_area[a.get("planning_area", "")].append(a)

    for area, area_agents in by_area.items():
        # Find married pairs first
        married = [a for a in area_agents if a.get("marital_status", "").lower() == "married" and a["agent_id"] not in assigned]
        random.shuffle(married)

        i = 0
        while i + 1 < len(married):
            a, b = married[i], married[i + 1]
            # Pair if different gender and age within 10 years
            if a.get("gender") != b.get("gender") and abs(a.get("age", 30) - b.get("age", 30)) <= 10:
                family = [a["agent_id"], b["agent_id"]]
                assigned.add(a["agent_id"])
                assigned.add(b["agent_id"])

                # Try to add children (younger agents in same area)
                parent_age = min(a.get("age", 30), b.get("age", 30))
                children = [
                    c for c in area_agents
                    if c["agent_id"] not in assigned
                    and c.get("age", 30) < parent_age - 18
                    and c.get("age", 30) >= 0
                    and c.get("marital_status", "").lower() == "single"
                ]
                for child in children[:random.randint(0, 2)]:
                    family.append(child["agent_id"])
                    assigned.add(child["agent_id"])

                families.append(family)
                i += 2
            else:
                i += 1

    return families


def get_graph_stats(graph: dict) -> dict:
    """Return summary statistics about the social graph."""
    degrees = [len(v) for v in graph.values()]
    type_counts = defaultdict(int)
    for conns in graph.values():
        for c in conns:
            type_counts[c["type"]] += 1

    return {
        "nodes": len(graph),
        "total_edges": sum(degrees),
        "avg_degree": round(sum(degrees) / max(len(degrees), 1), 1),
        "max_degree": max(degrees) if degrees else 0,
        "by_type": dict(type_counts),
    }
