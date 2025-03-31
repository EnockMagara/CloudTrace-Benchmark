import requests
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import time
import concurrent.futures
from functools import lru_cache
import threading
from src.constants import IPINFO_API_URL, DEFAULT_IPINFO_TOKEN
import socket

# Load environment variables
load_dotenv()

# Cache directory for geolocation data
CACHE_DIR = Path('data/geo_cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# DNS cache to avoid redundant lookups
dns_cache = {}
dns_cache_lock = threading.Lock()

# Use lru_cache to cache DNS lookups
@lru_cache(maxsize=1000)
def cached_gethostbyname(hostname):
    """Thread-safe cached DNS resolution"""
    with dns_cache_lock:
        if hostname in dns_cache:
            return dns_cache[hostname]
        try:
            ip = socket.gethostbyname(hostname)
            dns_cache[hostname] = ip
            return ip
        except Exception as e:
            print(f"DNS resolution error for {hostname}: {e}")
            return hostname  # Return hostname if resolution fails

class GeoLocator:
    def __init__(self):
        self.token = os.getenv('IPINFO_TOKEN', DEFAULT_IPINFO_TOKEN)
        self.cache_file = CACHE_DIR / 'ip_cache.json'
        self.ip_cache = self._load_cache()
        self.rate_limit_delay = 1.1  # seconds between API calls for free tier (1 request per second)
        self.last_request_time = 0
        self.cache_modified = False
        self.cache_lock = threading.Lock()
        self.save_timer = None
        
        # Start a timer to periodically save the cache
        self._start_save_timer()
    
    def _start_save_timer(self):
        """Start a timer that periodically saves the cache"""
        if self.save_timer:
            self.save_timer.cancel()
        
        # Save every 30 seconds if modified
        self.save_timer = threading.Timer(30.0, self._timed_save_cache)
        self.save_timer.daemon = True
        self.save_timer.start()
    
    def _timed_save_cache(self):
        """Scheduled function to save cache if modified"""
        with self.cache_lock:
            if self.cache_modified:
                self._save_cache_internal()
                self.cache_modified = False
        
        # Restart the timer
        self._start_save_timer()
    
    def _load_cache(self):
        """Load the IP cache from the cache file."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}
    
    def _save_cache_internal(self):
        """Internal method to save the cache without lock (must be called with lock acquired)"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.ip_cache, f)
    
    def _save_cache(self):
        """Thread-safe method to mark cache as modified for batched saving"""
        with self.cache_lock:
            self.cache_modified = True
    
    def save_cache_now(self):
        """Force an immediate save of the cache"""
        with self.cache_lock:
            if self.cache_modified:
                self._save_cache_internal()
                self.cache_modified = False
    
    def geolocate_ip(self, ip_address):
        """Get the geolocation information for an IP address."""
        if not ip_address or ip_address == "None":
            return None
        
        # Check cache first with thread safety
        with self.cache_lock:
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
            with self.cache_lock:
                self.ip_cache[ip_address] = result
                self.cache_modified = True
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
                
                with self.cache_lock:
                    self.ip_cache[ip_address] = result
                    self.cache_modified = True
                return result
            else:
                return {"error": f"API returned status code {response.status_code}", "ip": ip_address}
        
        except Exception as e:
            return {"error": str(e), "ip": ip_address}
    
    def geolocate_hops(self, hops):
        """Add geolocation data to a list of hops."""
        # Process all IPs in parallel
        ip_addresses = [hop.get("ip") for hop in hops if hop.get("ip") and hop["status"] == "success"]
        
        # Pre-fetch all IPs
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Create a dict of futures for each IP
            future_to_ip = {executor.submit(self.geolocate_ip, ip): ip for ip in ip_addresses}
            
            # Process results as they complete (this pre-populates the cache)
            for future in concurrent.futures.as_completed(future_to_ip):
                _ = future.result()  # Just to make sure it completes
        
        # Now attach geo data to hops (from cache)
        for hop in hops:
            if hop.get("ip") and hop["status"] == "success":
                geo_data = self.geolocate_ip(hop["ip"])  # Will come from cache now
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
        
        # Make sure to save the cache after processing
        self.save_cache_now()
        
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
    
    def __del__(self):
        """Clean up the object - save cache if modified"""
        if hasattr(self, 'save_timer') and self.save_timer:
            self.save_timer.cancel()
        
        # Save cache if modified
        if hasattr(self, 'cache_modified') and self.cache_modified:
            with self.cache_lock:
                self._save_cache_internal()