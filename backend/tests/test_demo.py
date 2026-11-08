import itertools

from backend import demo
from backend.app import app


def test_demo_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("DEMO_DELAY_SECONDS", "5")
    monkeypatch.setenv("DEMO_ERROR_EVERY", "1")
    assert demo.settings() == (0.0, 0)


def test_injected_failures_do_not_break_health_checks(monkeypatch):
    monkeypatch.setattr(demo, "ERROR_EVERY", 1)
    monkeypatch.setattr(demo, "REQUESTS", itertools.count(1))
    with app.test_client() as client:
        assert client.get("/api/tasks").status_code == 503
        assert client.get("/live").status_code == 200
