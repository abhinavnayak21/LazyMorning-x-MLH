import os
from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
IMPORTS_DIR = BASE_DIR / "imports"
FRONTEND_ASSETS_DIR = BASE_DIR / "frontend" / "assets"

DATA_DIR.mkdir(parents=True, exist_ok=True)
IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Settings:
    PROJECT_NAME: str = "LazyMorning"
    PROJECT_TAGLINE: str = "Your Overnight Life Assistant"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'lazymorning.db'}")

    # AI Provider: 'ollama' (Local or Cloudflare Tunnel) or 'cloudflare_workers_ai'
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")

    # Ollama / Cloudflare Tunnel Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # Cloudflare Access / Tunnel Auth (optional for protected tunnels)
    CF_ACCESS_CLIENT_ID: str = os.getenv("CF_ACCESS_CLIENT_ID", "")
    CF_ACCESS_CLIENT_SECRET: str = os.getenv("CF_ACCESS_CLIENT_SECRET", "")
    CF_BEARER_TOKEN: str = os.getenv("CF_BEARER_TOKEN", "")

    # Cloudflare Workers AI Settings (Serverless open-weight models)
    CF_ACCOUNT_ID: str = os.getenv("CF_ACCOUNT_ID", "")
    CF_API_TOKEN: str = os.getenv("CF_API_TOKEN", "")
    CF_WORKERS_AI_MODEL: str = os.getenv("CF_WORKERS_AI_MODEL", "@cf/qwen/qwen2.5-7b-instruct")

    # Scheduler Settings
    BRIEFING_TIME: str = os.getenv("BRIEFING_TIME", "06:30")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    ENABLE_SCHEDULE: bool = os.getenv("ENABLE_SCHEDULE", "true").lower() in ("true", "1", "yes")

    DATA_DIR: Path = DATA_DIR
    IMPORTS_DIR: Path = IMPORTS_DIR

settings = Settings()
