from typing import Optional
from pydantic import BaseModel

class SettingsUpdate(BaseModel):
    briefing_time: str = "06:30"
    timezone: str = "Asia/Kolkata"
    enable_schedule: bool = True
    ai_provider: str = "ollama"  # "ollama" (Local/Tunnel) or "cloudflare_workers_ai"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    cf_access_client_id: Optional[str] = ""
    cf_access_client_secret: Optional[str] = ""
    cf_bearer_token: Optional[str] = ""
    cf_account_id: Optional[str] = ""
    cf_api_token: Optional[str] = ""
    cf_workers_ai_model: Optional[str] = "@cf/qwen/qwen2.5-7b-instruct"

class SettingsResponse(BaseModel):
    briefing_time: str
    timezone: str
    enable_schedule: bool
    ai_provider: str
    ollama_model: str
    ollama_base_url: str
    cf_access_client_id: Optional[str] = ""
    cf_access_client_secret: Optional[str] = ""
    cf_bearer_token: Optional[str] = ""
    cf_account_id: Optional[str] = ""
    cf_workers_ai_model: Optional[str] = "@cf/qwen/qwen2.5-7b-instruct"
    is_connected: bool
    status_message: str
