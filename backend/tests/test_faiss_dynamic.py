"""
Test the new dynamic FAISS scoring system (no thresholds!)
"""
import asyncio
import sys
import os
from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from faiss_scorer import FaissScorer
from intel import IntelCache, check_virustotal, check_urlhaus

# Load API keys
from decouple import config
VIRUSTOTAL_API_KEY = config('VIRUSTOTAL_API_KEY', default=None)
URLHAUS_API_KEY = config('URLHAUS_API_KEY', default=None)


async def test_dynamic_faiss():
    print("=" * 60)
    print("TESTING DYNAMIC FAISS SCORER (CONTINUOUS 0-100)")
    print("=" * 60)
    
    # Load resources
    print("\n[1/4] Loading AI resources...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    index = faiss.read_index("corpus.faiss")
    with open("corpus_meta.json", 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print(f"   Loaded: {index.ntotal} vectors")
    
    # Initialize scorer
    print("\n[2/4] Initializing FaissScorer...")
    scorer = FaissScorer(
        faiss_index=index,
        corpus_meta=meta,
        encoder=model,
        k=8,
        tau=10.0
    )
    print(f"   K={scorer.k}, tau={scorer.tau}")
    print(f"   Has labels: {scorer.y is not None}")
    
    # Test cases
    test_cases = [
        {
            "name": "Clean message",
            "text": "Hi John, hope you're having a great day! Let's catch up soon.",
            "expected_range": (0, 30)
        },
        {
            "name": "Phishing (no URL)",
            "text": "URGENT: Your account will be suspended unless you verify your identity immediately. Click here to confirm.",
            "expected_range": (30, 70)
        },
        {
            "name": "Known phishing",
            "text": "Dear valued customer, we noticed suspicious activity on your account. Please verify your identity by clicking the link below or your account will be permanently suspended within 24 hours.",
            "expected_range": (50, 90)
        },
        {
            "name": "Malicious URL (actual virus)",
            "text": "Check this out: http://42.231.180.222:55828/bin.sh",
            "expected_range": (60, 100)
        }
    ]
    
    print("\n[3/4] Testing FAISS scoring (NO THRESHOLDS!)...")
    cache = IntelCache("test_faiss_cache.json")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {case['name']} ---")
        print(f"Text: {case['text'][:80]}...")
        
        # Score with FAISS only (no intel context)
        faiss_score, diag, neighbors = scorer.score_text(
            text=case['text'],
            intel_context=None
        )
        
        print(f"\nFAISS Score: {faiss_score}/100")
        print(f"  p_raw: {diag.p_raw:.3f}")
        print(f"  p_cal: {diag.p_cal:.3f}")
        print(f"  top_sim: {diag.top_sim:.3f}")
        print(f"  n_eff: {diag.n_eff:.2f}")
        print(f"  entropy: {diag.entropy:.3f}")
        
        print(f"\nTop 3 neighbors:")
        for n in neighbors[:3]:
            print(f"  {n['rank']}. sim={n['similarity']:.4f} label={n['label']} text={n['text'][:60]}...")
        
        # Check if in expected range
        min_score, max_score = case['expected_range']
        if min_score <= faiss_score <= max_score:
            print(f"\n[OK] Score {faiss_score} is in expected range [{min_score}, {max_score}]")
        else:
            print(f"\n[WARN] Score {faiss_score} is outside expected range [{min_score}, {max_score}]")
    
    # Test with intel context modulation
    print("\n" + "=" * 60)
    print("[4/4] Testing Intel Context Modulation...")
    print("=" * 60)
    
    malicious_url = "http://42.231.180.222:55828/bin.sh"
    print(f"\nTesting URL: {malicious_url}")
    
    # Get intel
    if VIRUSTOTAL_API_KEY and URLHAUS_API_KEY:
        print("Checking VirusTotal + URLHaus...")
        vt_result = await check_virustotal(malicious_url, VIRUSTOTAL_API_KEY, cache)
        uh_result = await check_urlhaus(malicious_url, cache, URLHAUS_API_KEY)
        
        print(f"  VT: status={vt_result.get('status')}, mal={vt_result.get('malicious', 0)}")
        print(f"  UH: status={uh_result.get('status')}")
        
        # Build intel context
        intel_context = {
            "urlhaus_hit": uh_result.get("status") == "malicious",
            "vt_malicious_max": vt_result.get("malicious", 0),
            "vt_all_clean": vt_result.get("malicious", 0) == 0 and vt_result.get("suspicious", 0) == 0
        }
        
        # Score without context
        score_no_ctx, _, _ = scorer.score_text(malicious_url, intel_context=None)
        
        # Score with context
        score_with_ctx, diag_ctx, _ = scorer.score_text(malicious_url, intel_context=intel_context)
        
        print(f"\nFAISS Score (no context): {score_no_ctx}/100")
        print(f"FAISS Score (with intel): {score_with_ctx}/100")
        print(f"Context modulation factor: {diag_ctx.alpha_ctx:.2f}x")
        
        if score_with_ctx > score_no_ctx:
            print(f"[OK] Intel context boosted score by {score_with_ctx - score_no_ctx} points")
        else:
            print(f"[WARN] Intel context did not boost score")
    else:
        print("[SKIP] No API keys configured")
    
    print("\n" + "=" * 60)
    print("DYNAMIC FAISS TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_dynamic_faiss())

