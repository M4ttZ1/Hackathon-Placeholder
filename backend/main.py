from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
import requests
import re
import urllib.parse
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from typing import List, Optional
import email
import email.policy
from thefuzz import fuzz

# --- Load API Key ---
VIRUSTOTAL_API_KEY = config('VIRUSTOTAL_API_KEY', default=None)

# --- AI Model and Data State ---
state = {"model": None, "faiss_index": None, "corpus_meta": None}

# --- FastAPI App Initialization ---
app = FastAPI(title="OmniLens API")


@app.on_event("startup")
def load_ai_resources():
    print("Loading AI resources...")
    try:
        state["model"] = SentenceTransformer('all-MiniLM-L6-v2')
        state["faiss_index"] = faiss.read_index("corpus.faiss")
        with open("corpus_meta.json", 'r', encoding='utf-8') as f:
            state["corpus_meta"] = json.load(f)
        print("✅ AI resources loaded successfully.")
    except Exception as e:
        print(f"--> ERROR: Failed to load AI resources: {e}. AI features will be disabled.")


# --- CORS Configuration ---
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])


# --- Helper Functions for Analysis ---

def check_url_on_virustotal(url_to_check: str) -> Optional[int]:
    if not VIRUSTOTAL_API_KEY: return None
    api_url = f"https://www.virustotal.com/api/v3/urls/{urllib.parse.quote_plus(url_to_check)}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            stats = response.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            return stats.get("malicious", 0)
    except requests.RequestException:
        return None
    return None


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
def perform_analysis(text: str):
    text_lower = text.lower()
    score = 0
    reasons = []
    neighbors_found = []

    # --- Rules Engine ---
    # URL Checks
    urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', text)
    for url in urls:
        malicious_count = check_url_on_virustotal(url)
        if malicious_count and malicious_count > 0:
            score += 40 + (malicious_count * 2)  # Dynamic score based on number of flags
            reasons.append(f"URL flagged as malicious by {malicious_count} vendors on VirusTotal.")
        try:
            hostname = urllib.parse.urlparse(url).hostname
            if any(tld in hostname for tld in ['.zip', '.mov']):
                score += 20;
                reasons.append(f"Suspicious TLD found: {hostname}")
        except Exception:
            pass

    # Keyword Checks
    if any(k in text_lower for k in ["gift card", "crypto", "wire"]):
        score += 20;
        reasons.append("Suspicious payment method mentioned.")

    # Brand Impersonation Check
    impersonation_reason = check_brand_impersonation(text)
    if impersonation_reason:
        score += 50;
        reasons.append(impersonation_reason)

    # --- AI Layer ---
    if state["model"] and state["faiss_index"]:
        query_embedding = state["model"].encode([text])
        k = 3
        distances, indices = state["faiss_index"].search(np.array(query_embedding, dtype='float32'), k)
        for i in range(k):
            idx = indices[0][i]
            similarity = 1 / (1 + distances[0][i])
            if similarity > 0.65:
                meta_item = state["corpus_meta"][idx]
                neighbors_found.append(Neighbor(similarity=round(similarity, 2), label=meta_item.get("label", "N/A"),
                                                text=meta_item.get("text", "")[:200] + "..."))
        if neighbors_found:
            top_match = neighbors_found[0]
            score_boost = int(top_match.similarity * 25)
            score += score_boost
            reasons.append(f"Message is {top_match.similarity:.0%} similar to a known '{top_match.label}' sample.")

    # --- Final Calculation ---
    final_score = min(100, score)
    label = "benign"
    if final_score >= 50:
        label = "high_risk"
    elif final_score >= 20:
        label = "suspicious"
    elif final_score > 0:
        label = "low_risk"
    if not reasons: reasons.append("No threats detected.")

    return AnalyzeResponse(score=final_score, label=label, reasons=reasons, neighbors=neighbors_found)


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


# --- API Endpoints ---
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_text_endpoint(request: AnalyzeRequest):
    return perform_analysis(request.text)


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
                    body = part.get_payload(decode=True).decode(part.get_content_charset(), 'ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset(), 'ignore')
        if not body:
            raise HTTPException(status_code=400, detail="Could not extract text body from the .eml file.")
        return perform_analysis(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse .eml file: {e}")