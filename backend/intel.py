# backend/intel.py
"""
Intel module for checking URLs against threat intelligence APIs
- VirusTotal v3 API
- URLHaus API
"""
import os
import base64
import json
from typing import Dict, Any, Optional
import httpx


class IntelCache:
    """Simple in-memory cache with optional file persistence"""
    
    def __init__(self, persist_path: Optional[str] = None):
        self.mem: Dict[str, Any] = {}
        self.persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            try:
                with open(persist_path, 'r') as f:
                    self.mem = json.load(f)
                print(f"[OK] Loaded {len(self.mem)} cached intel results from {persist_path}")
            except Exception as e:
                print(f"[WARN] Could not load cache: {e}")
                self.mem = {}

    def get(self, key: str):
        return self.mem.get(key)
    
    def set(self, key: str, val: Any):
        self.mem[key] = val
        if self.persist_path:
            try:
                with open(self.persist_path, 'w') as f:
                    json.dump(self.mem, f, indent=2)
            except Exception as e:
                print(f"⚠️ Could not save cache: {e}")


def vt_url_id(url: str) -> str:
    """
    Convert URL to VirusTotal URL-ID format.
    
    VirusTotal v3 API requires URLs to be encoded as base64url (RFC 4648)
    without padding. This is NOT the same as urllib.parse.quote_plus!
    
    Example:
        "https://example.com" -> "aHR0cHM6Ly9leGFtcGxlLmNvbQ"
    
    Args:
        url: The URL to encode
        
    Returns:
        Base64url-encoded URL without padding
    """
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


async def check_virustotal(
    url: str, 
    api_key: str, 
    cache: IntelCache, 
    timeout: float = 6.0
) -> Dict[str, Any]:
    """
    Check a single URL against VirusTotal v3 API.
    
    Args:
        url: The URL to check
        api_key: VirusTotal API key
        cache: IntelCache instance for caching results
        timeout: Request timeout in seconds
        
    Returns:
        Dict with keys: provider, malicious (int), suspicious (int), status
    """
    if not api_key:
        return {
            "provider": "virustotal",
            "malicious": 0,
            "suspicious": 0,
            "status": "no_key"
        }
    
    url_id = vt_url_id(url)
    cache_key = f"vt:{url_id}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Make API call
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers={"x-apikey": api_key},
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                result = {
                    "provider": "virustotal",
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "status": "ok"
                }
                cache.set(cache_key, result)
                return result
                
            elif response.status_code == 404:
                # URL not found in VT database
                result = {
                    "provider": "virustotal",
                    "malicious": 0,
                    "suspicious": 0,
                    "status": "not_found"
                }
                cache.set(cache_key, result)
                return result
                
            else:
                return {
                    "provider": "virustotal",
                    "malicious": 0,
                    "suspicious": 0,
                    "status": f"error_{response.status_code}"
                }
                
        except httpx.TimeoutException:
            return {
                "provider": "virustotal",
                "malicious": 0,
                "suspicious": 0,
                "status": "timeout"
            }
        except Exception as e:
            return {
                "provider": "virustotal",
                "malicious": 0,
                "suspicious": 0,
                "status": f"error"
            }


async def check_urlhaus(
    url: str, 
    cache: IntelCache,
    api_key: str = "",
    timeout: float = 6.0
) -> Dict[str, Any]:
    """
    Check a single URL against URLHaus API.
    
    URLHaus is a project from abuse.ch that tracks malicious URLs.
    Requires API key in Auth-Key header.
    
    Args:
        url: The URL to check
        cache: IntelCache instance for caching results
        api_key: URLHaus API key (optional but recommended)
        timeout: Request timeout in seconds
        
    Returns:
        Dict with keys: provider, status, threat (if malicious)
    """
    cache_key = f"urlhaus:{url}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Make API call
    headers = {}
    if api_key:
        headers["Auth-Key"] = api_key
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.post(
                "https://urlhaus-api.abuse.ch/v1/url/",
                data={"url": url},
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    query_status = data.get("query_status", "not_found")
                    
                    if query_status == "ok":
                        # URL is in the database (malicious)
                        result = {
                            "provider": "urlhaus",
                            "status": "malicious",
                            "threat": data.get("threat", "unknown"),
                            "url_status": data.get("url_status", "unknown")
                        }
                    elif query_status == "no_results":
                        # URL not found in database (clean)
                        result = {
                            "provider": "urlhaus",
                            "status": "clean"
                        }
                    else:
                        # Other status
                        result = {
                            "provider": "urlhaus",
                            "status": "clean"
                        }
                    
                    cache.set(cache_key, result)
                    return result
                except Exception:
                    # JSON parsing failed
                    return {
                        "provider": "urlhaus",
                        "status": "error_parse"
                    }
            else:
                return {
                    "provider": "urlhaus",
                    "status": f"error_{response.status_code}"
                }
                
        except httpx.TimeoutException:
            return {
                "provider": "urlhaus",
                "status": "timeout"
            }
        except Exception as e:
            return {
                "provider": "urlhaus",
                "status": "error"
            }


async def check_urls_intel(
    urls: list[str], 
    vt_api_key: str,
    urlhaus_api_key: str,
    cache: IntelCache
) -> tuple[int, list[str]]:
    """
    Check multiple URLs against VT and URLHaus in parallel.
    
    This function runs all API checks concurrently for maximum performance.
    
    Args:
        urls: List of URLs to check
        vt_api_key: VirusTotal API key
        urlhaus_api_key: URLHaus API key
        cache: IntelCache instance
        
    Returns:
        Tuple of (score_delta, reasons_list)
    """
    if not urls:
        return 0, []
    
    import asyncio
    
    score = 0
    reasons = []
    
    # Create tasks for all URLs (both VT and URLHaus)
    tasks = []
    for url in urls:
        tasks.append(check_virustotal(url, vt_api_key, cache))
        tasks.append(check_urlhaus(url, cache, urlhaus_api_key))
    
    # Run all checks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if isinstance(result, dict):
            # VirusTotal results
            if result.get("provider") == "virustotal":
                mal_count = result.get("malicious", 0)
                sus_count = result.get("suspicious", 0)
                
                if mal_count > 0:
                    score += 40 + min(20, mal_count * 2)
                    reasons.append(f"VirusTotal: {mal_count} vendors flagged URL as malicious.")
                elif sus_count > 0:
                    score += 10
                    reasons.append(f"VirusTotal: {sus_count} vendors marked URL as suspicious.")
            
            # URLHaus results
            elif result.get("provider") == "urlhaus":
                if result.get("status") == "malicious":
                    score += 50
                    threat = result.get("threat", "unknown")
                    reasons.append(f"URLHaus: URL identified as {threat}.")
    
    return score, reasons

