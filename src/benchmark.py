from src.tracer import get_route
from src.geo import GeoLocator
import concurrent.futures
import time
import json

def process_endpoint(name, host, geolocator):
    """Process a single endpoint in parallel"""
    start_time = time.time()
    
    print(f"Processing endpoint: {name} ({host})")
    
    # Get route for this endpoint
    hops = get_route(host)
    
    # Check if we got any hops
    if not hops:
        print(f"Warning: No hops returned for {host}, using fallback dummy hop")
        # Create a fallback hop for visualization
        hops = [{
            "ttl": 1,
            "ip": "127.0.0.1",
            "rtt": 1.0,
            "status": "error: No route data available. May need elevated permissions.",
            "attempt": 1,
            "fallback": True
        }]
    
    # Check for permission errors and generate fallback data if needed
    permission_errors = [h for h in hops if h.get("status", "").startswith("error: Insufficient permissions")]
    if permission_errors:
        print(f"Permission error detected for {host}, using fallback data")
        # Create fallback data for visualization
        hops = [{
            "ttl": 1,
            "ip": "127.0.0.1",
            "rtt": 1.0,
            "status": "error: Insufficient permissions to create raw socket. Run as administrator/root.",
            "attempt": 1,
            "fallback": True
        }]
    
    # Add geolocation data to hops
    hops = geolocator.geolocate_hops(hops)
    
    # Calculate latency between hops
    sorted_hops = sorted([h for h in hops if h["status"] == "success"], key=lambda x: x["ttl"])
    
    for i in range(1, len(sorted_hops)):
        prev_hop = sorted_hops[i-1]
        current_hop = sorted_hops[i]
        
        if prev_hop["rtt"] is not None and current_hop["rtt"] is not None:
            # Latency between this hop and previous hop
            current_hop["hop_latency"] = current_hop["rtt"] - prev_hop["rtt"]
    
    valid_hops = [h for h in hops if h["status"] == "success"]
    timeouts = len([h for h in hops if h["status"] == "timeout"])
    errors = len([h for h in hops if h["status"].startswith("error")])
    
    hop_count = len(valid_hops)
    avg_rtt = sum(h["rtt"] for h in valid_hops) / hop_count if hop_count > 0 else 0
    max_rtt = max((h["rtt"] for h in valid_hops), default=0)
    min_rtt = min((h["rtt"] for h in valid_hops), default=0)
    packet_loss = (timeouts + errors) / len(hops) * 100 if hops else 0  # % of failed attempts
    success_rate = (hop_count / len(hops)) * 100 if hops else 0
    
    # Calculate geographic distance if possible
    geo_hops = [h for h in valid_hops if "lat" in h and "lon" in h]
    hop_countries = set([h.get("geo", {}).get("country") for h in geo_hops if h.get("geo")])
    
    duration = time.time() - start_time
    print(f"Completed processing {host} in {duration:.2f} seconds")
    
    return {
        "host": host,
        "data": {
            "hop_count": hop_count,
            "avg_rtt_ms": avg_rtt,
            "max_rtt_ms": max_rtt,
            "min_rtt_ms": min_rtt,
            "success_rate": success_rate,
            "packet_loss": packet_loss,
            "countries_traversed": len(hop_countries),
            "hops": hops,  # Store raw hop data for visualization
            "benchmark_duration": duration,  # Store the processing time
            "has_permission_error": bool(permission_errors)
        }
    }

def run_benchmark(endpoints, num_runs=3):
    """
    Run benchmark for all endpoints with support for multiple runs per provider.
    
    Args:
        endpoints: Dictionary of provider name to hostname
        num_runs: Number of runs per provider to average results (default: 3)
    
    Returns:
        Dictionary of results
    """
    geolocator = GeoLocator()
    results = {}
    aggregated_results = {}
    
    # Track overall progress
    total_endpoints = len(endpoints)
    total_runs = total_endpoints * num_runs
    completed = 0
    
    start_time = time.time()
    
    # Initialize progress
    with open('data/benchmark_progress.json', 'w') as f:
        json.dump({
            "progress": 10,  # Start at 10% (initialization complete)
            "completed": 0,
            "total": total_runs,
            "current_provider": "Starting trace routes...",
            "status": "running",
            "start_time": start_time
        }, f)
        
    # Process each endpoint sequentially for more consistency
    for name, host in endpoints.items():
        print(f"Processing {name} ({host}), running {num_runs} times...")
        # Store runs for this endpoint
        endpoint_runs = []
        
        for run in range(num_runs):
            try:
                print(f"Run {run+1}/{num_runs} for {name}")
                # Update progress file for this run
                with open('data/benchmark_progress.json', 'w') as f:
                    json.dump({
                        "progress": 10 + (completed / total_runs) * 80,
                        "completed": completed,
                        "total": total_runs,
                        "current_provider": f"{name} (run {run+1}/{num_runs})",
                        "status": "running",
                        "start_time": start_time
                    }, f)
                
                # Process this endpoint
                result = process_endpoint(name, host, geolocator)
                endpoint_runs.append(result)
                
                # Update progress
                completed += 1
                
            except Exception as exc:
                print(f'Endpoint {name} (run {run+1}) generated an exception: {exc}')
                # Still count as completed
                completed += 1
        
        # Aggregate multiple runs for this endpoint if we have successful runs
        successful_runs = [r for r in endpoint_runs if r and "data" in r and r["data"].get("hop_count", 0) > 0]
        
        if successful_runs:
            # Average the metrics from all successful runs
            host_data = aggregate_runs(successful_runs)
            results[host] = host_data
            print(f"Successfully aggregated {len(successful_runs)} runs for {name}")
        else:
            # If all runs failed, create an error entry
            print(f"All runs for {name} failed, creating error entry")
            results[host] = {
                "status": "error",
                "error": "All benchmark runs failed",
                "hop_count": 0,
                "avg_rtt_ms": 0,
                "max_rtt_ms": 0,
                "min_rtt_ms": 0,
                "success_rate": 0,
                "packet_loss": 100,
                "countries_traversed": 0,
                "hops": []
            }
    
    # Add total benchmark time
    benchmark_time = time.time() - start_time
    
    # Store final progress (90% - leave final 10% for post-processing)
    with open('data/benchmark_progress.json', 'w') as f:
        json.dump({
            "progress": 90,
            "completed": total_runs,
            "total": total_runs,
            "current_provider": "Processing results...",
            "status": "running",
            "start_time": start_time,
            "benchmark_time": benchmark_time
        }, f)
    
    return results

def aggregate_runs(runs):
    """
    Aggregate multiple benchmark runs for the same endpoint.
    
    Args:
        runs: List of result dictionaries from process_endpoint
        
    Returns:
        Aggregated result dictionary
    """
    # Get the most successful run's hops (the one with the most valid hops)
    valid_hop_counts = [(i, len([h for h in run["data"]["hops"] if h["status"] == "success"])) 
                        for i, run in enumerate(runs)]
    
    # Sort by hop count descending
    valid_hop_counts.sort(key=lambda x: x[1], reverse=True)
    
    # Use the run with the most valid hops for visualization
    best_run_idx = valid_hop_counts[0][0]
    best_run = runs[best_run_idx]
    
    # Start with the hop data from the best run
    aggregated = {
        "hops": best_run["data"]["hops"],
        "countries_traversed": best_run["data"]["countries_traversed"],
        "countries_list": best_run["data"].get("countries_list", []),
        "benchmark_duration": sum(run["data"]["benchmark_duration"] for run in runs) / len(runs),
        "has_permission_error": any(run["data"].get("has_permission_error", False) for run in runs)
    }
    
    # Average the numeric metrics
    aggregated["hop_count"] = sum(run["data"]["hop_count"] for run in runs) / len(runs)
    aggregated["avg_rtt_ms"] = sum(run["data"]["avg_rtt_ms"] for run in runs) / len(runs)
    aggregated["max_rtt_ms"] = max(run["data"]["max_rtt_ms"] for run in runs)
    aggregated["min_rtt_ms"] = min(run["data"]["min_rtt_ms"] for run in runs) if any(run["data"]["min_rtt_ms"] > 0 for run in runs) else 0
    aggregated["success_rate"] = sum(run["data"]["success_rate"] for run in runs) / len(runs)
    aggregated["packet_loss"] = sum(run["data"]["packet_loss"] for run in runs) / len(runs)
    
    return aggregated
