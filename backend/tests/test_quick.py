#!/usr/bin/env python3
"""
Quick test - just checks if APIs work without loading heavy models
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from decouple import config

async def quick_test():
    print("="*60)
    print("QUICK API TEST (no model loading)")
    print("="*60)
    
    # Test VT
    print("\n[1] VirusTotal...")
    vt_key = config('VIRUSTOTAL_API_KEY', default=None)
    if not vt_key:
        print("   [SKIP] No VT key in .env")
    else:
        from intel import check_virustotal, IntelCache
        cache = IntelCache()
        result = await check_virustotal("https://google.com", vt_key, cache)
        if result.get("status") == "ok":
            print(f"   [OK] Working! (malicious: {result.get('malicious', 0)})")
        else:
            print(f"   [FAIL] Status: {result.get('status')}")
    
    # Test URLHaus
    print("\n[2] URLHaus...")
    uh_key = config('URLHAUS_API_KEY', default=None)
    if not uh_key:
        print("   [SKIP] No URLHaus key in .env")
    else:
        from intel import check_urlhaus, IntelCache
        cache = IntelCache()
        result = await check_urlhaus("https://google.com", cache, uh_key)
        if result.get("status") in ["clean", "malicious"]:
            print(f"   [OK] Working! (status: {result.get('status')})")
        else:
            print(f"   [WARN] Status: {result.get('status')}")
    
    print("\n" + "="*60)
    print("Done! Now start the server with: uvicorn main:app --reload")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(quick_test())

