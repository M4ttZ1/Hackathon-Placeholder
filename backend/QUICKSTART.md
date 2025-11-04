# OmniLens Quick Start Guide

## What is OmniLens?

OmniLens is a phishing detection system that analyzes text messages and emails for suspicious content. It combines multiple detection methods:

- **Threat Intelligence**: Checks URLs against VirusTotal and URLHaus databases
- **Semantic Similarity**: Uses AI embeddings (FAISS) to compare messages to known phishing samples
- **Pattern Detection**: Identifies suspicious keywords, URLs, and obfuscation techniques
- **Scoring Engine**: Blends all signals into a 0-100 risk score with labels (benign, low_risk, suspicious, high_risk, confirmed_phishing)

---

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up API Keys (Optional)

Create `backend/.env`:

```bash
VIRUSTOTAL_API_KEY=your_vt_key_here
URLHAUS_API_KEY=your_urlhaus_key_here
```

**Note:** Without API keys, the system still works but skips threat intelligence checks. Get keys from:
- VirusTotal: https://www.virustotal.com/gui/my-apikey
- URLHaus: https://urlhaus.abuse.ch/api/

---

## Build the Corpus

Before running the system, you need to build the FAISS index from your dataset:

```bash
cd backend
python create_corpus.py
python build_index.py
```

This creates:
- `corpus.json` - Corpus metadata
- `corpus_meta.json` - Extended metadata with labels
- `corpus.faiss` - FAISS index for similarity search

The corpus uses datasets from `backend/datasets/` (Enron, SpamAssassin, phishing datasets).

---

## Running the Server

### Start Backend

```bash
cd backend
uvicorn main:app --reload
```

Server runs on `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

Frontend runs on `http://localhost:5173`

### Test the API

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "URGENT: Verify your PayPal account at https://example.com"}'
```

**Response:**
```json
{
  "score": 45,
  "label": "suspicious",
  "reasons": [
    "Urgency keywords detected.",
    "VirusTotal: 0 vendors flagged URL as malicious."
  ],
  "neighbors": [...],
  "signals": {...}
}
```

---

## Running Tests

### Run All Tests

```bash
cd backend
python run_all_tests.py
```

This runs all test suites in sequence and reports results.

### Individual Tests

#### Quick API Test
```bash
python tests/test_quick.py
```
Checks if VirusTotal and URLHaus APIs are accessible without loading AI models.

#### Intel Module Test
```bash
python tests/test_intel.py
```
Tests URL encoding, async API calls, caching, and both VT/URLHaus integration.

#### Multiple URL Handling
```bash
python tests/test_multiple_urls.py
```
Verifies that messages with multiple URLs are processed correctly.

#### FAISS Dynamic Scorer
```bash
python tests/test_faiss_dynamic.py
```
Tests the continuous 0-100 FAISS scoring system (no hard thresholds).

#### Complete System Test
```bash
python tests/test_complete_system.py
```
End-to-end test verifying FAISS, VirusTotal, URLHaus, and scoring engine work together.

#### Full System with Malicious URL
```bash
python tests/test_malicious_full_system.py
```
Tests the complete pipeline with a known malicious URL to verify detection.

#### Score Inflation Test
```bash
python tests/test_score_inflation.py
```
Verifies that benign messages don't get artificially high scores.

---

## How It Works

### Analysis Pipeline

1. **Text Input** → Extract URLs and text content
2. **Threat Intel** → Check URLs against VirusTotal and URLHaus (async, cached)
3. **FAISS Search** → Find similar messages in corpus using AI embeddings
4. **Pattern Detection** → Scan for keywords, suspicious URLs, brand impersonation
5. **Scoring Engine** → Combine all signals into a single risk score
6. **Confidence Dampening** → Adjust score based on message length and evidence strength
7. **Label Assignment** → Classify as benign/low_risk/suspicious/high_risk/confirmed_phishing

### Scoring Components

- **Intel**: VirusTotal/URLHaus results (0-75 points)
- **FAISS**: Semantic similarity to known phishing (0-35 points)
- **Keywords**: Urgency and payment terms (0-30 points)
- **Patterns**: Suspicious TLDs, IP addresses, ports (0-45 points)
- **Brand**: Brand impersonation detection (0-10 points, contextual)

Final score is clamped to 0-100 and adjusted by confidence dampening.

---

## Common Issues

### Module Not Found Errors

Make sure you're in the `backend` directory:
```bash
cd backend
python -c "from intel import check_virustotal; print('OK')"
```

### VirusTotal Returns 401

Check your `.env` file:
```bash
# backend/.env
VIRUSTOTAL_API_KEY=your_key_here  # No quotes
```

### FAISS Index Not Found

Build the corpus first:
```bash
python create_corpus.py
python build_index.py
```

### Cache Issues

Delete `intel_cache.json` to clear cached API results:
```bash
rm backend/intel_cache.json
```

---

## Documentation

All detailed documentation is in `backend/docs/`:

- `ARCHITECTURE_EXPLAINED.md` - System architecture overview
- `IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `FAISS_DYNAMIC_SCORING.md` - FAISS scoring explanation
- `SETUP_API_KEYS.md` - API key setup guide
- `BUGFIX_MULTIPLE_URLS.md` - Known issues and fixes

---

**That's it! You're ready to analyze messages for phishing attempts.**
