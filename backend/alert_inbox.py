"""Local teaching receiver: actual Alertmanager webhooks, no external messaging."""
import threading
from collections import deque
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
notifications = deque(maxlen=100)
lock = threading.Lock()


@app.post("/alerts")
def receive():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("alerts"), list):
        return jsonify({"error": "Expected an Alertmanager webhook with alerts[]"}), 400
    event = {"received_at": datetime.now(timezone.utc).isoformat(), "payload": payload}
    with lock:
        notifications.appendleft(event)
    return jsonify({"received": True})


@app.get("/api/notifications")
def api_notifications():
    with lock:
        return jsonify(list(notifications))


@app.get("/")
def index():
    with lock:
        events = list(notifications)
    return render_template_string("""<!doctype html><html lang="ru"><meta charset="utf-8">
<meta http-equiv="refresh" content="10"><title>Tbonk — уведомления</title>
<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;background:#f4f6fa;color:#182334}
article{background:white;border:1px solid #dae0eb;border-radius:12px;padding:20px;margin:18px 0}
.firing{color:#b42318}.resolved{color:#067647}small{color:#526175}code{font-size:14px}</style>
<h1>Уведомления Tbonk</h1><p>Реальные webhook-сообщения от Alertmanager. Обновление каждые 10 секунд.</p>
{% for event in events %}<article><small>Получено: {{ event.received_at }}</small>
<h2 class="{{ event.payload.status }}">{{ event.payload.status }}</h2>
{% for alert in event.payload.alerts %}<h3>{{ alert.labels.alertname }}</h3>
<p>{{ alert.annotations.summary }}</p><p>{{ alert.annotations.description }}</p>
<p><code>{{ alert.labels }}</code></p><small>Начало: {{ alert.startsAt }} · Конец: {{ alert.endsAt }}</small>
{% endfor %}</article>{% else %}<p>Уведомлений пока нет.</p>{% endfor %}</html>""", events=events)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
