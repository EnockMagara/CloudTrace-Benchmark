import matplotlib.pyplot as plt
from pathlib import Path

def plot_rtt(results, output_dir="data"):
    """Bar plot of average RTT per endpoint."""
    endpoints = list(results.keys())
    avg_rtts = [results[e]["avg_rtt_ms"] for e in endpoints]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(endpoints, avg_rtts, color="skyblue")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval:.1f}", ha="center", va="bottom")
    plt.xlabel("Endpoint")
    plt.ylabel("Average RTT (ms)")
    plt.title("Average RTT by Cloud Provider")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "rtt_bar.png")
    plt.close()

def plot_hop_latency(results, output_dir="data"):
    """Line plot of RTT per hop for each endpoint with annotations."""
    plt.figure(figsize=(12, 8))
    for endpoint, data in results.items():
        hops = data["hops"]
        ttls = [h["ttl"] for h in hops if h["rtt"] is not None]
        rtts = [h["rtt"] for h in hops if h["rtt"] is not None]
        plt.plot(ttls, rtts, marker="o", label=endpoint)
        # Annotate spikes
        for ttl, rtt in zip(ttls, rtts):
            if rtt > 100:  # Highlight RTT > 100 ms
                plt.text(ttl, rtt + 20, f"{rtt:.1f} ms", ha="center", color="red")
    
    plt.xlabel("Hop Number (TTL)")
    plt.ylabel("RTT (ms)")
    plt.title("RTT per Hop by Cloud Provider")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "hop_latency.png")
    plt.close()

def visualize(results):
    plot_rtt(results)
    plot_hop_latency(results)