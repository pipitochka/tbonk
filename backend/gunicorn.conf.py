import os

bind = f"0.0.0.0:{int(os.getenv('PORT', '8000'))}"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
if workers != 1:
    raise RuntimeError("Metrics require WEB_CONCURRENCY=1; scale Kubernetes pods instead")
worker_class = "gthread"
threads = 4
# Flask emits one structured access event, so don't duplicate access logs.
accesslog = None
errorlog = "-"
logger_class = "backend.logging_config.JsonGunicornLogger"


def post_worker_init(worker):
    from backend.metrics import start_metrics_server
    start_metrics_server()
