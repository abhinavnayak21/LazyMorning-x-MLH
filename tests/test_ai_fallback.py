from backend.app.utils.validators import validate_and_filter_tasks, parse_ai_briefing_response
from backend.app.services.briefing_service import BriefingService
from backend.app.services.ai_service import AIService
from backend.app.config import settings

def test_hallucination_validator_filters_fake_tasks():
    valid_titles = ["Finish project proposal", "Review client feedback"]
    extracted = ["Finish project proposal", "Fake hallucinated task 123", "Review client feedback"]

    approved = validate_and_filter_tasks(extracted, valid_titles)
    assert len(approved) == 2
    assert "Finish project proposal" in approved
    assert "Review client feedback" in approved
    assert "Fake hallucinated task 123" not in approved

def test_fallback_with_empty_database(db_session):
    # Tests that fallback generator produces a valid morning briefing even with 0 tasks and 0 notes
    context = BriefingService.collect_context(db_session)
    result = BriefingService.generate_fallback(context)

    assert result["todays_focus"] is not None
    assert isinstance(result["top_priorities"], list)
    assert isinstance(result["upcoming_deadlines"], list)
    assert isinstance(result["unfinished_items"], list)
    assert result["suggested_first_step"] is not None
    assert result["source"] == "fallback"

def test_cloudflare_tunnel_headers():
    # Test that Cloudflare Access headers are attached when configured
    settings.CF_ACCESS_CLIENT_ID = "test-client-id"
    settings.CF_ACCESS_CLIENT_SECRET = "test-client-secret"
    settings.CF_BEARER_TOKEN = "test-token"

    svc = AIService(provider="ollama", base_url="https://ollama.trycloudflare.com")
    headers = svc._get_cloudflare_headers()

    assert headers["CF-Access-Client-Id"] == "test-client-id"
    assert headers["CF-Access-Client-Secret"] == "test-client-secret"
    assert headers["Authorization"] == "Bearer test-token"

    # Reset
    settings.CF_ACCESS_CLIENT_ID = ""
    settings.CF_ACCESS_CLIENT_SECRET = ""
    settings.CF_BEARER_TOKEN = ""

def test_cloudflare_workers_ai_model_list():
    svc = AIService(provider="cloudflare_workers_ai")
    models = svc.list_models()
    assert "@cf/qwen/qwen2.5-7b-instruct" in models
