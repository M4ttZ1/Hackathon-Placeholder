# backend/scoring_engine.py
"""
Robust scoring engine that blends multiple signals:
- VirusTotal & URLHaus intel
- FAISS semantic similarity
- Keywords & urgency signals
- Obfuscation detection
- Brand impersonation (contextual)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import os

# Thresholds
VT_MALICIOUS_STRONG = int(os.getenv("VT_MALICIOUS_STRONG", "5"))

@dataclass
class Subscore:
    """Individual scoring component"""
    name: str
    score: int
    reasons: List[str] = field(default_factory=list)
    debug: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScoringResult:
    """Final scoring result with all details"""
    score: int
    label: str
    reasons: List[str]
    signals: Dict[str, Any]
    neighbors: Optional[List[Dict[str, Any]]] = None
    url_intel: Optional[List[Dict[str, Any]]] = None

class ScoringEngine:
    """
    Modular scoring engine that blends multiple threat signals.
    
    Labels:
    - confirmed_phishing: URLHaus hit OR VT malicious >= 5
    - high_risk: score >= 70
    - suspicious: score >= 40
    - low_risk: score >= 10
    - benign: score < 10
    """
    
    @staticmethod
    def _label_from(score: int, urlhaus_hit: bool, vt_malicious_max: int) -> str:
        """Determine label based on score and intel signals"""
        if urlhaus_hit or vt_malicious_max >= VT_MALICIOUS_STRONG:
            return "confirmed_phishing"
        if score >= 70:
            return "high_risk"
        if score >= 40:
            return "suspicious"
        if score >= 10:
            return "low_risk"
        return "benign"
    
    def fold_intel(self, url_checks: List[Dict[str, Any]]) -> Subscore:
        """
        Process VirusTotal and URLHaus results.
        
        Scoring:
        - URLHaus malicious: +60
        - VT malicious: +10 + 5 * min(8, count)
        - VT suspicious: +5 + 3 * min(5, count)
        
        Intel score capped at 75 to avoid dominance.
        """
        score = 0
        reasons: List[str] = []
        vt_max_mal = 0
        urlhaus_hit = False
        
        for check in url_checks or []:
            url = check.get("url", "")
            vt = check.get("virustotal", {})
            uh = check.get("urlhaus", {})
            
            # URLHaus
            if uh.get("status") == "malicious":
                urlhaus_hit = True
                score += 60
                threat = uh.get("threat", "malware")
                url_status = uh.get("url_status", "")
                reasons.append(f"URLHaus: {threat} ({url_status}) — {url}")
            
            # VirusTotal
            status = vt.get("status")
            if status == "ok":
                mal = int(vt.get("malicious", 0))
                sus = int(vt.get("suspicious", 0))
                vt_max_mal = max(vt_max_mal, mal)
                
                if mal > 0:
                    delta = 10 + 5 * min(8, mal)
                    score += delta
                    reasons.append(f"VirusTotal: {mal} vendors flagged {url} as malicious (+{delta}).")
                elif sus > 0:
                    delta = 5 + 3 * min(5, sus)
                    score += delta
                    reasons.append(f"VirusTotal: {sus} vendors marked {url} as suspicious (+{delta}).")
            elif status == "not_found":
                reasons.append(f"VirusTotal: URL not in database ({url}).")
        
        # Cap intel to avoid complete dominance
        score = min(score, 75)
        
        return Subscore(
            name="intel",
            score=score,
            reasons=reasons,
            debug={
                "vt_max_malicious": vt_max_mal,
                "urlhaus_hit": urlhaus_hit
            }
        )
    
    def fold_neighbors(self, neighbors: List[Dict[str, Any]]) -> Subscore:
        """
        Score based on FAISS semantic similarity.
        
        Scoring: +round(25 * similarity) for top match
        """
        score = 0
        reasons: List[str] = []
        
        if neighbors:
            top = neighbors[0]
            sim = float(top.get("similarity", 0.0))
            score += round(25 * max(0.0, min(1.0, sim)))
            label = top.get("label", "sample")
            reasons.append(f"Message {sim:.0%} similar to known '{label}' sample.")
        
        return Subscore(
            name="neighbors",
            score=score,
            reasons=reasons,
            debug={"top_similarity": sim if neighbors else 0}
        )
    
    def fold_keywords(self, text_lower: str) -> Subscore:
        """
        Detect urgency and payment keywords.
        
        Scoring: +20 if suspicious keywords found
        """
        score = 0
        reasons = []
        
        urgency_words = ["urgent", "verify", "suspended", "immediately", "action required"]
        payment_words = ["gift card", "bitcoin", "wire", "crypto", "paypal", "venmo"]
        
        found_urgency = any(k in text_lower for k in urgency_words)
        found_payment = any(k in text_lower for k in payment_words)
        
        if found_urgency and found_payment:
            score += 30
            reasons.append("Urgency keywords + payment method detected.")
        elif found_urgency:
            score += 15
            reasons.append("Urgency keywords detected.")
        elif found_payment:
            score += 15
            reasons.append("Suspicious payment method mentioned.")
        
        return Subscore("keywords", score, reasons, {})
    
    def fold_brand(self, text: str, context_risky: bool) -> Subscore:
        """
        Detect brand impersonation (fuzzy matching).
        
        Only scores if context is risky (other signals present).
        Scoring: +10 if brand lookalike detected
        """
        if not context_risky:
            return Subscore("brand", 0, [], {"skipped": "no_risky_context"})
        
        # Use existing brand impersonation check
        from main import check_brand_impersonation
        result = check_brand_impersonation(text)
        
        if result:
            return Subscore("brand", 10, [result], {})
        
        return Subscore("brand", 0, [], {})
    
    def fold_suspicious_patterns(self, text: str, urls: List[str]) -> Subscore:
        """
        Detect suspicious patterns (TLDs, IP addresses, etc.)
        
        Scoring:
        - Suspicious TLD (.zip, .tk, etc.): +20
        - IP address in URL: +15
        - Port number in URL: +10
        """
        score = 0
        reasons = []
        
        from urllib.parse import urlparse
        import re
        
        for url in urls:
            try:
                parsed = urlparse(url)
                hostname = parsed.hostname or ""
                
                # Suspicious TLDs
                suspicious_tlds = ['.zip', '.mov', '.tk', '.ml', '.ga', '.cf']
                if any(tld in hostname for tld in suspicious_tlds):
                    score += 20
                    reasons.append(f"Suspicious TLD in URL: {hostname}")
                
                # IP address instead of domain
                if re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname):
                    score += 15
                    reasons.append(f"IP address used instead of domain: {hostname}")
                
                # Non-standard port
                if parsed.port and parsed.port not in [80, 443]:
                    score += 10
                    reasons.append(f"Non-standard port {parsed.port} in URL")
                
            except Exception:
                pass
        
        return Subscore("patterns", score, reasons, {})
    
    def blend(self, *subs: Subscore) -> Tuple[int, List[str], Dict[str, Any]]:
        """Combine all subscores into final score and reasons"""
        total = 0
        reasons = []
        signals = {}
        
        for s in subs:
            total += s.score
            reasons.extend(s.reasons)
            signals[s.name] = {"score": s.score, **s.debug}
        
        # Clamp to 0-100
        total = max(0, min(100, total))
        
        # Deduplicate reasons while preserving order
        seen = set()
        unique_reasons = []
        for r in reasons:
            if r not in seen:
                unique_reasons.append(r)
                seen.add(r)
        
        return total, unique_reasons, signals
    
    def score_message(
        self,
        text: str,
        neighbors: List[Dict[str, Any]],
        url_checks: List[Dict[str, Any]],
        urls: List[str],
        faiss_score: Optional[int] = None,
        faiss_diagnostics: Optional[Dict[str, Any]] = None
    ) -> ScoringResult:
        """
        Main scoring function that blends all signals.
        
        Args:
            text: Message text
            neighbors: FAISS neighbor matches
            url_checks: Combined VT + URLHaus results
            urls: Extracted URLs from text
            faiss_score: Pre-computed FAISS score (0-100) from FaissScorer
            faiss_diagnostics: Diagnostics from FaissScorer
            
        Returns:
            ScoringResult with score, label, reasons, and debug info
        """
        text_lower = text.lower()
        
        # Calculate subscores
        intel = self.fold_intel(url_checks)
        
        # Use pre-computed FAISS score if available, otherwise fall back to old method
        if faiss_score is not None:
            # Use the dynamic FAISS score directly (already 0-100)
            # Scale it to our weight range: FAISS can contribute up to 35 points
            faiss_contribution = int(round(faiss_score * 0.35))
            
            # Build a Subscore object for blending
            neigh_reasons = []
            if neighbors:
                top = neighbors[0]
                neigh_reasons.append(
                    f"FAISS (dynamic): {faiss_score}/100 score, "
                    f"top match {top.get('similarity', 0):.2f} similarity to '{top.get('label', 'sample')}'"
                )
            
            neigh = Subscore(
                name="neighbors",
                score=faiss_contribution,
                reasons=neigh_reasons,
                debug=faiss_diagnostics or {}
            )
        else:
            # Fallback to old threshold method
            neigh = self.fold_neighbors(neighbors)
        
        kw = self.fold_keywords(text_lower)
        patterns = self.fold_suspicious_patterns(text, urls)
        
        # Brand only scores if context is risky
        context_risky = (intel.score > 0) or (kw.score > 0) or (patterns.score > 0)
        brand = self.fold_brand(text, context_risky)
        
        # Blend all signals
        total, reasons, signals = self.blend(intel, neigh, kw, patterns, brand)
        
        # Apply confidence-based dampening for short messages
        from confidence_scoring import apply_confidence_dampening
        adjusted_score, confidence_reasons = apply_confidence_dampening(
            score=total,
            text=text,
            urls=urls,
            signals=signals
        )
        
        # Add confidence reasons if dampening was applied
        if confidence_reasons:
            reasons.extend(confidence_reasons)
        
        # Determine label using adjusted score
        vt_max_mal = signals["intel"].get("vt_max_malicious", 0)
        urlhaus_hit = bool(signals["intel"].get("urlhaus_hit"))
        label = self._label_from(adjusted_score, urlhaus_hit, vt_max_mal)
        
        return ScoringResult(
            score=adjusted_score,
            label=label,
            reasons=reasons if reasons else ["No threats detected."],
            signals=signals,
            neighbors=neighbors,
            url_intel=url_checks
        )

