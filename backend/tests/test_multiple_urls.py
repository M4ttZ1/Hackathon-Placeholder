#!/usr/bin/env python3
"""
Test that multiple URLs in a single message are ALL checked correctly.
This was a critical bug where only the first URL was being analyzed.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import perform_analysis, load_ai_resources


async def test_multiple_urls():
    print("="*70)
    print("TESTING MULTIPLE URL HANDLING")
    print("="*70)
    
    # Load resources
    print("\n[1/3] Loading AI resources...")
    await load_ai_resources()
    
    # Test 1: Benign URL first, malicious URL second
    print("\n[2/3] Test 1: Benign first, malicious second")
    print("-"*70)
    
    text1 = """
    Check out this article: https://google.com
    
    Also this: http://42.231.180.222:55828/bin.sh
    """
    
    result1 = await perform_analysis(text1)
    print(f"Score: {result1.score}/100")
    print(f"Label: {result1.label}")
    print(f"Reasons ({len(result1.reasons)}):")
    for r in result1.reasons[:5]:
        print(f"  - {r}")
    
    # Test 2: Malicious URL first, benign URL second
    print("\n[3/3] Test 2: Malicious first, benign second")
    print("-"*70)
    
    text2 = """
    Check out: http://42.231.180.222:55828/bin.sh
    
    And also: https://google.com
    """
    
    result2 = await perform_analysis(text2)
    print(f"Score: {result2.score}/100")
    print(f"Label: {result2.label}")
    print(f"Reasons ({len(result2.reasons)}):")
    for r in result2.reasons[:5]:
        print(f"  - {r}")
    
    # Verify both detected the malicious URL
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    
    if result1.score > 70 and result2.score > 70:
        print("[PASS] Both tests detected the malicious URL!")
        print(f"  Test 1 (benign first): {result1.score}/100 - {result1.label}")
        print(f"  Test 2 (malicious first): {result2.score}/100 - {result2.label}")
        
        # Scores should be similar (within 10 points)
        score_diff = abs(result1.score - result2.score)
        if score_diff <= 10:
            print(f"[PASS] Scores are consistent (diff: {score_diff})")
        else:
            print(f"[WARN] Scores differ by {score_diff} points")
        
        return True
    else:
        print("[FAIL] One or both tests failed to detect malicious URL!")
        print(f"  Test 1: {result1.score}/100")
        print(f"  Test 2: {result2.score}/100")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_multiple_urls())
    sys.exit(0 if success else 1)

