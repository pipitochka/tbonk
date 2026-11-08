import os

bind = f"0.0.0.0:{int(os.getenv('PORT', '8000'))}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
# Flask emits one structured access event, so don't duplicate access logs.
accesslog = None
errorlog = "-"
logger_class = "backend.logging_config.JsonGunicornLogger"
