"""Shared configuration for Digital Twins Singapore."""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_REWARD_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_REWARD_MODEL = "nvidia/llama-3.1-nemotron-70b-reward"

# Fields to select for agent personas (avoid pulling huge text columns)
AGENT_FIELDS = (
    "agent_id,age,age_group,gender,ethnicity,planning_area,housing_type,"
    "education_level,monthly_income,marital_status,health_status,life_phase,"
    "residency_status,big5_o,big5_c,big5_e,big5_a,big5_n,risk_appetite,"
    "income_band,political_leaning,religious_devotion,social_trust"
)
