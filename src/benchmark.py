from src.tracer import get_route

def run_benchmark(endpoints):
    results = {}
    for name, host in endpoints.items():
        hops = get_route(host)
        valid_hops = [h for h in hops if h["status"] == "success"]
        timeouts = len([h for h in hops if h["status"] == "timeout"])
        errors = len([h for h in hops if h["status"].startswith("error")])
        
        hop_count = len(valid_hops)
        avg_rtt = sum(h["rtt"] for h in valid_hops) / hop_count if hop_count > 0 else 0
        max_rtt = max((h["rtt"] for h in valid_hops), default=0)
        min_rtt = min((h["rtt"] for h in valid_hops), default=0)
        packet_loss = (timeouts + errors) / len(hops) * 100  # % of failed attempts
        success_rate = (hop_count / len(hops)) * 100 if hops else 0
        
        results[host] = {
            "hop_count": hop_count,
            "avg_rtt_ms": avg_rtt,
            "max_rtt_ms": max_rtt,
            "min_rtt_ms": min_rtt,
            "success_rate": success_rate,
            "packet_loss": packet_loss,
            "hops": hops  # Store raw hop data for visualization
        }
    return results
