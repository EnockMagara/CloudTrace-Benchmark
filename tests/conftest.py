import pytest
from src.tracer import get_route

@pytest.fixture
def mock_traceroute(monkeypatch):
    def mock_get_route(hostname):
        return [{"ttl": 1, "ip": "127.0.0.1", "rtt": 10.0}]
    monkeypatch.setattr("src.tracer.get_route", mock_get_route)