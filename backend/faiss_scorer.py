# backend/faiss_scorer.py
"""
Quantitative FAISS scoring with continuous 0-100 output.
No hard thresholds - all neighbors contribute based on weighted similarity.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import os
import json
import math
import numpy as np


def sims_from_dist(d: np.ndarray) -> np.ndarray:
    """
    Convert FAISS L2 distances to similarities in (0,1].
    For cosine/IP index, adjust accordingly.
    """
    d = d.ravel().astype("float32")
    return 1.0 / (1.0 + np.maximum(0.0, d))


def softmax(x: np.ndarray, tau: float = 10.0) -> np.ndarray:
    """
    Temperatured softmax for neighbor weighting.
    Higher tau = more peaked (emphasizes top matches).
    """
    z = (tau * x).astype("float32")
    z -= z.max()  # Numerical stability
    e = np.exp(z)
    return e / (e.sum() + 1e-8)


@dataclass
class FaissDiagnostics:
    """Diagnostic information for FAISS scoring"""
    p_raw: float        # Raw probability before calibration
    p_cal: float        # Calibrated probability
    n_eff: float        # Effective number of neighbors
    entropy: float      # Shannon entropy of weights
    top_sim: float      # Highest similarity score
    k: int             # Number of neighbors used
    has_labels: bool   # Whether corpus has labels
    tau: float         # Temperature parameter
    a: float           # Platt scaling parameter a
    b: float           # Platt scaling parameter b
    alpha_ctx: float   # Context modulation factor


class FaissScorer:
    """
    Continuous FAISS scoring system.
    
    Converts neighbor similarities to a smooth 0-100 score using:
    - Softmax weighting (no hard thresholds)
    - Label-aware scoring (if corpus has labels)
    - Platt calibration (optional)
    - Context modulation from threat intel (optional)
    """
    
    def __init__(
        self,
        faiss_index,
        corpus_meta: List[Dict[str, Any]],
        encoder,
        k: int = None,
        tau: float = None,
        calibration_path: str = "backend/calibration.json",
        pos_labels: Tuple[str, ...] = ("phishing", "malicious", "spam")
    ):
        self.index = faiss_index
        self.meta = corpus_meta or []
        self.enc = encoder
        
        # Configuration
        self.k = int(os.getenv("FAISS_K", str(k if k is not None else 8)))
        self.tau = float(os.getenv("FAISS_TAU", str(tau if tau is not None else 10.0)))
        
        # Platt calibration (a, b)
        # Default: a=1.5, b=-1.0 shifts sigmoid down to reduce false positives
        # This makes benign messages score lower (more reasonable)
        self.a, self.b = 1.5, -1.0
        if os.path.exists(calibration_path):
            try:
                cal = json.load(open(calibration_path))
                self.a = float(cal.get("a", 1.5))
                self.b = float(cal.get("b", -1.0))
            except Exception:
                pass
        
        # Build label vector if corpus has labels
        self.y = None
        if self.meta and "label" in self.meta[0]:
            labs = set(s.lower() for s in pos_labels)
            ys = [
                1 if str(m.get("label", "")).lower() in labs else 0
                for m in self.meta
            ]
            self.y = np.array(ys, dtype="float32")
    
    def _platt(self, p_raw: float) -> float:
        """Logistic calibration (Platt scaling)"""
        return 1.0 / (1.0 + math.exp(-(self.a * p_raw + self.b)))
    
    def score_text(
        self,
        text: str,
        intel_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, FaissDiagnostics, List[Dict[str, Any]]]:
        """
        Score text using FAISS neighbors with continuous output.
        
        Args:
            text: Text to analyze
            intel_context: Optional context from VT/URLHaus for modulation
            
        Returns:
            (score, diagnostics, neighbors)
            - score: 0-100 integer
            - diagnostics: FaissDiagnostics object
            - neighbors: List of neighbor dicts with similarity/label/text
        """
        # 1) Embed and search
        vec = np.array(self.enc.encode([text]), dtype="float32")
        D, I = self.index.search(vec, self.k)
        d = D[0]      # distances
        idxs = I[0]   # indices
        
        # 2) Convert to similarities and compute weights
        sim = sims_from_dist(d)              # (k,) array in (0,1]
        w = softmax(sim, tau=self.tau)       # (k,) softmax weights
        top = float(sim.max(initial=0.0))
        
        # 3) Compute raw probability
        if self.y is not None:
            # Labeled corpus: weighted average of labels
            yk = self.y[idxs]
            p_raw = float((w * yk).sum())
            has_labels = True
        else:
            # Unlabeled corpus: use "outlierness"
            # Lower average similarity → higher suspicion
            p_raw = float(1.0 - (w * sim).sum())
            has_labels = False
        
        # 4) Compute diagnostics
        n_eff = float(1.0 / (np.square(w).sum() + 1e-12))
        entropy = float(-(w * np.log(w + 1e-12)).sum())
        
        # 5) Calibrate to 0-1 probability
        p_cal = float(self._platt(p_raw))
        faiss_score = int(round(100.0 * np.clip(p_cal, 0.0, 1.0)))
        
        # 6) Optional context modulation from intel
        alpha = 1.0
        if intel_context:
            urlhaus_hit = intel_context.get("urlhaus_hit", False)
            vt_malicious = int(intel_context.get("vt_malicious_max", 0))
            vt_all_clean = bool(intel_context.get("vt_all_clean", False))
            
            if urlhaus_hit:
                alpha = 1.10      # Boost if URLHaus confirms
            elif vt_malicious >= 3:
                alpha = 1.05      # Slight boost if VT flags
            elif vt_all_clean:
                alpha = 0.90      # Dampen if all clean
        
        faiss_score = int(round(np.clip(faiss_score * alpha, 0, 100)))
        
        # 7) Build neighbor payload for UI
        neighbors = []
        for rank, (ii, s) in enumerate(zip(idxs.tolist(), sim.tolist()), start=1):
            m = self.meta[ii] if 0 <= ii < len(self.meta) else {}
            neighbors.append({
                "rank": rank,
                "idx": ii,
                "similarity": round(float(s), 4),
                "label": m.get("label", "N/A"),
                "text": (m.get("text", "")[:200] + "...") if m.get("text") else ""
            })
        
        # 8) Package diagnostics
        diag = FaissDiagnostics(
            p_raw=p_raw,
            p_cal=p_cal,
            n_eff=n_eff,
            entropy=entropy,
            top_sim=top,
            k=len(sim),
            has_labels=has_labels,
            tau=self.tau,
            a=self.a,
            b=self.b,
            alpha_ctx=alpha
        )
        
        return faiss_score, diag, neighbors

