import json
import logging

from backend.app import app
from backend.logging_config import JsonFormatter


def test_log_is_single_json_line_with_required_fields():
    record = logging.LogRecord("test", logging.ERROR, __file__, 1, "line one\nline two", (), None)
    record.fields = {"request_id": "abc", "http.status_code": 503}
    line = JsonFormatter().format(record)
    assert len(line.splitlines()) == 1
    event = json.loads(line)
    assert {"timestamp", "level", "message", "service.name"} <= event.keys()
    assert event["level"] == "error"
    assert event["http.status_code"] == 503


def test_request_log_uses_route_template_and_omits_payload(caplog):
    with caplog.at_level(logging.WARNING, logger="tbonk"):
        response = app.test_client().put("/api/tasks/123", json={"title": "secret" * 100})
    record = next(record for record in caplog.records if record.name == "tbonk")
    event = json.loads(JsonFormatter().format(record))
    assert event["http.route"] == "/api/tasks/<int:task_id>"
    assert event["request_id"] == response.headers["X-Request-ID"]
    assert "secret" not in json.dumps(event)
