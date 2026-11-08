from backend import prober


def test_probe_checks_full_scenario_and_cleans_up_on_failure(monkeypatch):
    calls = []

    def fake(base, method, path, payload=None):
        calls.append((method, path))
        if method == "POST":
            return 201, {"id": 7, "title": payload["title"]}
        if method == "GET":
            raise TimeoutError("read timed out")
        return 204, None

    monkeypatch.setattr(prober, "api", fake)
    assert not prober.run_once("http://test")
    assert calls == [("POST", "/api/tasks"), ("GET", "/api/tasks/7"), ("DELETE", "/api/tasks/7")]
    assert prober.REGISTRY.get_sample_value("tbonk_probe_success") == 0
