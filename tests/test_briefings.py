from backend.app.models.task import Task

def test_generate_briefing_and_verify_sections(client, db_session):
    # Add sample tasks
    db_session.add(Task(title="Finish project proposal", priority="High", due_date="Today, 5:00 PM"))
    db_session.add(Task(title="Review client feedback", priority="High", due_date="Today"))
    db_session.add(Task(title="Prepare meeting materials", priority="Medium", due_date="Tomorrow"))
    db_session.commit()

    # Generate briefing forcing fallback to test offline engine reliably
    res = client.post("/api/briefings/generate", json={"force_fallback": True})
    assert res.status_code == 201
    data = res.json()

    # Verify the 5 core sections required
    assert "todays_focus" in data and len(data["todays_focus"]) > 0
    assert "top_priorities" in data and len(data["top_priorities"]) > 0
    assert "upcoming_deadlines" in data and len(data["upcoming_deadlines"]) > 0
    assert "unfinished_items" in data and len(data["unfinished_items"]) > 0
    assert "suggested_first_step" in data and len(data["suggested_first_step"]) > 0

    assert data["source"] == "fallback"

    # Get latest briefing
    latest_res = client.get("/api/briefings/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == data["id"]

    # History list
    history_res = client.get("/api/briefings")
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1
