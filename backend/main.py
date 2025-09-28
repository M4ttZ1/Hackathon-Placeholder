import logging
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import email
import email.policy
from thefuzz import fuzz
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
import requests
import re
import urllib.parse
from typing import List, Optional

# --- Basic Logging & Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
VIRUSTOTAL_API_KEY = config('VIRUSTOTAL_API_KEY', default=None)
state = {"model": None, "faiss_index": None, "corpus_meta": None}
app = FastAPI(title="OmniLens API")


@app.on_event("startup")
def load_ai_resources():
    logging.info("Attempting to load AI resources...")
    try:
        state["model"] = SentenceTransformer('all-MiniLM-L6-v2')
        state["faiss_index"] = faiss.read_index("corpus.faiss")
        with open("corpus_meta.json", 'r', encoding='utf-8') as f:
            state["corpus_meta"] = json.load(f)
        logging.info("✅ AI resources loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load AI resources: {e}", exc_info=True)


origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])


# --- Helper Functions for Analysis ---

def check_url_on_virustotal(url_to_check: str) -> Optional[int]:
    print(f"\n--- DEBUG: Checking VirusTotal for: {url_to_check} ---")
    if not VIRUSTOTAL_API_KEY:
        print("--- DEBUG: VIRUSTOTAL_API_KEY is missing. Skipping check. ---")
        return None
    api_url = f"https://www.virustotal.com/api/v3/urls/{urllib.parse.quote_plus(url_to_check)}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        print(f"--- DEBUG: VirusTotal Response Status Code: {response.status_code} ---")
        print(f"--- DEBUG: VirusTotal Response Body: {response.text[:300]} ... ---")
        if response.status_code == 200:
            stats = response.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious_count = stats.get("malicious", 0)
            print(f"--- DEBUG: Malicious count found: {malicious_count} ---")
            return malicious_count
    except requests.RequestException as e:
        print(f"--- DEBUG: VirusTotal API request failed with an exception: {e} ---")
    return None


def check_url_on_urlhaus(url_to_check: str) -> bool:
    print(f"\n--- DEBUG: Checking URLhaus for: {url_to_check} ---")
    try:
        api_url = "https://urlhaus-api.abuse.ch/v1/url/"
        response = requests.post(api_url, data={'url': url_to_check}, timeout=5)
        print(f"--- DEBUG: URLhaus Response: {response.json()} ---")
        if response.status_code == 200 and response.json().get("query_status") == "ok":
            return True
    except requests.RequestException as e:
        print(f"--- DEBUG: URLhaus API request failed: {e} ---")
    return False


def check_brand_impersonation(text: str) -> Optional[str]:
    BRAND_KEYWORDS = ['microsoft', 'google', 'apple', 'paypal', 'amazon', 'discord', 'steam']
    words_in_text = re.findall(r'\b\w{4,}\b', text.lower())  # Find words with 4+ letters
    for word in words_in_text:
        for brand in BRAND_KEYWORDS:
            similarity_score = fuzz.ratio(word, brand)
            if 85 < similarity_score < 100:
                return f"Potential brand impersonation: found '{word}', which is similar to '{brand}'."
    return None


# --- Pydantic Models ---
class Neighbor(BaseModel):
    similarity: float;
    label: str;
    text: str


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    score: int;
    label: str;
    reasons: list[str];
    neighbors: List[Neighbor] = []


# --- Main API Endpoint ---
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    text = request.text
    score, reasons, neighbors_found = 0, [], []
    text_lower = text.lower()

    # --- Rules Engine ---
    urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', text)
    if urls:
        reasons.append(f"Found {len(urls)} URL(s).")
        for url in urls:
            malicious_count = check_url_on_virustotal(url)
            if malicious_count and malicious_count > 0:
                score += 40 + (malicious_count * 2);
                reasons.append(f"URL flagged as malicious by {malicious_count} vendors on VirusTotal.")
            if check_url_on_urlhaus(url):
                score += 50;
                reasons.append("URL is listed on the URLhaus real-time threat list.")
            try:
                hostname = urllib.parse.urlparse(url).hostname
                if any(tld in hostname for tld in ['.zip', '.mov']):
                    score += 20;
                    reasons.append(f"Suspicious TLD found: {hostname}")
            except Exception:
                pass

    impersonation_reason = check_brand_impersonation(text)
    if impersonation_reason:
        score += 50;
        reasons.append(impersonation_reason)

    # --- AI Layer ---
    if state["model"] and state["faiss_index"]:
        query_embedding = state["model"].encode([text])
        distances, indices = state["faiss_index"].search(np.array(query_embedding, dtype='float32'), 3)
        for i in range(3):
            similarity = 1 / (1 + distances[0][i])
            if similarity > 0.65:
                meta_item = state["corpus_meta"][indices[0][i]]
                neighbors_found.append(Neighbor(similarity=round(similarity, 2), label=meta_item.get("label", "N/A"),
                                                text=meta_item.get("text", "")[:200] + "..."))
        if neighbors_found:
            score += int(neighbors_found[0].similarity * 25);
            reasons.append(
                f"Message is {neighbors_found[0].similarity:.0%} similar to a known '{neighbors_found[0].label}' sample.")

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