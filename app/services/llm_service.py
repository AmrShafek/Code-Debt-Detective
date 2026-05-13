"""
LLM Service
Manages LLM configuration, providers, and API interactions for CrewAI agents
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """Manages LLM configuration and provider setup for CrewAI agents"""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.api_base = os.getenv("LLM_API_BASE", "")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    def get_llm_config(self) -> Dict[str, Any]:
        """Get the LLM configuration dict for CrewAI agents"""
        config = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.provider == "openai":
            config["model"] = self.model
            if self.api_key:
                config["api_key"] = self.api_key
            if self.api_base:
                config["api_base"] = self.api_base

        elif self.provider == "azure":
            config["model"] = self.model
            config["api_key"] = self.api_key
            config["api_base"] = self.api_base
            config["api_type"] = "azure"
            config["api_version"] = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")

        elif self.provider == "anthropic":
            config["model"] = self.model
            config["api_key"] = self.api_key

        elif self.provider == "ollama":
            config["model"] = self.model
            config["api_base"] = self.api_base or "http://localhost:11434"

        elif self.provider == "groq":
            config["model"] = self.model
            config["api_key"] = self.api_key
            config["api_base"] = "https://api.groq.com/openai/v1"

        elif self.provider == "local":
            config["model"] = self.model
            config["api_base"] = self.api_base or "http://localhost:1234/v1"

        return config

    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        if self.provider in ("ollama", "local"):
            return bool(self.api_base)
        return bool(self.api_key)

    def get_provider_name(self) -> str:
        return self.provider.upper()

    def get_model_name(self) -> str:
        return self.model
