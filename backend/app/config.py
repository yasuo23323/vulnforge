import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "VulnForge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    DATABASE_TYPE: str = "sqlite"

    DATABASE_URL: str = "sqlite+aiosqlite:///./vulnforge.db"
    POSTGRES_DATABASE_URL: str = "postgresql+asyncpg://vulnforge:vulnforge@localhost:5432/vulnforge"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # LLM Defaults
    LLM_DEFAULT_PROVIDER: str = "anthropic"
    LLM_DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    # Custom base URL for OpenAI-compatible providers (e.g., DeepSeek)
    OPENAI_BASE_URL: Optional[str] = None

    # Root directory (two levels up from backend/app/config.py)
    _ROOT_DIR: str = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

    SCANNER_TOOLS_DIR: str = ""

    @property
    def tools_dir(self) -> str:
        return self.SCANNER_TOOLS_DIR or os.path.join(self._ROOT_DIR, "tools")

    @property
    def SCANNER_NUCLEI_PATH(self) -> str:
        return "nuclei" if sys.platform != "win32" else os.path.join(self.tools_dir, "nuclei.exe")

    @property
    def SCANNER_SQLMAP_PATH(self) -> str:
        return "sqlmap"

    @property
    def SCANNER_DALFOX_PATH(self) -> str:
        return "dalfox" if sys.platform != "win32" else os.path.join(self.tools_dir, "dalfox.exe")

    @property
    def SCANNER_FFUF_PATH(self) -> str:
        return "ffuf" if sys.platform != "win32" else os.path.join(self.tools_dir, "ffuf.exe")

    DOCKER_SANDBOX_ENABLED: bool = False
    DOCKER_SANDBOX_NETWORK: str = "vulnforge_scan"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def effective_database_url(self) -> str:
        if self.DATABASE_TYPE == "postgres":
            return self.POSTGRES_DATABASE_URL
        return self.DATABASE_URL


settings = Settings()


