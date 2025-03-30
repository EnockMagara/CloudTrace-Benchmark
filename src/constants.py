ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2

PROVIDERS = {
    "aws": "Amazon Web Services",
    "azure": "Microsoft Azure", 
    "gcp": "Google Cloud Platform",
    "ibm": "IBM Cloud",
    "oracle": "Oracle Cloud",
    "alibaba": "Alibaba Cloud",
    "digitalocean": "DigitalOcean",
    "linode": "Linode (Akamai)"
}

OUTPUT_FORMATS = ["csv", "json"]

RESULTS_TABLE = "benchmark_results"
RESULTS_SCHEMA = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "endpoint": "TEXT NOT NULL",
    "hop_count": "INTEGER",
    "avg_rtt_ms": "REAL",
    "max_rtt_ms": "REAL",
    "min_rtt_ms": "REAL",
    "success_rate": "REAL",
    "packet_loss": "REAL",
    "timestamp": "TEXT DEFAULT CURRENT_TIMESTAMP"
}

# IP Geolocation API settings
IPINFO_API_URL = "https://ipinfo.io/{}/json"
# Free tier API key limit
DEFAULT_IPINFO_TOKEN = None
