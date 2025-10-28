"""
Full system test with the malicious URL
Tests the complete pipeline: FAISS + Intel + Scoring Engine
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import main components
from main import perform_analysis, load_ai_resources

async def test_malicious_url():
    print("=" * 60)
    print("FULL SYSTEM TEST - MALICIOUS URL")
    print("=" * 60)
    
    # Load resources
    print("\n[1/2] Loading AI resources...")
    await load_ai_resources()
    
    # Test the malicious URL
    malicious_url = "http://42.231.180.222:55828/bin.sh"
    test_text = f"Check this out: {malicious_url}"
    
    print(f"\n[2/2] Analyzing: {test_text}")
    print("-" * 60)
    
    result = await perform_analysis(test_text)
    
    print(f"\nRESULTS:")
    print(f"  Score: {result.score}/100")
    print(f"  Label: {result.label}")
    print(f"\nReasons:")
    for i, reason in enumerate(result.reasons, 1):
        print(f"  {i}. {reason}")
    
    print(f"\nNeighbors ({len(result.neighbors)}):")
    for n in result.neighbors[:3]:
        print(f"  - sim={n.similarity:.3f} label={n.label}")
    
    if result.signals:
        print(f"\nSignals:")
        for signal_name, signal_data in result.signals.items():
            if isinstance(signal_data, dict):
                score = signal_data.get('score', 0)
                print(f"  {signal_name}: {score} points")
    
    print("\n" + "=" * 60)
    
    # Verify score is reasonable
    if result.score > 50:
        print(f"[OK] High risk detected (score={result.score})")
        print("     System is working correctly!")
    else:
        print(f"[WARN] Score is low ({result.score}) for known malicious URL")
        print("       This might indicate a configuration issue")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_malicious_url())

