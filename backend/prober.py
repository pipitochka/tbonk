"""Synthetic create -> read -> update -> delete, with best-effort cleanup."""
import json
import logging
import os
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, start_http_server

from backend.logging_config import configure_logging

REGISTRY = CollectorRegistry()
SUCCESS = Gauge("tbonk_probe_success", "Last full CRUD probe result", registry=REGISTRY)
RUNS = Counter("tbonk_probe_runs_total", "Completed synthetic scenarios", ["outcome"], registry=REGISTRY)
DURATION = Histogram("tbonk_probe_duration_seconds", "Full CRUD probe duration", registry=REGISTRY)
LAST_RUN = Gauge("tbonk_probe_last_run_timestamp_seconds", "Time of last completed probe", registry=REGISTRY)
for outcome in ("success", "failure"):
    RUNS.labels(outcome)
logger = logging.getLogger("tbonk.prober")


def api(base_url, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(base_url + path, data=data, method=method,
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else None


def run_once(base_url):
    started = time.perf_counter()
    task_id = None
    ok = False
    try:
        title = "synthetic-probe-" + uuid.uuid4().hex
        status, task = api(base_url, "POST", "/api/tasks", {"title": title})
        if status != 201 or task["title"] != title:
            raise ValueError("Create response mismatch")
        task_id = task["id"]
        status, fetched = api(base_url, "GET", f"/api/tasks/{task_id}")
        if status != 200 or fetched["title"] != title:
            raise ValueError("Read response mismatch")
        status, updated = api(base_url, "PUT", f"/api/tasks/{task_id}", {"title": title, "status": "done"})
        if status != 200 or updated["status"] != "done":
            raise ValueError("Update response mismatch")
        status, _ = api(base_url, "DELETE", f"/api/tasks/{task_id}")
        if status != 204:
            raise ValueError("Delete response mismatch")
        task_id = None
        ok = True
    except Exception as error:
        logger.warning("Synthetic scenario failed", extra={"fields": {"exception.type": type(error).__name__}})
    finally:
        if task_id is not None:
            # Delete only the task created by this run, never other users' data.
            try:
                api(base_url, "DELETE", f"/api/tasks/{task_id}")
            except HTTPError as error:
                if error.code != 404:
                    logger.warning("Probe cleanup failed", extra={"fields": {"task_id": task_id}})
            except Exception:
                logger.warning("Probe cleanup failed", extra={"fields": {"task_id": task_id}})
        SUCCESS.set(int(ok))
        RUNS.labels("success" if ok else "failure").inc()
        DURATION.observe(time.perf_counter() - started)
        LAST_RUN.set(time.time())
    return ok


def main():
    configure_logging()
    base_url = os.getenv("PROBE_URL", "http://tbonk.tbonk.svc.cluster.local:8000").rstrip("/")
    interval = float(os.getenv("PROBE_INTERVAL_SECONDS", "15"))
    if interval < 1:
        raise ValueError("Probe interval must be >= 1 second")
    start_http_server(int(os.getenv("METRICS_PORT", "9115")), registry=REGISTRY)
    while True:
        started = time.monotonic()
        run_once(base_url)
        time.sleep(max(0, interval - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
