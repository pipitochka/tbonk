import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder="frontend", static_url_path="")


def database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://tbonk:tbonk@localhost:5432/tbonk",
    )


def get_connection():
    return psycopg.connect(database_url())


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(160) NOT NULL CHECK (char_length(trim(title)) > 0),
                description TEXT NOT NULL DEFAULT '',
                status VARCHAR(20) NOT NULL DEFAULT 'todo'
                    CHECK (status IN ('todo', 'in_progress', 'done')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


def serialize_task(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "status": row[3],
        "created_at": row[4].isoformat(),
        "updated_at": row[5].isoformat(),
    }


def find_task(task_id: int):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, title, description, status, created_at, updated_at "
            "FROM tasks WHERE id = %s",
            (task_id,),
        ).fetchone()


@app.get("/health")
def health():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
        return jsonify({"status": "ok", "database": "ok"})
    except psycopg.Error:
        return jsonify({"status": "error", "database": "unavailable"}), 503


@app.get("/api/tasks")
def list_tasks():
    status = request.args.get("status")
    query = (
        "SELECT id, title, description, status, created_at, updated_at "
        "FROM tasks"
    )
    params = ()
    if status:
        query += " WHERE status = %s"
        params = (status,)
    query += " ORDER BY created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return jsonify([serialize_task(row) for row in rows])


@app.get("/api/tasks/<int:task_id>")
def get_task(task_id: int):
    row = find_task(task_id)
    if row is None:
        return jsonify({"error": "Задача не найдена"}), 404
    return jsonify(serialize_task(row))


@app.post("/api/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    status = payload.get("status", "todo")
    if not title:
        return jsonify({"error": "Название задачи обязательно"}), 400
    if status not in ("todo", "in_progress", "done"):
        return jsonify({"error": "Недопустимый статус"}), 400
    with get_connection() as connection:
        row = connection.execute(
            "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s) "
            "RETURNING id, title, description, status, created_at, updated_at",
            (title, description, status),
        ).fetchone()
    return jsonify(serialize_task(row)), 201


@app.put("/api/tasks/<int:task_id>")
def update_task(task_id: int):
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    status = payload.get("status", "todo")
    if not title:
        return jsonify({"error": "Название задачи обязательно"}), 400
    if status not in ("todo", "in_progress", "done"):
        return jsonify({"error": "Недопустимый статус"}), 400
    with get_connection() as connection:
        row = connection.execute(
            "UPDATE tasks SET title = %s, description = %s, status = %s, "
            "updated_at = NOW() WHERE id = %s "
            "RETURNING id, title, description, status, created_at, updated_at",
            (title, description, status, task_id),
        ).fetchone()
    if row is None:
        return jsonify({"error": "Задача не найдена"}), 404
    return jsonify(serialize_task(row))


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id: int):
    with get_connection() as connection:
        result = connection.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    if result.rowcount == 0:
        return jsonify({"error": "Задача не найдена"}), 404
    return "", 204


@app.errorhandler(psycopg.Error)
def database_error(_error):
    return jsonify({"error": "Ошибка подключения к базе данных"}), 503


@app.get("/")
def index():
    return send_from_directory(BASE_DIR / "frontend", "index.html")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
