"""
Tick Manager — Time Engine for the Singapore Digital Twin.

Each tick = 1 simulated day.
Not all 20,000 agents are active every tick. The Time Engine selectively
activates 3-7% of agents (~600-1,400) based on:
1. Life phase activation probability
2. Pending events requiring response
3. Scheduled life transitions
4. Random sampling for background activity

This keeps LLM costs manageable while maintaining realistic dynamics.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Optional, Set
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Life phase activation probabilities (from life_ontology.yaml)
PHASE_ACTIVATION_PROB = {
    "dependence": 0.005,
    "growth": 0.008,
    "adolescence": 0.01,
    "ns_service": 0.02,
    "establishment": 0.03,
    "bearing": 0.025,
    "release": 0.02,
    "retirement_early": 0.015,
    "decline": 0.015,
    "end_of_life": 0.01,
}


class TickManager:
    """Manages simulation ticks and agent activation."""

    def __init__(self, agents_df: pd.DataFrame, start_date: date,
                 seed: int = 42):
        self.agents = agents_df
        self.current_tick = 0
        self.current_date = start_date
        self.rng = np.random.default_rng(seed)

        # Track which agents have pending events
        self.pending_events: Dict[str, List[dict]] = {}  # agent_id -> events
        # Track scheduled transitions
        self.scheduled: Dict[int, List[str]] = {}  # tick -> agent_ids

        logger.info(f"TickManager initialized: {len(agents_df)} agents, "
                    f"start={start_date}")

    def select_active_agents(self) -> List[str]:
        """
        Select which agents are active this tick.

        Returns list of agent_ids to activate.
        """
        active_set: Set[str] = set()

        # 1. Agents with pending events (must respond)
        for agent_id, events in self.pending_events.items():
            if events:
                active_set.add(agent_id)

        # 2. Agents with scheduled transitions this tick
        scheduled = self.scheduled.get(self.current_tick, [])
        active_set.update(scheduled)

        # 3. Life phase-based probabilistic activation
        for _, agent in self.agents.iterrows():
            if agent["agent_id"] in active_set:
                continue
            if not agent.get("is_alive", True):
                continue

            phase = agent.get("life_phase", "establishment")
            prob = PHASE_ACTIVATION_PROB.get(phase, 0.02)

            if self.rng.random() < prob:
                active_set.add(agent["agent_id"])

        # 4. Ensure minimum activation (at least 1% for statistical coverage)
        min_active = max(int(len(self.agents) * 0.01), 50)
        if len(active_set) < min_active:
            remaining = set(self.agents["agent_id"]) - active_set
            n_extra = min(min_active - len(active_set), len(remaining))
            extra = self.rng.choice(list(remaining), size=n_extra, replace=False)
            active_set.update(extra)

        logger.info(f"Tick {self.current_tick} ({self.current_date}): "
                    f"{len(active_set)} agents active "
                    f"({len(active_set)/len(self.agents)*100:.1f}%)")

        return list(active_set)

    def advance_tick(self):
        """Move to next tick (next day)."""
        self.current_tick += 1
        self.current_date += timedelta(days=1)

        # Age agents on their birthday (simplified: Jan 1 for everyone)
        if self.current_date.month == 1 and self.current_date.day == 1:
            self._age_all_agents()

    def _age_all_agents(self):
        """Increment age for all living agents on Jan 1."""
        alive_mask = self.agents["is_alive"] == True
        self.agents.loc[alive_mask, "age"] += 1
        logger.info(f"New year: aged {alive_mask.sum()} agents")

    def queue_event(self, agent_id: str, event: dict):
        """Queue an event for an agent to process."""
        if agent_id not in self.pending_events:
            self.pending_events[agent_id] = []
        self.pending_events[agent_id].append(event)

    def queue_event_for_relevant(self, event, agents_df: pd.DataFrame):
        """Queue an external event for all relevant agents."""
        from engine.pipeline.collectors.base import ExternalEvent
        if not isinstance(event, ExternalEvent):
            return
        for _, agent in agents_df.iterrows():
            if event.affects_agent(agent.to_dict()):
                self.queue_event(agent["agent_id"], event.to_dict())

    def clear_events(self, agent_id: str):
        """Clear processed events for an agent."""
        self.pending_events.pop(agent_id, None)

    def schedule_transition(self, tick: int, agent_id: str):
        """Schedule an agent for activation at a specific tick."""
        if tick not in self.scheduled:
            self.scheduled[tick] = []
        self.scheduled[tick].append(agent_id)

    def get_tick_stats(self) -> dict:
        """Get statistics for current tick."""
        return {
            "tick": self.current_tick,
            "date": str(self.current_date),
            "total_agents": len(self.agents),
            "alive_agents": int((self.agents["is_alive"] == True).sum()),
            "pending_events": sum(len(v) for v in self.pending_events.values()),
            "scheduled_this_tick": len(self.scheduled.get(self.current_tick, [])),
        }


class SimulationRunner:
    """
    High-level simulation orchestrator.

    Wires together all three decision layers:
    - Layer 1: LifeRuleEngine (deterministic, zero cost)
    - Layer 2: ProbabilityEngine (Markov/logistic, near-zero cost)
    - Layer 3: LLMDecisionEngine (DeepSeek API, $0.01-0.05/call)

    Plus external data collection and snapshot-based time rollback.
    """

    def __init__(self, agents_df: pd.DataFrame, start_date: date,
                 seed: int = 42, snapshot_dir: str = "snapshots",
                 llm_api_key: str = "", enable_collectors: bool = True):
        self.tick_manager = TickManager(agents_df, start_date, seed)
        self.event_log: List[dict] = []
        self.decision_log: List[dict] = []

        # Layer 1: Rule engine
        from engine.rules.life_rules import LifeRuleEngine
        self.rule_engine = LifeRuleEngine()

        # Layer 2: Probability engine
        from engine.models.probability_models import ProbabilityEngine
        self.prob_engine = ProbabilityEngine(seed=seed)

        # Layer 3: LLM engine
        from engine.llm.decision_engine import LLMDecisionEngine
        self.llm_engine = LLMDecisionEngine(api_key=llm_api_key)

        # External data collectors
        from engine.pipeline.collectors import (
            CollectorRegistry, RSSCollector, GovDataCollector,
            MarketDataCollector,
        )
        self.collector_registry = CollectorRegistry()
        if enable_collectors:
            self.collector_registry.register(RSSCollector())
            self.collector_registry.register(GovDataCollector())
            self.collector_registry.register(MarketDataCollector())

        # Snapshot manager
        from engine.pipeline.snapshot_manager import SnapshotManager
        self.snapshot_mgr = SnapshotManager(
            snapshot_dir=snapshot_dir, auto_interval=30)

    def run_tick(self) -> dict:
        """
        Execute one simulation tick.

        Pipeline per tick:
        1. Collect external events (RSS, market data, gov APIs)
        2. Route events to relevant agents
        3. Select active agents
        4. For each active agent:
           a. Layer 1: Rule engine (deterministic)
           b. Layer 2: Probability models (stochastic)
           c. Layer 3: LLM (if needed for complex decisions)
        5. Apply state changes
        6. Log everything
        7. Auto-snapshot if interval reached
        8. Advance tick
        """
        tick = self.tick_manager.current_tick
        sim_date = str(self.tick_manager.current_date)

        # Step 1: Collect external events
        external_events = self.collector_registry.fetch_all(sim_date)

        # Step 2: Route events to relevant agents
        for event in external_events:
            self.tick_manager.queue_event_for_relevant(
                event, self.tick_manager.agents)

        # Step 3: Select active agents
        active_ids = self.tick_manager.select_active_agents()

        # Step 4: Process each active agent
        tick_stats = {
            "tick": tick,
            "date": sim_date,
            "active_agents": len(active_ids),
            "rule_decisions": 0,
            "prob_decisions": 0,
            "llm_decisions": 0,
            "events_ingested": len(external_events),
            "events_routed": sum(
                len(v) for v in self.tick_manager.pending_events.values()),
            "llm_cost_usd": 0.0,
            "state_changes": [],
        }

        for agent_id in active_ids:
            result = self._process_agent(agent_id, external_events)
            tick_stats["rule_decisions"] += result.get("rule", 0)
            tick_stats["prob_decisions"] += result.get("prob", 0)
            tick_stats["llm_decisions"] += result.get("llm", 0)
            tick_stats["llm_cost_usd"] += result.get("llm_cost", 0.0)
            tick_stats["state_changes"].extend(result.get("changes", []))

            # Clear processed events
            self.tick_manager.clear_events(agent_id)

        # Step 6: Log
        self.event_log.append(tick_stats)

        # Step 7: Auto-snapshot
        if self.snapshot_mgr.should_auto_snapshot(tick):
            self.snapshot_mgr.save_snapshot(
                self.tick_manager.agents, tick, sim_date,
                self.event_log,
                metadata={"active": len(active_ids),
                          "llm_cost": tick_stats["llm_cost_usd"]},
            )

        # Step 8: Advance
        self.tick_manager.advance_tick()

        logger.info(f"Tick {tick} complete: {tick_stats['rule_decisions']}R "
                    f"{tick_stats['prob_decisions']}P "
                    f"{tick_stats['llm_decisions']}L "
                    f"({len(external_events)} events)")
        return tick_stats

    def _process_agent(self, agent_id: str, events: List) -> dict:
        """
        Process one agent through the 3-layer decision engine.
        Returns counts of decisions made at each layer + state changes.
        """
        result = {"rule": 0, "prob": 0, "llm": 0, "llm_cost": 0.0,
                  "changes": []}

        # Get agent row as dict
        agent_mask = self.tick_manager.agents["agent_id"] == agent_id
        if not agent_mask.any():
            return result
        agent_row = self.tick_manager.agents.loc[agent_mask].iloc[0]
        agent = agent_row.to_dict()

        # ---- Layer 1: Rule engine (deterministic, zero cost) ----
        rule_actions = self.rule_engine.evaluate(
            agent, self.tick_manager.current_tick,
            str(self.tick_manager.current_date))
        result["rule"] = len(rule_actions)

        # Apply rule actions to agent state
        for action in rule_actions:
            self._apply_action(agent_id, action, agent_mask)
            result["changes"].append({
                "agent_id": agent_id, "layer": "rule",
                "action": action,
            })

        # ---- Layer 2: Probability models (near-zero cost) ----
        prob_events = self.prob_engine.evaluate(agent)
        result["prob"] = len(prob_events)

        for pe in prob_events:
            self._apply_prob_event(agent_id, pe, agent_mask)
            result["changes"].append({
                "agent_id": agent_id, "layer": "prob",
                "event": pe,
            })

        # ---- Layer 3: LLM (only if needed) ----
        pending = self.tick_manager.pending_events.get(agent_id, [])
        if self._needs_llm(agent, pending, rule_actions, prob_events):
            # Build situation from pending events
            situation = self._build_situation(pending, prob_events)
            action_space = self._get_action_space(agent)

            llm_result = self.llm_engine.decide(
                persona_prompt=self._agent_to_persona(agent),
                situation=situation,
                action_space=action_space,
            )
            result["llm"] = 1
            result["llm_cost"] = llm_result.get("cost_usd", 0.0)
            result["changes"].append({
                "agent_id": agent_id, "layer": "llm",
                "decision": llm_result,
            })
            self.decision_log.append({
                "tick": self.tick_manager.current_tick,
                "agent_id": agent_id,
                "decision": llm_result,
            })

        return result

    def _apply_action(self, agent_id: str, action: dict,
                      mask: pd.Series):
        """Apply a rule engine action to the agent DataFrame."""
        if action["type"] == "field_change":
            field = action["field"]
            value = action["value"]
            if field in self.tick_manager.agents.columns:
                self.tick_manager.agents.loc[mask, field] = value

        elif action["type"] == "cpf_contribution":
            for f in ["cpf_oa", "cpf_sa", "cpf_ma"]:
                add_key = f"{f}_add"
                if add_key in action and f in self.tick_manager.agents.columns:
                    self.tick_manager.agents.loc[mask, f] += action[add_key]

    def _apply_prob_event(self, agent_id: str, event: dict,
                          mask: pd.Series):
        """Apply a probability-triggered event to agent state."""
        etype = event.get("event", "")

        if etype == "job_transition":
            if "job_status" in self.tick_manager.agents.columns:
                self.tick_manager.agents.loc[mask, "job_status"] = event["to"]

        elif etype == "marital_transition":
            if "marital_status" in self.tick_manager.agents.columns:
                self.tick_manager.agents.loc[mask, "marital_status"] = event["to"]

        elif etype == "health_transition":
            if "health_status" in self.tick_manager.agents.columns:
                self.tick_manager.agents.loc[mask, "health_status"] = event["to"]

        elif etype == "first_child" or etype == "additional_child":
            if "num_children" in self.tick_manager.agents.columns:
                self.tick_manager.agents.loc[mask, "num_children"] += 1

        elif etype == "death":
            if "is_alive" in self.tick_manager.agents.columns:
                self.tick_manager.agents.loc[mask, "is_alive"] = False

    def _needs_llm(self, agent: dict, pending_events: list,
                   rule_actions: list, prob_events: list) -> bool:
        """Determine if this agent needs LLM processing this tick."""
        # LLM needed when:
        # 1. Agent has external events to react to
        if pending_events:
            return True
        # 2. Major life events from probability layer
        major_events = {"first_child", "marital_transition", "job_transition"}
        for pe in prob_events:
            if pe.get("event") in major_events:
                return True
        # 3. Life phase transitions (from rule layer)
        for ra in rule_actions:
            if (ra.get("type") == "field_change"
                    and ra.get("field") == "life_phase"):
                return True
        return False

    def _build_situation(self, pending_events: list,
                         prob_events: list) -> str:
        """Build a situation description for LLM from events."""
        parts = []
        for e in pending_events:
            title = e.get("payload", {}).get("title", e.get("event_type", ""))
            parts.append(f"News: {title}")
        for pe in prob_events:
            parts.append(f"Life event: {pe.get('event', 'unknown')}")
        return "; ".join(parts) if parts else "Routine day, no special events."

    def _get_action_space(self, agent: dict) -> List[str]:
        """Get available actions based on agent's life phase."""
        phase = agent.get("life_phase", "establishment")
        base_actions = ["no_action", "save_more", "reduce_spending"]

        phase_actions = {
            "establishment": ["apply_bto", "change_job", "start_dating",
                              "buy_insurance", "invest"],
            "bearing": ["upgrade_housing", "apply_bto", "change_job",
                        "save_for_children", "buy_insurance"],
            "release": ["invest", "plan_retirement", "downsize_housing",
                        "volunteer"],
            "retirement_early": ["withdraw_cpf", "part_time_work",
                                 "medical_checkup", "travel"],
            "decline": ["medical_checkup", "adjust_living", "family_support"],
        }

        return base_actions + phase_actions.get(phase, [])

    def _agent_to_persona(self, agent: dict) -> str:
        """Convert agent dict to persona prompt string."""
        parts = [
            f"You are a {agent.get('age', 30)}-year-old "
            f"{agent.get('ethnicity', 'Chinese')} {agent.get('gender', 'M')}",
            f"living in {agent.get('planning_area', 'Bedok')}, Singapore.",
            f"Education: {agent.get('education_level', 'Secondary')}.",
        ]
        income = agent.get("monthly_income", 0)
        if income > 0:
            parts.append(f"Monthly income: ${income:,}.")
        parts.append(f"Housing: {agent.get('housing_type', 'HDB_4')}.")
        parts.append(f"Marital status: {agent.get('marital_status', 'Single')}.")
        if agent.get("num_children", 0) > 0:
            parts.append(f"Children: {agent['num_children']}.")
        parts.append(f"Life phase: {agent.get('life_phase', 'establishment')}.")
        if agent.get("industry"):
            parts.append(f"Industry: {agent['industry']}.")
        if agent.get("has_vehicle"):
            parts.append("Owns a vehicle.")
        return " ".join(parts)

    # ---- Time Travel ----

    def save_snapshot(self, metadata: Optional[dict] = None) -> str:
        """Manually save a snapshot at current tick."""
        return self.snapshot_mgr.save_snapshot(
            self.tick_manager.agents,
            self.tick_manager.current_tick,
            str(self.tick_manager.current_date),
            self.event_log,
            metadata=metadata,
        )

    def rollback(self, target_tick: int) -> bool:
        """
        Rollback simulation to target tick.

        Returns True if successful.
        """
        result = self.snapshot_mgr.rollback(target_tick)
        if result is None:
            return False

        # Restore state
        self.tick_manager.agents = result["agents_df"]
        self.tick_manager.current_tick = result["tick"]
        if result["sim_date"]:
            from datetime import date as dt_date
            parts = result["sim_date"].split("-")
            self.tick_manager.current_date = dt_date(
                int(parts[0]), int(parts[1]), int(parts[2]))
        self.event_log = result["event_log"]
        self.tick_manager.pending_events.clear()
        self.tick_manager.scheduled = {
            k: v for k, v in self.tick_manager.scheduled.items()
            if k > result["tick"]
        }

        logger.info(f"Rollback complete: now at tick {result['tick']} "
                    f"({result['sim_date']})")
        return True

    def list_snapshots(self) -> List[dict]:
        """List all available snapshots for time travel."""
        return self.snapshot_mgr.list_snapshots()

    # ---- Run ----

    def run(self, n_ticks: int = 1) -> List[dict]:
        """Run multiple ticks."""
        results = []
        for _ in range(n_ticks):
            result = self.run_tick()
            results.append(result)
        return results

    def get_stats(self) -> dict:
        """Get comprehensive simulation statistics."""
        return {
            "tick": self.tick_manager.get_tick_stats(),
            "llm": self.llm_engine.get_stats(),
            "collectors": self.collector_registry.get_stats(),
            "snapshots": self.snapshot_mgr.get_storage_stats(),
            "total_events_logged": len(self.event_log),
            "total_decisions_logged": len(self.decision_log),
        }
