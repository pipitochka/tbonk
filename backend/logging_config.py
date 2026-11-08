"""One JSON object per line, including Gunicorn lifecycle messages."""
import json
import logging
import os
import sys
from datetime import datetime, timezone

from gunicorn.glogging import Logger


class JsonFormatter(logging.Formatter):
    def format(self, record):
        event = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service.name": os.getenv("SERVICE_NAME", "tbonk-tasks"),
            "logger": record.name,
        }
        event.update(getattr(record, "fields", {}))
        if record.exc_info:
            event["exception.type"] = record.exc_info[0].__name__
        return json.dumps(event, ensure_ascii=False)


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class JsonGunicornLogger(Logger):
    def setup(self, cfg):
        super().setup(cfg)
        for logger in (self.error_log, self.access_log):
            for handler in logger.handlers:
                handler.setFormatter(JsonFormatter())
                if isinstance(handler, logging.StreamHandler):
                    handler.setStream(sys.stdout)
