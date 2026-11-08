from backend.alert_inbox import app, notifications


def test_webhook_is_visible_as_a_notification_and_html_is_escaped():
    notifications.clear()
    client = app.test_client()
    payload = {"status": "firing", "alerts": [{
        "labels": {"alertname": "HighPythonMemory"},
        "annotations": {"summary": "<script>alert(1)</script>", "description": "Memory high"},
        "startsAt": "2026-11-08T00:00:00Z", "endsAt": "0001-01-01T00:00:00Z",
    }]}
    assert client.post("/alerts", json=payload).status_code == 200
    assert client.get("/api/notifications").json[0]["payload"] == payload
    assert "&lt;script&gt;" in client.get("/").text
    assert client.post("/alerts", json=[]).status_code == 400
