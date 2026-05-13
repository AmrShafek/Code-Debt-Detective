"""
Global application settings loaded from environment
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Code Debt Detective"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    REPOS_BASE_DIR: Path = Path(os.getenv("REPOS_BASE_DIR", "repos/scanned_projects"))
    SESSIONS_DIR: Path = Path(os.getenv("SESSIONS_DIR", "app/memory/sessions"))
    VECTOR_STORE_DIR: Path = Path(os.getenv("VECTOR_STORE_DIR", "app/memory/vector_store"))
    SUMMARIES_DIR: Path = Path(os.getenv("SUMMARIES_DIR", "app/memory/summaries"))

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    ANALYSIS_MAX_FILES: int = int(os.getenv("ANALYSIS_MAX_FILES", "5000"))
    ANALYSIS_MAX_LINES: int = int(os.getenv("ANALYSIS_MAX_LINES", "10000"))
    GIT_MAX_COMMITS: int = int(os.getenv("GIT_MAX_COMMITS", "100"))

    STREAMLIT_THEME: str = os.getenv("STREAMLIT_THEME", "dark")
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.REPOS_BASE_DIR, cls.SESSIONS_DIR, cls.VECTOR_STORE_DIR, cls.SUMMARIES_DIR]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
