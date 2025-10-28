"""
Confidence-based score dampening for short/ambiguous messages.

Problem: Short messages can trigger false positives because:
- "Click here" matches phishing patterns
- "Verify now" matches urgency keywords
- Limited text makes FAISS matching less reliable

Solution: Apply intelligent dampening based on message characteristics,
but preserve concrete evidence (URLs, strong intel signals).
"""
from typing import Dict, Any, Tuple, List
import re


def calculate_confidence(
    text: str,
    has_urls: bool,
    intel_score: int,
    signal_count: int,
    signals: Dict[str, Any]
) -> Tuple[float, List[str]]:
    """
    Calculate confidence factor (0.0 to 1.0) for the analysis.
    
    Higher confidence = less dampening applied to final score.
    
    Args:
        text: Message text
        has_urls: Whether message contains URLs (concrete evidence)
        intel_score: Score from threat intel (VT + URLHaus)
        signal_count: Number of non-zero signals
        signals: All signal scores for detailed analysis
        
    Returns:
        (confidence_factor, reasons)
        - confidence_factor: 0.0 to 1.0 (1.0 = full confidence, no dampening)
        - reasons: List of explanations for confidence adjustments
    """
    confidence = 1.0
    reasons = []
    
    # Count words (simple whitespace split)
    words = text.strip().split()
    word_count = len(words)
    
    # Factor 1: Message Length
    # Very short messages are less reliable unless they have concrete evidence
    if word_count <= 3:
        length_factor = 0.4
        reasons.append(f"Very short message ({word_count} words) - confidence reduced")
    elif word_count <= 8:
        length_factor = 0.6
        reasons.append(f"Short message ({word_count} words) - confidence reduced")
    elif word_count <= 15:
        length_factor = 0.8
    else:
        length_factor = 1.0  # Normal length, full confidence
    
    # Factor 2: Concrete Evidence (URLs)
    # If message has URLs, we have concrete evidence - high confidence
    if has_urls:
        url_factor = 1.0  # Don't dampen URL-based evidence
        if word_count <= 8:
            reasons.append("URL present - maintaining confidence despite short length")
    else:
        url_factor = length_factor  # Apply length dampening
    
    # Factor 3: Intel Strength
    # Strong intel (VT/URLHaus hits) = concrete evidence
    if intel_score >= 50:  # Strong intel signal
        intel_factor = 1.0
        if not has_urls:
            reasons.append("Strong threat intel - high confidence")
    elif intel_score >= 20:  # Moderate intel
        intel_factor = 0.9
    else:
        intel_factor = url_factor  # No strong intel, use URL factor
    
    # Factor 4: Signal Diversity
    # Multiple independent signals = higher confidence
    if signal_count >= 3:
        diversity_factor = 1.0
    elif signal_count >= 2:
        diversity_factor = 0.95
    else:
        diversity_factor = 0.85
        if word_count <= 8 and not has_urls:
            reasons.append("Single signal source - confidence reduced")
    
    # Combine factors
    # Intel strength is most important, then URL presence, then length
    if intel_score >= 50 or has_urls:
        # Strong concrete evidence - minimal dampening
        confidence = max(intel_factor, url_factor) * diversity_factor
    else:
        # Soft signals only - apply length-based dampening
        confidence = length_factor * diversity_factor
    
    # Ensure confidence is in valid range
    confidence = max(0.3, min(1.0, confidence))  # Floor at 0.3, never zero out
    
    return confidence, reasons


def apply_confidence_dampening(
    score: int,
    text: str,
    urls: List[str],
    signals: Dict[str, Any]
) -> Tuple[int, List[str]]:
    """
    Apply confidence-based dampening to the final score.
    
    Args:
        score: Initial score (0-100)
        text: Message text
        urls: Extracted URLs
        signals: Signal breakdown from scoring engine
        
    Returns:
        (adjusted_score, confidence_reasons)
    """
    # Extract signal information
    has_urls = len(urls) > 0
    intel_score = signals.get("intel", {}).get("score", 0)
    
    # Count non-zero signals
    signal_count = sum(
        1 for sig_name, sig_data in signals.items()
        if isinstance(sig_data, dict) and sig_data.get("score", 0) > 0
    )
    
    # Calculate confidence
    confidence, reasons = calculate_confidence(
        text=text,
        has_urls=has_urls,
        intel_score=intel_score,
        signal_count=signal_count,
        signals=signals
    )
    
    # Apply dampening
    adjusted_score = int(round(score * confidence))
    
    # Add explanation if dampening was applied
    if confidence < 1.0:
        dampening_pct = int((1.0 - confidence) * 100)
        reasons.append(
            f"Confidence dampening: {dampening_pct}% reduction applied "
            f"(score: {score} -> {adjusted_score})"
        )
    
    return adjusted_score, reasons


# Example usage and test cases
if __name__ == "__main__":
    print("="*70)
    print("CONFIDENCE SCORING EXAMPLES")
    print("="*70)
    
    test_cases = [
        {
            "name": "Short benign",
            "text": "Hey there",
            "urls": [],
            "intel_score": 0,
            "signal_count": 1,
            "initial_score": 30
        },
        {
            "name": "Short with URL",
            "text": "Click here: malicious.com",
            "urls": ["http://malicious.com"],
            "intel_score": 60,
            "signal_count": 2,
            "initial_score": 80
        },
        {
            "name": "Short suspicious",
            "text": "URGENT verify now",
            "urls": [],
            "intel_score": 0,
            "signal_count": 1,
            "initial_score": 40
        },
        {
            "name": "Long phishing",
            "text": "Dear valued customer, we detected suspicious activity on your account. Please verify your identity immediately to avoid suspension.",
            "urls": [],
            "intel_score": 0,
            "signal_count": 2,
            "initial_score": 70
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        print(f"Text: {case['text'][:60]}...")
        print(f"Initial score: {case['initial_score']}")
        
        signals = {
            "intel": {"score": case['intel_score']},
            "neighbors": {"score": 20 if case['signal_count'] > 1 else 0}
        }
        
        adjusted, reasons = apply_confidence_dampening(
            score=case['initial_score'],
            text=case['text'],
            urls=case['urls'],
            signals=signals
        )
        
        print(f"Adjusted score: {adjusted}")
        for r in reasons:
            print(f"  - {r}")

