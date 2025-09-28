import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    score: int
    label: str
    reasons: list[str]

app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"Status": "API is running"}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Analyzes the incoming text and returns a mock phishing analysis.
    """
    text = request.text
    score = 0
    reasons = []

    # Simple mock logic
    if "http" in text:
        score += 30
        reasons.append("Contains a URL")
    if "act now" in text.lower() or "urgent" in text.lower():
        score += 40
        reasons.append("Urgency language detected")
    if "password" in text.lower() or "account" in text.lower():
        score += 25
        reasons.append("Keywords like 'password' or 'account' found")

    # Determine label
    score = min(score, 100)
    if score >= 70:
        label = "high_risk"
    elif score >= 40:
        label = "suspicious"
    else:
        label = "low_risk"
        if not reasons:
            reasons.append("No immediate signs of phishing found")

    return AnalyzeResponse(score=score, label=label, reasons=reasons)

