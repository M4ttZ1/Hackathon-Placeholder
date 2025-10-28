#!/usr/bin/env python3
"""
Test for score inflation on simple benign messages.
Even single words like "Hello" shouldn't score high.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import perform_analysis, load_ai_resources


async def test_simple_messages():
    print("="*70)
    print("SIMPLE MESSAGE SCORING TEST")
    print("="*70)
    
    await load_ai_resources()
    
    test_cases = [
        "Hello",
        "Hi",
        "Thanks",
        "OK",
        "Yes",
        "No problem",
        "See you later",
        "Have a good day",
        "Meeting at 3pm",
        "Got it",
    ]
    
    results = []
    
    for text in test_cases:
        result = await perform_analysis(text)
        results.append({
            "text": text,
            "score": result.score,
            "label": result.label,
            "reasons": result.reasons
        })
        
        print(f"\nText: '{text}'")
        print(f"  Score: {result.score}/100")
        print(f"  Label: {result.label}")
        if result.reasons:
            print(f"  Reasons: {result.reasons[0]}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    high_scores = [r for r in results if r['score'] >= 15]
    
    print(f"\nTotal tested: {len(results)}")
    print(f"Scores >= 15 (low_risk): {len(high_scores)}")
    
    if high_scores:
        print("\nSimple messages with inflated scores:")
        for r in high_scores:
            print(f"  '{r['text']}' -> {r['score']}/100 ({r['label']})")
            if r['reasons']:
                print(f"    Reason: {r['reasons'][0]}")
    
    # Check for proper 0-10 range usage
    very_low = [r for r in results if r['score'] < 10]
    print(f"\nScores 0-10: {len(very_low)}")
    
    if len(very_low) == 0:
        print("[WARN] No scores in 0-10 range! System may be inflating all scores.")
    
    return len(high_scores) == 0  # Pass if no simple messages score >= 15


if __name__ == "__main__":
    success = asyncio.run(test_simple_messages())
    sys.exit(0 if success else 1)

