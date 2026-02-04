from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
import re
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from typing import List, Optional
import email
import email.policy
from thefuzz import fuzz
import asyncio
import warnings
import os

# Suppress protobuf warnings (harmless compatibility messages)
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf')

# Import new intel module
from intel import check_urls_intel, IntelCache
from scoring_engine import ScoringEngine

# Initialize scoring engine
scoring_engine = ScoringEngine()

# --- Load API Keys ---
VIRUSTOTAL_API_KEY = config('VIRUSTOTAL_API_KEY', default=None)
URLHAUS_API_KEY = config('URLHAUS_API_KEY', default=None)

# --- AI Model and Data State ---
# Initialize intel cache immediately (don't wait for startup)
from intel import IntelCache
_intel_cache = IntelCache("intel_cache.json")

state = {
    "model": None, 
    "faiss_index": None, 
    "corpus_meta": None, 
    "intel_cache": _intel_cache,
    "faiss_scorer": None
}

# --- FastAPI App Initialization ---
app = FastAPI(title="OmniLens API")


@app.on_event("startup")
async def load_ai_resources():
    print("[STARTUP] Loading AI resources...")
    try:
        print("   [1/5] Loading SentenceTransformer model...")
        state["model"] = SentenceTransformer('all-MiniLM-L6-v2')
        print("   [2/5] Loading FAISS index...")
        state["faiss_index"] = faiss.read_index("corpus.faiss")
        print("   [3/5] Loading corpus metadata...")
        with open("corpus_meta.json", 'r', encoding='utf-8') as f:
            state["corpus_meta"] = json.load(f)
        print("   [4/5] Initializing intel cache...")
        
        # Initialize intel cache
        state["intel_cache"] = IntelCache("intel_cache.json")
        
        print("   [5/5] Initializing dynamic FAISS scorer...")
        from faiss_scorer import FaissScorer
        state["faiss_scorer"] = FaissScorer(
            faiss_index=state["faiss_index"],
            corpus_meta=state["corpus_meta"],
            encoder=state["model"],
            k=8,  # Use top 8 neighbors
            tau=10.0  # Temperature for softmax
        )
        
        print("[OK] AI resources loaded successfully!")
        print(f"   - Model: all-MiniLM-L6-v2")
        print(f"   - FAISS vectors: {state['faiss_index'].ntotal}")
        print(f"   - FAISS scorer: Dynamic (no thresholds)")
        print(f"   - Intel cache: Ready")
    except Exception as e:
        print(f"[ERROR] Failed to load AI resources: {e}")
        import traceback
        traceback.print_exc()
        print("AI features will be disabled.")


# --- CORS Configuration ---
# Allow all localhost ports for development
origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174"
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])


# --- Helper Functions for Analysis ---


def check_brand_impersonation(text: str) -> Optional[str]:
    BRAND_KEYWORDS = ['microsoft', 'google', 'apple', 'paypal', 'amazon', 'discord', 'steam']
    words_in_text = re.findall(r'\b\w+\b', text.lower())
    for word in words_in_text:
        for brand in BRAND_KEYWORDS:
            similarity_score = fuzz.ratio(word, brand)
            if 85 < similarity_score < 100:
                return f"Potential brand impersonation: found '{word}', which is similar to '{brand}'."
    return None


# --- Main Analysis Logic (reusable function) ---
async def perform_analysis(text: str):
    # Extract URLs
    urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', text)
    
    # Get URL intel checks (VT + URLHaus)
    url_checks = []
    if urls and state["intel_cache"]:
        # Run intel checks and convert to format expected by scoring engine
        from intel import check_virustotal, check_urlhaus
        import asyncio
        
        tasks = []
        for url in urls:
            tasks.append(check_virustotal(url, VIRUSTOTAL_API_KEY or "", state["intel_cache"]))
            tasks.append(check_urlhaus(url, state["intel_cache"], URLHAUS_API_KEY or ""))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Group results by URL
        # For each URL, we have 2 results: VT at i*2, URLHaus at i*2+1
        for i in range(len(urls)):
            vt_result = results[i * 2] if i * 2 < len(results) else {}
            uh_result = results[i * 2 + 1] if i * 2 + 1 < len(results) else {}
            url_checks.append({
                "url": urls[i],
                "virustotal": vt_result if isinstance(vt_result, dict) else {},
                "urlhaus": uh_result if isinstance(uh_result, dict) else {}
            })
    
    # Get FAISS neighbors using dynamic scorer (NO THRESHOLDS!)
    neighbors_found = []
    faiss_score_value = 0
    faiss_diagnostics = {}
    
    if state.get("faiss_scorer"):
        # Build intel context for FAISS modulation
        intel_context = {}
        if url_checks:
            # Check if URLHaus flagged anything
            urlhaus_hit = any(
                check.get("urlhaus", {}).get("status") == "malicious"
                for check in url_checks
            )
            # Get max VT malicious count
            vt_malicious_max = max(
                (check.get("virustotal", {}).get("malicious", 0) for check in url_checks),
                default=0
            )
            # Check if all are clean
            vt_all_clean = all(
                check.get("virustotal", {}).get("malicious", 0) == 0 and
                check.get("virustotal", {}).get("suspicious", 0) == 0 and
                check.get("urlhaus", {}).get("status") != "malicious"
                for check in url_checks
            )
            
            intel_context = {
                "urlhaus_hit": urlhaus_hit,
                "vt_malicious_max": vt_malicious_max,
                "vt_all_clean": vt_all_clean
            }
        
        # Score with continuous function (no hard cutoffs!)
        faiss_score_value, diag, scored_neighbors = state["faiss_scorer"].score_text(
            text=text,
            intel_context=intel_context if intel_context else None
        )
        
        # Convert to format expected by scoring engine
        neighbors_found = [{
            "similarity": n["similarity"],
            "label": n["label"],
            "text": n["text"]
        } for n in scored_neighbors if n["similarity"] > 0.3]  # Very low bar, just filter noise
        
        # Store diagnostics
        faiss_diagnostics = {
            "score": faiss_score_value,
            "p_raw": diag.p_raw,
            "p_cal": diag.p_cal,
            "n_eff": diag.n_eff,
            "entropy": diag.entropy,
            "top_sim": diag.top_sim,
            "k": diag.k,
            "has_labels": diag.has_labels,
            "tau": diag.tau,
            "alpha_ctx": diag.alpha_ctx
        }
    
    # Use scoring engine to calculate final score
    result = scoring_engine.score_message(
        text=text,
        neighbors=neighbors_found,
        url_checks=url_checks,
        urls=urls,
        faiss_score=faiss_score_value if state.get("faiss_scorer") else None,
        faiss_diagnostics=faiss_diagnostics if state.get("faiss_scorer") else None
    )
    
    # Convert neighbors back to Pydantic models for response
    neighbor_models = [
        Neighbor(
            similarity=n["similarity"],
            label=n["label"],
            text=n["text"]
        )
        for n in neighbors_found
    ]
    
    return AnalyzeResponse(
        score=result.score,
        label=result.label,
        reasons=result.reasons,
        neighbors=neighbor_models,
        signals=result.signals  # Include all diagnostic information
    )


# --- Pydantic Models ---
class Neighbor(BaseModel):
    similarity: float
    label: str
    text: str


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    score: int
    label: str
    reasons: list[str]
    neighbors: List[Neighbor] = []
    signals: Optional[dict] = None  # Diagnostics for debugging


# --- API Endpoints ---
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text_endpoint(request: AnalyzeRequest):
    return await perform_analysis(request.text)


@app.post("/upload", response_model=AnalyzeResponse)
async def analyze_file_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .eml file.")
    contents = await file.read()
    try:
        msg = email.message_from_bytes(contents, policy=email.policy.default)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', 'ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', 'ignore')
        if not body:
            raise HTTPException(status_code=400, detail="Could not extract text body from the .eml file.")
        return await perform_analysis(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse .eml file: {e}")