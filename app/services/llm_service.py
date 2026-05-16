"""
LLM Service
Manages per-agent LLM configuration for CrewAI agents
Supports different models/providers for different agents
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()


class LLMService:
    """Manages per-agent LLM configuration for CrewAI agents"""

    def __init__(self):
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    def get_code_analyzer_llm(self) -> Optional[LLM]:
        """LLM for Code Analyzer Agent -> Qwen Coder via OpenRouter"""
        model = os.getenv("CODE_ANALYZER_LLM_MODEL", "qwen/qwen3-coder-next")
        api_key = os.getenv("CODE_ANALYZER_API_KEY", "")
        base_url = os.getenv("CODE_ANALYZER_API_BASE", "https://openrouter.ai/api/v1")
        return self._build_llm(model, api_key, base_url, provider="openrouter")

    def get_refactor_llm(self) -> Optional[LLM]:
        """LLM for Strategist, Risk Assessor, Diff Explainer -> DeepSeek via OpenRouter"""
        model = os.getenv("REFACTOR_LLM_MODEL", "deepseek/deepseek-chat")
        api_key = os.getenv("REFACTOR_API_KEY", "")
        base_url = os.getenv("REFACTOR_API_BASE", "https://openrouter.ai/api/v1")
        return self._build_llm(model, api_key, base_url, provider="openrouter")

    def _build_llm(self, model: str, api_key: str, base_url: str, provider: Optional[str] = None) -> Optional[LLM]:
        """Build a CrewAI LLM object"""
        if not api_key:
            return None
        return LLM(
            model=model,
            api_key=api_key,
            base_url=base_url,
            provider=provider,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def get_code_analyzer_config(self) -> Dict[str, Any]:
        """Return config dict for display purposes"""
        return {
            "model": os.getenv("CODE_ANALYZER_LLM_MODEL", "qwen/qwen3-coder-next"),
            "base_url": os.getenv("CODE_ANALYZER_API_BASE", "https://openrouter.ai/api/v1"),
        }

    def get_refactor_config(self) -> Dict[str, Any]:
        return {
            "model": os.getenv("REFACTOR_LLM_MODEL", "deepseek-chat"),
            "base_url": os.getenv("REFACTOR_API_BASE", "https://api.deepseek.com/v1"),
        }

    def is_code_analyzer_configured(self) -> bool:
        return bool(os.getenv("CODE_ANALYZER_API_KEY"))

    def is_refactor_configured(self) -> bool:
        return bool(os.getenv("REFACTOR_API_KEY"))
