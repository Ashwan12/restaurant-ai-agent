import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    """Central configuration for Restaurant Support & Operations Agent."""
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Database
    DATABASE_PATH: str = str(BASE_DIR / os.getenv("DATABASE_PATH", "restaurant.db"))

    # RAG & Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.50"))
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))

    # Agent Limits & Guardrails
    MAX_AGENT_ITERATIONS: int = int(os.getenv("MAX_AGENT_ITERATIONS", "5"))
    ENABLE_PROMPT_INJECTION_SHIELD: bool = os.getenv("ENABLE_PROMPT_INJECTION_SHIELD", "True").lower() in ("true", "1", "yes")
    ENABLE_AUTHORIZATION_CHECKS: bool = os.getenv("ENABLE_AUTHORIZATION_CHECKS", "True").lower() in ("true", "1", "yes")

    # Simulated API Failure Flags (for testing failure handling)
    SIMULATE_ORDER_API_FAILURE: bool = os.getenv("SIMULATE_ORDER_API_FAILURE", "False").lower() in ("true", "1", "yes")
    ORDER_API_TIMEOUT_SECONDS: float = float(os.getenv("ORDER_API_TIMEOUT_SECONDS", "5.0"))

settings = Settings()

