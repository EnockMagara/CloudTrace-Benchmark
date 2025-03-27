from src.benchmark import run_benchmark

def test_run_benchmark_mock():
    # Mock endpoints and traceroute results
    endpoints = {"test.com": "127.0.0.1"}
    results = run_benchmark(endpoints)
    assert "127.0.0.1" in results
    assert "hop_count" in results["127.0.0.1"]
