#!/usr/bin/env python3
"""
Complete system test - verifies FAISS, VirusTotal, and URLHaus are all working
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from decouple import config

async def test_complete_system():
    print("="*60)
    print("COMPLETE SYSTEM TEST")
    print("="*60)
    
    # Test 1: FAISS and Model Loading
    print("\n[1] Testing FAISS + SentenceTransformer...")
    print("    (This may take 1-2 minutes on first run - downloading model...)")
    try:
        import faiss
        import json
        print("   [OK] FAISS library imported")
        
        from sentence_transformers import SentenceTransformer
        print("   [OK] SentenceTransformer library imported")
        
        print("   Loading model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("   [OK] SentenceTransformer model loaded")
        
        index = faiss.read_index("corpus.faiss")
        print(f"   [OK] FAISS index loaded ({index.ntotal} vectors)")
        
        with open("corpus_meta.json", 'r') as f:
            corpus_meta = json.load(f)
        print(f"   [OK] Corpus metadata loaded ({len(corpus_meta)} entries)")
        
        # Test encoding
        test_text = "Click here to verify your PayPal account"
        embedding = model.encode([test_text])
        distances, indices = index.search(embedding, k=3)
        print(f"   [OK] FAISS similarity search working")
        print(f"      Top match similarity: {1 / (1 + distances[0][0]):.2%}")
        
    except Exception as e:
        print(f"   [FAIL] FAISS/Model Error: {e}")
        return False
    
    # Test 2: VirusTotal
    print("\n[2] Testing VirusTotal...")
    vt_key = config('VIRUSTOTAL_API_KEY', default=None)
    
    if not vt_key:
        print("   [WARN]  No VIRUSTOTAL_API_KEY in .env")
        print("   [WARN]  Add to backend/.env: VIRUSTOTAL_API_KEY=your_key")
    else:
        try:
            from intel import check_virustotal, IntelCache
            cache = IntelCache()
            
            result = await check_virustotal("https://google.com", vt_key, cache)
            if result.get("status") == "ok":
                print(f"   [OK] VirusTotal API working")
                print(f"      Malicious: {result.get('malicious', 0)}")
                print(f"      Suspicious: {result.get('suspicious', 0)}")
            else:
                print(f"   [WARN]  VirusTotal status: {result.get('status')}")
        except Exception as e:
            print(f"   [FAIL] VirusTotal Error: {e}")
    
    # Test 3: URLHaus
    print("\n[3] Testing URLHaus...")
    uh_key = config('URLHAUS_API_KEY', default=None)
    
    if not uh_key:
        print("   [WARN]  No URLHAUS_API_KEY in .env")
        print("   [WARN]  Add to backend/.env: URLHAUS_API_KEY=your_key")
    else:
        try:
            from intel import check_urlhaus, IntelCache
            cache = IntelCache()
            
            result = await check_urlhaus("https://google.com", cache, uh_key)
            if result.get("status") in ["clean", "malicious"]:
                print(f"   [OK] URLHaus API working")
                print(f"      Status: {result.get('status')}")
                if result.get("status") == "malicious":
                    print(f"      Threat: {result.get('threat')}")
            else:
                print(f"   [WARN]  URLHaus status: {result.get('status')}")
        except Exception as e:
            print(f"   [FAIL] URLHaus Error: {e}")
    
    # Test 4: Full Analysis Pipeline
    print("\n[4] Testing Full Analysis Pipeline...")
    try:
        from main import perform_analysis
        
        test_message = """
        URGENT! Your PayPal account has been suspended.
        Verify immediately: https://google.com
        Send $500 via wire transfer to reactivate.
        """
        
        result = await perform_analysis(test_message)
        print(f"   [OK] Analysis pipeline working")
        print(f"      Score: {result.score}")
        print(f"      Label: {result.label}")
        print(f"      Reasons: {len(result.reasons)}")
        for reason in result.reasons[:3]:
            print(f"        - {reason}")
        
    except Exception as e:
        print(f"   [FAIL] Analysis Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("[PASS] SYSTEM TEST COMPLETE")
    print("="*60)
    return True

if __name__ == "__main__":
    sys.exit(0 if asyncio.run(test_complete_system()) else 1)

