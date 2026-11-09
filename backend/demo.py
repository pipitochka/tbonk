"""Opt-in fault injection for a local teaching cluster; no control HTTP API."""
import itertools
import os
import time

from flask import jsonify


def settings():
    if os.getenv("DEMO_MODE", "false").lower() != "true":
        return 0.0, 0
    delay = float(os.getenv("DEMO_DELAY_SECONDS", "0"))
    every = int(os.getenv("DEMO_ERROR_EVERY", "0"))
    if not 0 <= delay <= 5 or every < 0:
        raise ValueError("Demo delay must be 0..5 seconds; error interval must be >= 0")
    return delay, every


DELAY, ERROR_EVERY = settings()
REQUESTS = itertools.count(1)


def inject_fault():
    if DELAY:
        time.sleep(DELAY)
    if ERROR_EVERY and next(REQUESTS) % ERROR_EVERY == 0:
        return jsonify({"error": "Учебный режим: искусственная ошибка сервиса"}), 503
    return None
