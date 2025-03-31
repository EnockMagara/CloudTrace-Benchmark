import requests
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import time
from functools import lru_cache
from src.constants import IPINFO_API_URL, DEFAULT_IPINFO_TOKEN

# Load environment variables
load_dotenv()

# Cache directory for geolocation data
CACHE_DIR = Path('data/geo_cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class GeoLocator:
    def __init__(self):
        self.token = os.getenv('IPINFO_TOKEN', DEFAULT_IPINFO_TOKEN)
        self.cache_file = CACHE_DIR / 'ip_cache.json'
        self.ip_cache = self._load_cache()
        self.rate_limit_delay = 1.1  # seconds between API calls for free tier (1 request per second)
        self.last_request_time = 0
    
    def _load_cache(self):
        """Load the IP cache from the cache file."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}
    
    def _save_cache(self):
        """Save the IP cache to the cache file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.ip_cache, f)
    
    def geolocate_ip(self, ip_address):
        """Get the geolocation information for an IP address."""
        if not ip_address or ip_address == "None":
            return None
        
        # Check cache first
        if ip_address in self.ip_cache:
            return self.ip_cache[ip_address]
        
        # Private IP ranges don't need API calls
        if self._is_private_ip(ip_address):
            result = {
                "ip": ip_address,
                "city": "Private Network",
                "region": "Local",
                "country": "Local",
                "loc": "0,0",  # Default location for private IPs
                "org": "Private Network",
                "asn": "0",
                "private": True
            }
            self.ip_cache[ip_address] = result
            self._save_cache()
            return result
        
        # Respect rate limits for the API
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - (current_time - self.last_request_time))
        
        # Make the API request
        try:
            # Include ASN information in the request
            url = IPINFO_API_URL.format(ip_address)
            params = {}
            if self.token:
                params['token'] = self.token
            
            response = requests.get(url, params=params)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse ASN from the org field if it exists and doesn't have ASN field
                if 'org' in result and 'asn' not in result:
                    org_parts = result['org'].split()
                    if org_parts and org_parts[0].startswith('AS'):
                        try:
                            asn = org_parts[0][2:]  # Remove 'AS' prefix
                            result['asn'] = asn
                        except:
                            pass
                
                self.ip_cache[ip_address] = result
                self._save_cache()
                return result
            else:
                return {"error": f"API returned status code {response.status_code}", "ip": ip_address}
        
        except Exception as e:
            return {"error": str(e), "ip": ip_address}
    
    def geolocate_hops(self, hops):
        """Add geolocation data to a list of hops."""
        for hop in hops:
            if hop.get("ip") and hop["status"] == "success":
                geo_data = self.geolocate_ip(hop["ip"])
                if geo_data:
                    hop["geo"] = geo_data
                    # Extract latitude and longitude
                    if "loc" in geo_data:
                        try:
                            lat, lon = geo_data["loc"].split(",")
                            hop["lat"] = float(lat)
                            hop["lon"] = float(lon)
                        except:
                            hop["lat"] = 0
                            hop["lon"] = 0
        return hops
    
    def _is_private_ip(self, ip):
        """Check if an IP address is in a private range."""
        octets = ip.split('.')
        if len(octets) != 4:
            return False
        
        # Check for private IP ranges
        if octets[0] == '10':
            return True
        if octets[0] == '172' and 16 <= int(octets[1]) <= 31:
            return True
        if octets[0] == '192' and octets[1] == '168':
            return True
        if octets[0] == '127':
            return True
        return False