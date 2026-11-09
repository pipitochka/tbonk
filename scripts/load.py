"""Small bounded demo traffic; each worker deletes only its own created task."""
import argparse
import concurrent.futures
import json
import time
from urllib.request import Request, urlopen


def call(base, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    with urlopen(Request(base + path, data=data, method=method,
                         headers={"Content-Type": "application/json"}), timeout=10) as response:
        body = response.read()
        return json.loads(body) if body else None


def worker(base, deadline):
    success = failure = 0
    while time.monotonic() < deadline:
        task_id = None
        try:
            call(base, "GET", "/api/tasks")
            task_id = call(base, "POST", "/api/tasks", {"title": "load-demo"})["id"]
            call(base, "PUT", f"/api/tasks/{task_id}", {"title": "load-demo", "status": "done"})
            success += 1
        except Exception:
            failure += 1
        finally:
            if task_id is not None:
                for attempt in range(3):
                    try:
                        call(base, "DELETE", f"/api/tasks/{task_id}")
                        break
                    except Exception:
                        time.sleep(0.1)
                else:
                    print(f"Cleanup incomplete: task {task_id}", flush=True)
        time.sleep(0.1)
    return success, failure


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600 or not 1 <= args.workers <= 8:
        parser.error("seconds must be 1..3600 and workers 1..8")
    deadline = time.monotonic() + args.seconds
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda _: worker(args.url.rstrip('/'), deadline), range(args.workers)))
    print({"successful_cycles": sum(x[0] for x in results), "failed_cycles": sum(x[1] for x in results)})
