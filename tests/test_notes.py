def test_create_and_list_note(client):
    res = client.post("/api/notes", json={
        "title": "Deep Work Morning",
        "content": "Focus on the core algorithm before reading emails.",
        "category": "Work",
        "tags": "Work, Focus"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Deep Work Morning"
    assert data["id"] is not None

    # List notes
    list_res = client.get("/api/notes")
    assert list_res.status_code == 200
    notes = list_res.json()
    assert len(notes) >= 1
    assert any(n["title"] == "Deep Work Morning" for n in notes)

def test_filter_notes_by_category(client):
    client.post("/api/notes", json={"title": "N1", "content": "C1", "category": "Personal"})
    client.post("/api/notes", json={"title": "N2", "content": "C2", "category": "Work"})

    res = client.get("/api/notes?category=Personal")
    assert res.status_code == 200
    notes = res.json()
    assert all(n["category"] == "Personal" for n in notes)

def test_update_and_delete_note(client):
    create_res = client.post("/api/notes", json={"title": "Temp", "content": "Body"})
    note_id = create_res.json()["id"]

    # Update
    update_res = client.put(f"/api/notes/{note_id}", json={"title": "Updated Title"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"

    # Delete
    del_res = client.delete(f"/api/notes/{note_id}")
    assert del_res.status_code == 204

    # Verify not found
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 404
