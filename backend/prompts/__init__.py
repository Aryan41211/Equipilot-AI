# EquiPilot AI - Backend Prompts Package
# LLM prompt templates

from backend.prompts.router_prompts import ROUTER_SYSTEM_PROMPT, ROUTER_CLASSIFICATION_PROMPT
from backend.prompts.synthesis_prompts import REPORT_SYSTEM_PROMPT, REPORT_GENERATION_PROMPT
from backend.prompts.sentiment_prompts import SENTIMENT_SYSTEM_PROMPT, SENTIMENT_ANALYSIS_PROMPT

__all__ = [
    "ROUTER_SYSTEM_PROMPT",
    "ROUTER_CLASSIFICATION_PROMPT",
    "REPORT_SYSTEM_PROMPT",
    "REPORT_GENERATION_PROMPT",
    "SENTIMENT_SYSTEM_PROMPT",
    "SENTIMENT_ANALYSIS_PROMPT",
]