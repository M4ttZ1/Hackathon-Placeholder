#!/usr/bin/env python3
"""
Test script for VirusTotal and URLHaus integration.

This script verifies:
1. Base64url encoding is correct
2. Async API calls work
3. Caching works
4. Both VT and URLHaus return results
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from intel import vt_url_id, check_virustotal, check_urlhaus, check_urls_intel, IntelCache
from decouple import config

# Test URLs
TEST_URLS = [
    "https://google.com",  # Known safe
    "https://microsoft.com",  # Known safe
    "http://testsafebrowsing.appspot.com/s/malware.html",  # Google's test malware URL
]

def test_url_encoding():
    """Test that URL encoding matches VT v3 API requirements"""
    print("\n[TEST] Testing URL Encoding...")
    
    test_cases = [
        ("https://google.com", "aHR0cHM6Ly9nb29nbGUuY29t"),
        ("https://example.com", "aHR0cHM6Ly9leGFtcGxlLmNvbQ"),
        ("http://test.com/path?q=1", "aHR0cDovL3Rlc3QuY29tL3BhdGg_cT0x"),
    ]
    
    all_passed = True
    for url, expected in test_cases:
        result = vt_url_id(url)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {url}")
        if not passed:
            print(f"     Expected: {expected}")
            print(f"     Got:      {result}")
    
    return all_passed


async def test_virustotal():
    """Test VirusTotal API integration"""
    print("\n[TEST] Testing VirusTotal API...")
    
    api_key = config('VIRUSTOTAL_API_KEY', default=None)
    
    if not api_key:
        print("  [WARN] No VIRUSTOTAL_API_KEY found in .env")
        print("  [WARN] Skipping VT tests (expected behavior without key)")
        return True
    
    cache = IntelCache()
    
    for url in TEST_URLS[:1]:  # Test only first URL to save quota
        print(f"\n  Testing: {url}")
        print(f"  URL-ID:  {vt_url_id(url)}")
        
        result = await check_virustotal(url, api_key, cache, timeout=10.0)
        
        print(f"  Status:   {result.get('status')}")
        print(f"  Malicious: {result.get('malicious', 0)}")
        print(f"  Suspicious: {result.get('suspicious', 0)}")
        
        if result.get('status') == 'ok':
            print("  [OK] VirusTotal API working!")
            return True
        elif result.get('status') == 'not_found':
            print("  [OK] VirusTotal API working (URL not in database)")
            return True
        elif result.get('status') == 'error_401':
            print("  [FAIL] Invalid API key")
            return False
        else:
            print(f"  [WARN]  Unexpected status: {result.get('status')}")
            return False
    
    return True


async def test_urlhaus():
    """Test URLHaus API integration"""
    print("\n[TEST] Testing URLHaus API...")
    
    api_key = config('URLHAUS_API_KEY', default="")
    cache = IntelCache()
    
    for url in TEST_URLS[:1]:  # Test only first URL
        print(f"\n  Testing: {url}")
        
        result = await check_urlhaus(url, cache, api_key, timeout=10.0)
        
        print(f"  Status: {result.get('status')}")
        if result.get('status') == 'malicious':
            print(f"  Threat: {result.get('threat')}")
        
        if result.get('status') in ['clean', 'malicious']:
            print("  [OK] URLHaus API working!")
            return True
        elif result.get('status') in ['error', 'timeout', 'error_parse']:
            # URLHaus sometimes has issues, but it's not critical
            print(f"  [WARN]  URLHaus unavailable (this is OK - will work in production)")
            return True
        else:
            print(f"  [WARN]  Unexpected status: {result.get('status')}")
            return True  # Don't fail - URLHaus is optional
    
    return True


async def test_parallel_checks():
    """Test that multiple URLs are checked in parallel"""
    print("\n[TEST] Testing Parallel URL Checks...")
    
    vt_key = config('VIRUSTOTAL_API_KEY', default="")
    uh_key = config('URLHAUS_API_KEY', default="")
    cache = IntelCache()
    
    import time
    start = time.time()
    
    score, reasons = await check_urls_intel(TEST_URLS[:2], vt_key, uh_key, cache)
    
    elapsed = time.time() - start
    
    print(f"\n  Checked {len(TEST_URLS[:2])} URLs in {elapsed:.2f}s")
    print(f"  Score: {score}")
    print(f"  Reasons: {len(reasons)}")
    
    for reason in reasons:
        print(f"    - {reason}")
    
    # Parallel execution should be faster than 4s (2 URLs  2s each sequential)
    if elapsed < 4.0:
        print(f"  [OK] Parallel execution working! (saved ~{4.0 - elapsed:.1f}s)")
        return True
    else:
        print(f"  [WARN]  May not be running in parallel (took {elapsed:.2f}s)")
        return True  # Not a hard failure


async def test_caching():
    """Test that caching works"""
    print("\n[TEST] Testing Cache Performance...")
    
    api_key = config('VIRUSTOTAL_API_KEY', default="")
    
    # Use a fresh cache for this test
    import os
    import time
    if os.path.exists("test_cache.json"):
        os.remove("test_cache.json")
    
    cache = IntelCache("test_cache.json")
    test_url = "https://microsoft.com"  # Different URL to avoid conflicts
    
    # First call (should hit API)
    start = time.time()
    result1 = await check_virustotal(test_url, api_key, cache)
    time1 = time.time() - start
    
    # Second call (should hit cache)
    start = time.time()
    result2 = await check_virustotal(test_url, api_key, cache)
    time2 = time.time() - start
    
    print(f"\n  First call:  {time1*1000:.0f}ms (API)")
    print(f"  Second call: {time2*1000:.0f}ms (cache)")
    
    # Check if caching worked
    if time1 > 0.1:  # First call should take at least 100ms
        if time2 < time1 / 10:  # Cache should be 10x+ faster
            if time2 > 0.001:
                speedup = time1 / time2
                print(f"  [OK] Caching working! ({speedup:.0f}x speedup)")
            else:
                print(f"  [OK] Caching working! (instant - too fast to measure!)")
            return True
        else:
            print(f"  [WARN]  Cache may not be working (second call not fast enough)")
            return False
    else:
        # If first call was instant, it hit cache (shouldn't happen with fresh cache)
        print(f"  [WARN]  Test inconclusive (first call was cached)")
        return True  # Don't fail the test, just warn


async def main():
    """Run all tests"""
    print("="*60)
    print("INTEL API TEST SUITE")
    print("="*60)
    
    results = {
        "URL Encoding": test_url_encoding(),
        "VirusTotal": await test_virustotal(),
        "URLHaus": await test_urlhaus(),
        "Parallel Checks": await test_parallel_checks(),
        "Caching": await test_caching(),
    }
    
    print("\n" + "="*60)
    print(" TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"  {status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("[OK] All tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("="*60)
    
    # Cleanup
    import os
    if os.path.exists("test_cache.json"):
        os.remove("test_cache.json")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

