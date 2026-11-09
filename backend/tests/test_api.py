import os

import psycopg
import pytest

from backend.app import app, init_db


DATABASE_URL = os.getenv("DATABASE_URL", "")


@pytest.fixture(scope="session", autouse=True)
def database():
    init_db()
    yield
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("TRUNCATE TABLE tasks RESTART IDENTITY")


@pytest.fixture(autouse=True)
def clean_tasks():
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("TRUNCATE TABLE tasks RESTART IDENTITY")


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_health_reports_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok", "database": "ok"}


def test_task_crud_flow(client):
    created = client.post(
        "/api/tasks",
        json={"title": "Подготовить PR", "description": "Добавить CI"},
    )
    assert created.status_code == 201
    task_id = created.json["id"]
    assert created.json["status"] == "todo"

    fetched = client.get(f"/api/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json["title"] == "Подготовить PR"

    updated = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Подготовить PR",
            "description": "CI готов",
            "status": "done",
        },
    )
    assert updated.status_code == 200
    assert updated.json["status"] == "done"

    filtered = client.get("/api/tasks?status=done")
    assert filtered.status_code == 200
    assert [task["id"] for task in filtered.json] == [task_id]

    deleted = client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


@pytest.mark.parametrize(
    "payload, error",
    [
        ({"title": ""}, "Название задачи обязательно"),
        ({"title": "Задача", "status": "unknown"}, "Недопустимый статус"),
    ],
)
def test_validation_errors(client, payload, error):
    response = client.post("/api/tasks", json=payload)

    assert response.status_code == 400
    assert response.json["error"] == error


def test_missing_task_returns_not_found(client):
    assert client.get("/api/tasks/999999").status_code == 404
    assert client.delete("/api/tasks/999999").status_code == 404


def test_title_length_boundary_for_create_and_update(client):
    created = client.post("/api/tasks", json={"title": "я" * 160})
    assert created.status_code == 201
    task_id = created.json["id"]
    assert client.put(f"/api/tasks/{task_id}", json={"title": "ю" * 160}).status_code == 200
    for method, url in [(client.post, "/api/tasks"), (client.put, f"/api/tasks/{task_id}")]:
        response = method(url, json={"title": "я" * 161})
        assert response.status_code == 400
        assert response.json["error"] == "Название задачи должно быть не длиннее 160 символов"
    assert client.get(f"/api/tasks/{task_id}").json["title"] == "ю" * 160
