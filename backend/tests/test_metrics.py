import psycopg
from prometheus_client.openmetrics.exposition import generate_latest

import backend.app as application
from backend.metrics import REGISTRY


def test_database_failure_is_an_operation_error_not_success(monkeypatch):
    def fail():
        raise psycopg.OperationalError("test connection failure")

    monkeypatch.setattr(application, "get_connection", fail)
    labels = {"operation": "create", "outcome": "server_error"}
    before = REGISTRY.get_sample_value("tbonk_task_operations_total", labels)
    created_before = REGISTRY.get_sample_value("tbonk_tasks_created_total")
    response = application.app.test_client().post("/api/tasks", json={"title": "test"})
    assert response.status_code == 503
    assert REGISTRY.get_sample_value("tbonk_task_operations_total", labels) == before + 1
    assert REGISTRY.get_sample_value("tbonk_tasks_created_total") == created_before


def test_openmetrics_and_runtime_collectors():
    body = generate_latest(REGISTRY).decode()
    assert body.endswith("# EOF\n")
    assert "python_gc_objects_collected_total" in body
    assert "python_info" in body
    assert 'tbonk_task_operation_duration_seconds_bucket{le="0.5"' in body
    assert application.app.test_client().get("/metrics").status_code == 404
