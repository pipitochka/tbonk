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
CPU_SECONDS = float(os.getenv("DEMO_CPU_SECONDS", "0")) if os.getenv("DEMO_MODE", "false").lower() == "true" else 0
if not 0 <= CPU_SECONDS <= 0.5:
    raise ValueError("DEMO_CPU_SECONDS must be 0..0.5")
_memory = None


def initialize_runtime_demo():
    global _memory
    if os.getenv("DEMO_MODE", "false").lower() != "true":
        return
    size_mb = int(os.getenv("DEMO_MEMORY_MB", "0"))
    if not 0 <= size_mb <= 128:
        raise ValueError("DEMO_MEMORY_MB must be 0..128")
    _memory = bytearray(size_mb * 1024 * 1024)
    # Touch each page so RSS, not only virtual address space, actually grows.
    for offset in range(0, len(_memory), 4096):
        _memory[offset] = 1


def inject_fault():
    deadline = time.perf_counter() + CPU_SECONDS
    while time.perf_counter() < deadline:
        pass
    if DELAY:
        time.sleep(DELAY)
    if ERROR_EVERY and next(REQUESTS) % ERROR_EVERY == 0:
        return jsonify({"error": "Учебный режим: искусственная ошибка сервиса"}), 503
    return None
