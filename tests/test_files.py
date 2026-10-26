from backend.app.models.imported_file import ImportedFile

def test_file_scan_and_approval_gate(client, db_session):
    # Trigger scan
    scan_res = client.post("/api/files/scan")
    assert scan_res.status_code == 200
    files = scan_res.json()
    assert len(files) >= 1

    file_id = files[0]["id"]
    initial_approved = files[0]["is_approved"]

    # Toggle approval
    toggle_res = client.patch(f"/api/files/{file_id}/approve", json={"is_approved": not initial_approved})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_approved"] == (not initial_approved)

def test_delete_file(client, db_session):
    # Add a mock file record
    record = ImportedFile(
        filename="dummy_test.txt",
        filepath="/tmp/dummy_test.txt",
        file_type="TXT",
        content_preview="preview",
        full_content="test body",
        is_approved=False
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    del_res = client.delete(f"/api/files/{record.id}")
    assert del_res.status_code == 204
