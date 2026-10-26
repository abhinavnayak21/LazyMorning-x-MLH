def test_create_and_list_tasks(client):
    res = client.post("/api/tasks", json={
        "title": "Finalize quarterly pitch",
        "description": "Prepare 5 slides",
        "priority": "High",
        "due_date": "Today, 5:00 PM"
    })
    assert res.status_code == 201
    task_id = res.json()["id"]

    # List tasks
    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    assert any(t["id"] == task_id for t in list_res.json())

def test_toggle_task_completion(client):
    res = client.post("/api/tasks", json={"title": "Check emails", "priority": "Low"})
    task_id = res.json()["id"]
    assert res.json()["is_done"] is False

    # Toggle to done
    toggle_res = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_done"] is True

    # Filter by completed
    comp_res = client.get("/api/tasks?status_filter=completed")
    assert any(t["id"] == task_id for t in comp_res.json())

    # Filter by pending
    pend_res = client.get("/api/tasks?status_filter=pending")
    assert not any(t["id"] == task_id for t in pend_res.json())
