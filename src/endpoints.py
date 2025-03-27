import json
from src.constants import PROVIDERS

def load_static_endpoints():
    with open("config/endpoints.json", "r") as f:
        return json.load(f)

def get_endpoints(providers):
    endpoints = load_static_endpoints()
    return {key: endpoints[key] for key in providers if key in endpoints}
