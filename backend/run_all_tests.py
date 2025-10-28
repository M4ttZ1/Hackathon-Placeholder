#!/usr/bin/env python3
"""
Master Test Runner for OmniLens Backend

Runs all test suites in sequence and reports results.
"""
import sys
import os
import subprocess
import time
from typing import List, Tuple

# Test files in order of complexity (fast → slow)
TEST_FILES = [
    ("Quick API Check", "tests/test_quick.py", True),
    ("Intel Module (VT + URLHaus)", "tests/test_intel.py", True),
    ("Multiple URL Handling", "tests/test_multiple_urls.py", True),
    ("FAISS Dynamic Scorer", "tests/test_faiss_dynamic.py", True),
    ("Complete System", "tests/test_complete_system.py", True),
    ("Full System (Malicious URL)", "tests/test_malicious_full_system.py", True),
    ("Legacy: FAISS Threshold", "tests/test_faiss_working.py", False),
    ("Legacy: Threshold Test", "tests/test_threshold.py", False),
]


def run_test(name: str, filepath: str) -> Tuple[bool, float]:
    """Run a single test file and return (success, duration)"""
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"File: {filepath}")
    print('='*70)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, filepath],
            cwd=os.path.dirname(__file__),
            capture_output=False,
            text=True,
            timeout=120  # 2 minute timeout per test
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        if success:
            print(f"\n[PASS] Test passed in {duration:.1f}s")
        else:
            print(f"\n[FAIL] Test failed (exit code {result.returncode}) after {duration:.1f}s")
        
        return success, duration
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"\n[TIMEOUT] Test timed out after {duration:.1f}s")
        return False, duration
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n[ERROR] {e}")
        return False, duration


def main():
    print("""
====================================================================
                  OMNILENS TEST SUITE RUNNER                      
====================================================================
""")
    
    # Check if we should run legacy tests
    run_legacy = "--all" in sys.argv or "--legacy" in sys.argv
    
    if not run_legacy:
        print("TIP: Use --all or --legacy to include legacy tests\n")
    
    results: List[Tuple[str, bool, float]] = []
    total_start = time.time()
    
    # Run each test
    for name, filepath, is_current in TEST_FILES:
        # Skip legacy tests unless requested
        if not is_current and not run_legacy:
            print(f"\n[SKIP] {name} (legacy test, use --legacy to run)")
            continue
        
        success, duration = run_test(name, filepath)
        results.append((name, success, duration))
        
        # Short pause between tests
        time.sleep(0.5)
    
    # Summary
    total_duration = time.time() - total_start
    
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    
    print(f"\nTests Run: {len(results)}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[TIME] Total Time: {total_duration:.1f}s")
    
    print("\n" + "="*70)
    print("DETAILED RESULTS")
    print("="*70)
    
    for name, success, duration in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status:10} | {duration:6.1f}s | {name}")
    
    print("="*70)
    
    # Exit with appropriate code
    if failed > 0:
        print(f"\n[FAIL] {failed} test(s) failed")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

