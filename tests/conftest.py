import pytest
from src.tracer import get_route

@pytest.fixture
def mock_traceroute(monkeypatch):
    def mock_get_route(hostname):
        return [
            {"ttl": 1, "ip": "192.168.1.1", "rtt": 10.0, "status": "success", "attempt": 1, "location": None},
            {"ttl": 2, "ip": "10.0.0.1", "rtt": 20.0, "status": "success", "attempt": 1, "location": None}
        ]
    monkeypatch.setattr("tests.test_tracer.get_route", mock_get_route)