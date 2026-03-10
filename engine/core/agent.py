"""
Agent data model — the core entity of the simulation.
Each agent represents one synthetic person in the Singapore population.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Gender(str, Enum):
    M = "M"
    F = "F"


class Ethnicity(str, Enum):
    CHINESE = "Chinese"
    MALAY = "Malay"
    INDIAN = "Indian"
    OTHERS = "Others"


class ResidencyStatus(str, Enum):
    CITIZEN = "Citizen"
    PR = "PR"
    EP = "EP"
    SP = "SP"
    WP = "WP"
    FDW = "FDW"
    DP = "DP"
    STP = "STP"


class HousingType(str, Enum):
    HDB_1_2 = "HDB_1_2"
    HDB_3 = "HDB_3"
    HDB_4 = "HDB_4"
    HDB_5_EC = "HDB_5_EC"
    CONDO = "Condo"
    LANDED = "Landed"


class EducationLevel(str, Enum):
    NO_FORMAL = "No_Formal"
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    POST_SECONDARY = "Post_Secondary"  # ITE, A-Level
    POLYTECHNIC = "Polytechnic"
    UNIVERSITY = "University"
    POSTGRADUATE = "Postgraduate"


class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class HealthStatus(str, Enum):
    HEALTHY = "Healthy"
    CHRONIC_MILD = "Chronic_Mild"
    CHRONIC_SEVERE = "Chronic_Severe"
    DISABLED = "Disabled"


class NSStatus(str, Enum):
    NOT_APPLICABLE = "Not_Applicable"
    PRE_ENLISTMENT = "Pre_Enlistment"
    SERVING_NSF = "Serving_NSF"
    ACTIVE_NSMEN = "Active_NSmen"
    COMPLETED = "Completed"
    EXEMPT = "Exempt"


class LifePhase(str, Enum):
    DEPENDENCE = "dependence"
    GROWTH = "growth"
    ADOLESCENCE = "adolescence"
    NS_SERVICE = "ns_service"
    ESTABLISHMENT = "establishment"
    BEARING = "bearing"
    RELEASE = "release"
    RETIREMENT_EARLY = "retirement_early"
    DECLINE = "decline"
    END_OF_LIFE = "end_of_life"


class AgentType(str, Enum):
    PASSIVE = "passive"      # 0-14, follows parent
    SEMI_ACTIVE = "semi_active"  # 13-16, shared decisions
    ACTIVE = "active"        # 15+, independent decisions


@dataclass
class Agent:
    """A synthetic person in the Singapore Digital Twin."""

    # Identity
    id: str
    age: int
    gender: Gender
    ethnicity: Ethnicity
    residency_status: ResidencyStatus
    generation: str = "3rd+"           # 1st, 1.5, 2nd, 3rd+
    years_in_sg: int = 0              # for non-citizens
    religion: str = "None"
    primary_language: str = "English"

    # Education / Career
    education_level: EducationLevel = EducationLevel.SECONDARY
    occupation: str = ""               # SSOC code
    industry: str = ""                 # SSIC code
    employer_type: str = ""            # MNC/SME/Gov/StatBoard/Gig/Self
    monthly_income: int = 0

    # Family
    marital_status: MaritalStatus = MaritalStatus.SINGLE
    household_id: str = ""
    household_role: str = ""           # head/spouse/child/parent/helper
    num_children: int = 0

    # Housing / Finance
    planning_area: str = ""            # one of 55 areas
    housing_type: HousingType = HousingType.HDB_4
    housing_value: int = 0
    monthly_savings: int = 0
    total_debt: int = 0

    # CPF
    cpf_oa: int = 0
    cpf_sa: int = 0
    cpf_ma: int = 0
    cpf_ra: int = 0

    # Health
    health_status: HealthStatus = HealthStatus.HEALTHY
    chronic_conditions: list = field(default_factory=list)
    bmi_category: str = "normal"
    smoking: bool = False

    # NS
    ns_status: NSStatus = NSStatus.NOT_APPLICABLE

    # Transport
    commute_mode: str = "MRT"
    has_vehicle: bool = False

    # Personality (Layer A - stable)
    big5_o: float = 3.0  # Openness (1-5)
    big5_c: float = 3.0  # Conscientiousness
    big5_e: float = 3.0  # Extraversion
    big5_a: float = 3.0  # Agreeableness
    big5_n: float = 3.0  # Neuroticism

    # Attitudes (Layer B - medium stability)
    risk_appetite: float = 3.0       # 1-5
    political_leaning: float = 3.0   # 1=conservative, 5=progressive
    social_trust: float = 3.0        # 1-5
    religious_devotion: float = 3.0  # 1-5

    # Life state
    life_phase: LifePhase = LifePhase.ESTABLISHMENT
    agent_type: AgentType = AgentType.ACTIVE
    is_alive: bool = True

    def to_dict(self) -> dict:
        """Convert agent to dictionary for database storage."""
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                d[k] = v.value
            elif isinstance(v, list):
                d[k] = v
            else:
                d[k] = v
        return d

    def determine_life_phase(self) -> LifePhase:
        """Determine current life phase based on attributes."""
        if self.age <= 6:
            return LifePhase.DEPENDENCE
        elif self.age <= 12:
            return LifePhase.GROWTH
        elif self.age <= 16:
            return LifePhase.ADOLESCENCE
        elif (self.gender == Gender.M
              and self.residency_status in (ResidencyStatus.CITIZEN, ResidencyStatus.PR)
              and self.ns_status == NSStatus.SERVING_NSF):
            return LifePhase.NS_SERVICE
        elif self.age >= 85 or self.health_status == HealthStatus.DISABLED:
            return LifePhase.END_OF_LIFE
        elif self.age >= 75 or self.health_status == HealthStatus.CHRONIC_SEVERE:
            return LifePhase.DECLINE
        elif self.age >= 63:
            return LifePhase.RETIREMENT_EARLY
        elif self.age >= 51:
            return LifePhase.RELEASE
        elif self.age >= 36 or (self.num_children > 0 and self.age >= 30):
            return LifePhase.BEARING
        else:
            return LifePhase.ESTABLISHMENT

    def determine_agent_type(self) -> AgentType:
        """Determine agent type based on age."""
        if self.age < 13:
            return AgentType.PASSIVE
        elif self.age < 15:
            return AgentType.SEMI_ACTIVE
        else:
            return AgentType.ACTIVE

    def to_persona_prompt(self) -> str:
        """Generate a persona description for LLM prompting."""
        parts = []
        parts.append(f"You are a {self.age}-year-old {self.ethnicity.value} {self.gender.value}")
        parts.append(f"living in {self.planning_area}, Singapore.")
        parts.append(f"Residency: {self.residency_status.value}.")
        parts.append(f"Education: {self.education_level.value}.")
        if self.monthly_income > 0:
            parts.append(f"Monthly income: ${self.monthly_income:,}.")
        parts.append(f"Housing: {self.housing_type.value}.")
        parts.append(f"Marital status: {self.marital_status.value}.")
        if self.num_children > 0:
            parts.append(f"Children: {self.num_children}.")
        parts.append(f"Life phase: {self.life_phase.value}.")

        # Personality description
        traits = []
        if self.big5_o > 3.5:
            traits.append("open to new experiences")
        if self.big5_c > 3.5:
            traits.append("organized and disciplined")
        if self.big5_e > 3.5:
            traits.append("outgoing and sociable")
        elif self.big5_e < 2.5:
            traits.append("introverted and reserved")
        if self.big5_a > 3.5:
            traits.append("agreeable and cooperative")
        if self.big5_n > 3.5:
            traits.append("tends to worry and feel anxious")

        if traits:
            parts.append(f"Personality: {', '.join(traits)}.")

        if self.risk_appetite > 3.5:
            parts.append("Willing to take financial risks.")
        elif self.risk_appetite < 2.5:
            parts.append("Financially conservative.")

        return " ".join(parts)
