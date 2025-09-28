import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- Pydantic Models (Defines the shape of API requests/responses) ---
class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    score: int
    label: str
    reasons: list[str]

# --- App and Model Loading ---
app = FastAPI()

# This is a critical section. We load the model files ONCE when the app starts.
# This is much more efficient than loading them for every single request.
try:
    vectorizer = joblib.load('vectorizer.joblib')
    model = joblib.load('model.joblib')
    print("Vectorizer and model loaded successfully at startup.")
except FileNotFoundError:
    print("ERROR: Model files not found. Please run train_model.py first.")
    vectorizer = None
    model = None

# --- CORS Configuration (Allows your frontend to connect) ---
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Heuristic Reasons Function ---
# The ML model gives a score, but not human-readable reasons.
# We can add simple rules to provide context, similar to your old mock logic.
def get_heuristic_reasons(text: str):
    reasons = []
    text_lower = text.lower()
    if "http" in text_lower or "www" in text_lower or ".com" in text_lower:
        reasons.append("Contains a link")
    if any(word in text_lower for word in ["urgent", "act now", "immediate", "verify", "warning"]):
        reasons.append("Uses urgency language")
    if any(word in text_lower for word in ["winner", "congratulations", "free", "claim", "prize"]):
        reasons.append("Contains promotional keywords")
    if any(word in text_lower for word in ["password", "account", "login", "ssn", "bank"]):
        reasons.append("Requests sensitive information")
    return reasons

# --- API Endpoints ---
@app.get("/")
def read_root():
    if model and vectorizer:
        return {"Status": "API is running and model is loaded."}
    return {"Status": "API is running, but the MODEL IS NOT LOADED."}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    if not model or not vectorizer:
        raise HTTPException(status_code=500, detail="Model is not loaded. Cannot process request.")

    text_to_analyze = request.text
    
    # --- The Machine Learning Prediction Happens Here ---
    
    # 1. Transform the user's text into numbers using the loaded vectorizer.
    text_tfidf = vectorizer.transform([text_to_analyze])
    
    # 2. Use the loaded model to predict the probability of it being phishing.
    # The result is in the format: [[probability_of_safe, probability_of_phishing]]
    phishing_probability = model.predict_proba(text_tfidf)[0][1]
    
    # 3. Convert the probability (a float from 0.0 to 1.0) to an integer score (0-100).
    score = int(phishing_probability * 100)
    
    # 4. Determine a human-readable label based on the score.
    if score >= 70:
        label = "high_risk"
    elif score >= 40:
        label = "suspicious"
    else:
        label = "low_risk"
        
    # 5. Get some simple, contextual reasons to show the user.
    reasons = get_heuristic_reasons(text_to_analyze)
    if label == "low_risk" and not reasons:
        reasons.append("No common phishing indicators found.")
        
    return AnalyzeResponse(score=score, label=label, reasons=reasons)

