import joblib
import faiss
import json
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sklearn.decomposition import TruncatedSVD # <-- You might need this import if not already present

# --- Pydantic Models ---
class SimilarExample(BaseModel):
    text: str
    label: str
    distance: float

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    score: int
    label: str
    reasons: list[str]
    similar_examples: list[SimilarExample]

# --- App and Model Loading ---
app = FastAPI()
vectorizer = None
model = None
svd_transformer = None # <-- NEW: Add a variable for the SVD transformer
faiss_index = None
corpus_lookup = []

@app.on_event("startup")
def load_models():
    """Load all necessary models and data when the API starts."""
    global vectorizer, model, svd_transformer, faiss_index, corpus_lookup
    print("Loading models, SVD transformer, and Faiss index at startup...")
    try:
        vectorizer = joblib.load('vectorizer.joblib')
        model = joblib.load('model.joblib')
        svd_transformer = joblib.load('svd_transformer.joblib') # <-- NEW: Load the SVD transformer
        faiss_index = faiss.read_index('faiss_index.bin')
        with open('corpus_texts.json', 'r', encoding='utf-8') as f:
            corpus_lookup = json.load(f)
        print("✅ All models and data loaded successfully.")
    except FileNotFoundError as e:
        print(f"❌ ERROR: A required file was not found: {e.filename}")
        print("Please run train_model.py to generate all necessary files.")
        
# --- CORS Configuration ---
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Heuristic Reasons Function (remains the same) ---
def get_heuristic_reasons(text: str):
    reasons = []
    text_lower = text.lower()
    if "http" in text_lower or "www" in text_lower or ".com" in text_lower:
        reasons.append("Contains a link")
    if any(word in text_lower for word in ["urgent", "act now", "immediate", "verify", "warning"]):
        reasons.append("Uses urgency language")
    # ... etc
    return reasons

# --- API Endpoints ---
@app.get("/")
def read_root():
    if all([vectorizer, model, svd_transformer, faiss_index]):
        return {"Status": "API is running and all models are loaded."}
    return {"Status": "API is running, but one or more models FAILED to load."}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    if not all([vectorizer, model, svd_transformer, faiss_index]):
        raise HTTPException(status_code=503, detail="Models are not loaded. Server is not ready.")

    text_to_analyze = request.text
    
    # --- 1. CLASSIFICATION ---
    text_tfidf_sparse = vectorizer.transform([text_to_analyze])
    phishing_probability = model.predict_proba(text_tfidf_sparse)[0][1]
    score = int(phishing_probability * 100)
    label = "high_risk" if score >= 70 else "suspicious" if score >= 40 else "low_risk"
    reasons = get_heuristic_reasons(text_to_analyze)
    
    # --- 2. SIMILARITY SEARCH ---
    # --- THIS IS THE FIX ---
    # We must apply the SAME SVD transformation to the incoming text
    # that we applied to the training data.
    query_vector_dense = svd_transformer.transform(text_tfidf_sparse).astype('float32')
    
    faiss.normalize_L2(query_vector_dense)
    
    # Now, the query_vector_dense has 300 dimensions, matching the Faiss index.
    k = 3
    distances, indices = faiss_index.search(query_vector_dense, k)
    
    similar_examples = []
    for i in range(k):
        retrieved_index = indices[0][i]
        retrieved_example = corpus_lookup[retrieved_index]
        similar_examples.append(SimilarExample(
            text=retrieved_example['text'],
            label=retrieved_example['label'],
            distance=float(distances[0][i])
        ))
        
    return AnalyzeResponse(
        score=score, 
        label=label, 
        reasons=reasons, 
        similar_examples=similar_examples
    )

    

