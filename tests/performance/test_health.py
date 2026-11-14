from time import perf_counter
from apps.api.main import create_app
from fastapi.testclient import TestClient


def test_health_smoke_latency(runtime):
    with TestClient(create_app(runtime.settings, runtime=runtime)) as client:
        start = perf_counter()
        assert all(client.get('/health').status_code == 200 for _ in range(20))
        assert perf_counter() - start < 20
