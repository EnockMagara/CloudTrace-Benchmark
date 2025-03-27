import os
import pytest
from src.tracer import get_route

@pytest.fixture
def mock_traceroute(monkeypatch):
    def mock_get_route(hostname):
        return [
            {"ttl": 1, "ip": "192.168.1.1", "rtt": 10.0},
            {"ttl": 2, "ip": "10.0.0.1", "rtt": 20.0}
        ]
    monkeypatch.setattr("src.tracer.get_route", mock_get_route)
# Skip test if not running as root
pytestmark = pytest.mark.skipif(os.geteuid() != 0, reason="Test requires root privileges")

def test_get_route(mock_traceroute):
    hops = get_route("test.com")
    assert len(hops) == 2
    assert hops[0]["ip"] == "192.168.1.1"
    assert hops[1]["rtt"] == 20.0
