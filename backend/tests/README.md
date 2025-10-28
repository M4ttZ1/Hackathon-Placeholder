# OmniLens Test Suite

This directory contains all test files for the OmniLens backend.

## Quick Start: Run All Tests

```bash
# Run all current tests
python run_all_tests.py

# Run all tests including legacy ones
python run_all_tests.py --all
```

## Running Individual Tests

From the `backend` directory:
```bash
# Quick API check (fast, no AI models)
python tests/test_quick.py

# Intel API tests (VT + URLHaus)
python tests/test_intel.py

# FAISS dynamic scorer tests
python tests/test_faiss_dynamic.py

# Full system integration test
python tests/test_malicious_full_system.py

# Complete system test (all components)
python tests/test_complete_system.py
```

## Current/Recommended Tests

### ✅ test_quick.py
**Purpose:** Quick check of VirusTotal and URLHaus API functionality  
**Use:** Fast verification that API keys are working  
**Runtime:** ~2-3 seconds  
**Dependencies:** None (no AI models needed)

### ✅ test_intel.py
**Purpose:** Comprehensive intel module tests  
**Features:**
- URL encoding verification
- VirusTotal API integration
- URLHaus API integration
- Parallel execution
- Caching performance  
**Runtime:** ~5-10 seconds  
**Dependencies:** API keys required

### ✅ test_multiple_urls.py (NEW)
**Purpose:** Verify multiple URLs in one message are ALL checked  
**Features:**
- Tests benign URL first, malicious URL second
- Tests malicious URL first, benign URL second
- Verifies order doesn't matter
- Ensures consistent scoring  
**Runtime:** ~15-20 seconds  
**Dependencies:** Full system (AI models + API keys)  
**Why Critical:** Catches regression of bug where only first URL was checked

### ✅ test_faiss_dynamic.py (NEW)
**Purpose:** Dynamic FAISS scoring system validation  
**Features:**
- Tests continuous 0-100 scoring
- Validates softmax weighting
- Checks context modulation from intel
- Verifies diagnostics (n_eff, entropy, top_sim)  
**Runtime:** ~10-15 seconds  
**Dependencies:** AI models (SentenceTransformer, FAISS index, corpus)

### ✅ test_malicious_full_system.py (NEW)
**Purpose:** End-to-end integration test with known malicious URL  
**Features:**
- Tests complete pipeline (FAISS + Intel + Scoring)
- Validates scoring on real threat
- Checks all signal contributions  
**Runtime:** ~15-20 seconds  
**Dependencies:** Full system (AI models + API keys)

### ✅ test_complete_system.py
**Purpose:** Comprehensive system validation  
**Features:**
- Tests all major components
- Multiple test cases (benign, phishing, malicious)
- Detailed diagnostic output  
**Runtime:** ~20-30 seconds  
**Dependencies:** Full system

## Legacy Tests (for comparison)

### 📦 test_faiss_working.py
**Status:** Legacy - tests old threshold-based FAISS (sim > 0.60)  
**Use:** Compare old vs new system performance  
**Run:** Use `python run_all_tests.py --legacy`

### 📦 test_threshold.py
**Status:** Legacy - tests old threshold scoring  
**Use:** Benchmark for validating improvements  
**Run:** Use `python run_all_tests.py --legacy`

## Test Data

### test_faiss_cache.json
Temporary cache file created during FAISS tests. Can be safely deleted between test runs.

## Test Recommendations by Use Case

### "I want to run everything"
→ `python run_all_tests.py`

### "Is my setup working?"
→ `python tests/test_quick.py`

### "Are the APIs configured correctly?"
→ `python tests/test_intel.py`

### "Is the new FAISS scoring working?"
→ `python tests/test_faiss_dynamic.py`

### "Does the complete system work end-to-end?"
→ `python tests/test_malicious_full_system.py`

### "I want to compare old vs new FAISS"
→ `python run_all_tests.py --legacy`

## Common Issues

### "ModuleNotFoundError: No module named 'intel'"
**Fix:** Run tests from the `backend` directory, not from `backend/tests`

### "FileNotFoundError: corpus.faiss"
**Fix:** Ensure you're running from the `backend` directory where corpus files are located

### "API key not found"
**Fix:** Set environment variables or create `.env` file:
```bash
export VIRUSTOTAL_API_KEY=your_key_here
export URLHAUS_API_KEY=your_key_here
```

### "UnicodeEncodeError" on Windows
**Fix:** Already handled - all emoji characters replaced with ASCII equivalents

## Future Tests to Add

- [ ] Performance benchmarking (latency, throughput)
- [ ] Accuracy evaluation (precision, recall, F1)
- [ ] Calibration validation
- [ ] Stress testing (large messages, many URLs)
- [ ] Edge cases (empty text, invalid URLs, etc.)

---

**Last Updated:** 2025-10-27  
**Test Suite Status:** ✅ All current tests passing

