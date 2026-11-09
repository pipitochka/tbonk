"""Per-process metrics: exactly one threaded Gunicorn worker per pod."""
import os

from prometheus_client import (
    CollectorRegistry, Counter, GCCollector, Histogram, PlatformCollector,
    ProcessCollector, start_http_server,
)

REGISTRY = CollectorRegistry()
GCCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)
ProcessCollector(registry=REGISTRY)

HTTP_REQUESTS = Counter("tbonk_http_requests_total", "Completed HTTP requests",
                        ["method", "route", "status_class"], registry=REGISTRY)
OPERATIONS = Counter("tbonk_task_operations_total", "Completed task API operations",
                     ["operation", "outcome"], registry=REGISTRY)
DURATION = Histogram("tbonk_task_operation_duration_seconds", "Task API latency",
                     ["operation", "outcome"], registry=REGISTRY,
                     buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5))
CREATED = Counter("tbonk_tasks_created_total", "Committed task creations", registry=REGISTRY)
UPDATED = Counter("tbonk_tasks_updated_total", "Committed task updates", registry=REGISTRY)
DELETED = Counter("tbonk_tasks_deleted_total", "Committed task deletions", registry=REGISTRY)
COMPLETED = Counter("tbonk_tasks_completed_total", "Committed entries into done status", registry=REGISTRY)

ENDPOINT_OPERATIONS = {
    "list_tasks": "list", "get_task": "read", "create_task": "create",
    "update_task": "update", "delete_task": "delete",
}
for operation in ENDPOINT_OPERATIONS.values():
    for outcome in ("success", "client_error", "server_error"):
        OPERATIONS.labels(operation, outcome)
        DURATION.labels(operation, outcome)


def observe_request(method, route, endpoint, status_code, duration):
    if route in ("/live", "/health"):
        return
    method = method if method in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS") else "OTHER"
    HTTP_REQUESTS.labels(method, route, f"{status_code // 100}xx").inc()
    operation = ENDPOINT_OPERATIONS.get(endpoint)
    if operation and method not in ("HEAD", "OPTIONS"):
        outcome = "server_error" if status_code >= 500 else (
            "client_error" if status_code >= 400 else "success"
        )
        OPERATIONS.labels(operation, outcome).inc()
        DURATION.labels(operation, outcome).observe(duration)


def start_metrics_server():
    return start_http_server(int(os.getenv("METRICS_PORT", "9100")), registry=REGISTRY)
