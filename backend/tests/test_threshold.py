#!/usr/bin/env python3
"""Test different threshold values"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import perform_analysis

async def test():
    tests = [
        "Urgent: Your PayPal account suspended. Verify now!",
        "Bank account verification needed immediately.",
        "Congratulations! You won $1000 gift card!",
        "Hey, want to grab coffee later?",
        "Meeting at 3pm in conference room B.",
    ]
    
    print("Testing current system with various texts:")
    print("="*60)
    
    for text in tests:
        result = await perform_analysis(text)
        print(f"\nText: {text[:50]}...")
        print(f"  Score: {result.score}")
        print(f"  Label: {result.label}")
        if result.neighbors:
            print(f"  Neighbors found: {len(result.neighbors)}")
            for n in result.neighbors[:2]:
                print(f"    - {n.similarity:.3f} | {n.label}")
        else:
            print(f"  Neighbors: None found above threshold")
        print(f"  Reasons: {len(result.reasons)}")

if __name__ == "__main__":
    asyncio.run(test())

