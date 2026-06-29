import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "VulnForge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    DATABASE_TYPE: str = "sqlite"
    DATABASE_URL: str = "sqlite+aiosqlite:///./vulnforge.db"
    POSTGRES_DATABASE_URL: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    ANTHROPIC_API_KEY: str = ""
    LLM_DEFAULT_PROVIDER: str = "openai"
    LLM_DEFAULT_MODEL: str = "deepseek-chat"

    SCANNER_NUCLEI_PATH: str = "nuclei"
    SCANNER_DALFOX_PATH: str = "dalfox"
    SCANNER_FFUF_PATH: str = "ffuf"
    SCANNER_SQLMAP_PATH: str = "sqlmap"
    SCANNER_TOOLS_DIR: str = "/usr/local/bin"

    DOCKER_SANDBOX_ENABLED: bool = True
    DOCKER_SANDBOX_NETWORK: str = "host"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
