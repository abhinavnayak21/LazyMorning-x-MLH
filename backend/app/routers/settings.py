from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.settings import SettingsUpdate, SettingsResponse
from backend.app.services.ai_service import ai_service
from backend.app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])

def _get_status_message(is_connected: bool) -> str:
    if settings.AI_PROVIDER == "cloudflare_workers_ai":
        return f"Connected to Cloudflare Workers AI ({settings.CF_WORKERS_AI_MODEL})" if is_connected else "Cloudflare Workers AI offline (Local fallback active)"
    is_tunnel = "trycloudflare.com" in settings.OLLAMA_BASE_URL or "https://" in settings.OLLAMA_BASE_URL
    label = "Cloudflare Tunnel" if is_tunnel else "Local Ollama"
    return f"Connected to {label} ({settings.OLLAMA_MODEL})" if is_connected else f"{label} offline (Local fallback active)"

@router.get("", response_model=SettingsResponse)
def get_settings():
    is_connected = ai_service.is_available()
    msg = _get_status_message(is_connected)
    return SettingsResponse(
        briefing_time=settings.BRIEFING_TIME,
        timezone=settings.TIMEZONE,
        enable_schedule=settings.ENABLE_SCHEDULE,
        ai_provider=settings.AI_PROVIDER,
        ollama_model=settings.OLLAMA_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        cf_access_client_id=settings.CF_ACCESS_CLIENT_ID,
        cf_access_client_secret=settings.CF_ACCESS_CLIENT_SECRET,
        cf_bearer_token=settings.CF_BEARER_TOKEN,
        cf_account_id=settings.CF_ACCOUNT_ID,
        cf_workers_ai_model=settings.CF_WORKERS_AI_MODEL,
        is_connected=is_connected,
        status_message=msg
    )

@router.post("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate):
    settings.BRIEFING_TIME = payload.briefing_time
    settings.TIMEZONE = payload.timezone
    settings.ENABLE_SCHEDULE = payload.enable_schedule
    settings.AI_PROVIDER = payload.ai_provider
    settings.OLLAMA_MODEL = payload.ollama_model
    settings.OLLAMA_BASE_URL = payload.ollama_base_url
    settings.CF_ACCESS_CLIENT_ID = payload.cf_access_client_id or ""
    settings.CF_ACCESS_CLIENT_SECRET = payload.cf_access_client_secret or ""
    settings.CF_BEARER_TOKEN = payload.cf_bearer_token or ""
    settings.CF_ACCOUNT_ID = payload.cf_account_id or ""
    if payload.cf_api_token:
        settings.CF_API_TOKEN = payload.cf_api_token
    settings.CF_WORKERS_AI_MODEL = payload.cf_workers_ai_model or "@cf/qwen/qwen2.5-7b-instruct"

    ai_service.provider = payload.ai_provider
    ai_service.base_url = payload.ollama_base_url.rstrip("/")
    ai_service.model = payload.cf_workers_ai_model if payload.ai_provider == "cloudflare_workers_ai" else payload.ollama_model

    if payload.enable_schedule:
        scheduler_service.reschedule(payload.briefing_time)
        scheduler_service.resume()
    else:
        scheduler_service.pause()

    is_connected = ai_service.is_available()
    msg = _get_status_message(is_connected)

    return SettingsResponse(
        briefing_time=settings.BRIEFING_TIME,
        timezone=settings.TIMEZONE,
        enable_schedule=settings.ENABLE_SCHEDULE,
        ai_provider=settings.AI_PROVIDER,
        ollama_model=settings.OLLAMA_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        cf_access_client_id=settings.CF_ACCESS_CLIENT_ID,
        cf_access_client_secret=settings.CF_ACCESS_CLIENT_SECRET,
        cf_bearer_token=settings.CF_BEARER_TOKEN,
        cf_account_id=settings.CF_ACCOUNT_ID,
        cf_workers_ai_model=settings.CF_WORKERS_AI_MODEL,
        is_connected=is_connected,
        status_message=msg
    )

@router.post("/test-ollama")
def test_connection():
    is_connected = ai_service.is_available()
    models = ai_service.list_models() if is_connected else []
    target = settings.CF_WORKERS_AI_MODEL if settings.AI_PROVIDER == "cloudflare_workers_ai" else settings.OLLAMA_BASE_URL
    return {
        "connected": is_connected,
        "provider": settings.AI_PROVIDER,
        "target": target,
        "available_models": models,
        "message": "Successfully reached AI service via Cloudflare" if is_connected else "Endpoint not reachable. Local offline briefing engine will generate all briefings reliably."
    }
