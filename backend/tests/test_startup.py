"""Startup and input validation must not depend on a running database."""
import importlib

import pytest

import backend.app as application


def test_wsgi_import_does_not_initialize_database(monkeypatch):
    def forbidden():
        raise AssertionError("WSGI import must not connect to PostgreSQL")

    monkeypatch.setattr(application, "get_connection", forbidden)
    from backend import wsgi
    importlib.reload(wsgi)


@pytest.mark.parametrize("method, url", [("post", "/api/tasks"), ("put", "/api/tasks/1")])
def test_long_title_is_rejected_before_database_access(monkeypatch, method, url):
    def forbidden():
        raise AssertionError("Invalid input must not reach PostgreSQL")

    monkeypatch.setattr(application, "get_connection", forbidden)
    with application.app.test_client() as client:
        response = getattr(client, method)(url, json={"title": "я" * 161})
    assert response.status_code == 400
    assert "160" in response.json["error"]


def test_liveness_does_not_require_database(monkeypatch):
    def forbidden():
        raise AssertionError("Liveness must not depend on PostgreSQL")

    monkeypatch.setattr(application, "get_connection", forbidden)
    assert application.app.test_client().get("/live").status_code == 200
