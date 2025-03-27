import os
import pytest
from src.tracer import get_route

def test_get_route(mock_traceroute):
    hops = get_route("test.com")
    assert len(hops) == 2
    assert hops[0]["ip"] == "192.168.1.1"
    assert hops[1]["rtt"] == 20.0
