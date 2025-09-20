"""
Lightweight semantic utilities with optional embeddings.

Attempts to use sentence-transformers if available; otherwise falls back to
string similarity for a coarse semantic-like signal.
"""
from __future__ import annotations

from typing import Optional, List

import math

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore


class SemanticEmbedder:
    """Abstraction for embeddings with graceful fallback."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self._model = None
        self._use_model = False
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(self.model_name)
            self._use_model = True
        except Exception:
            self._use_model = False

    def embed(self, texts: List[str]):
        if self._use_model and self._model is not None:
            return self._model.encode(texts, normalize_embeddings=True)
        # Fallback: return None to indicate not available
        return None

    def similarity(self, a: str, b: str) -> float:
        """Compute semantic similarity.

        If embeddings available, cosine similarity; otherwise fallback to
        token set overlap using RapidFuzz if present.
        """
        # Try simple embedding for two texts
        if self._use_model and self._model is not None and np is not None:
            vecs = self.embed([a, b])
            if vecs is not None:
                v1, v2 = vecs[0], vecs[1]
                # Since embeddings are normalized, dot = cosine
                try:
                    return float(np.dot(v1, v2))
                except Exception:
                    pass
        try:
            from rapidfuzz import fuzz  # type: ignore
            # Scale to 0..1
            return float(fuzz.token_set_ratio(a, b) / 100.0)
        except Exception:
            # Minimal fallback: Jaccard over tokens
            set_a = set(w for w in a.lower().split())
            set_b = set(w for w in b.lower().split())
            if not set_a or not set_b:
                return 0.0
            inter = len(set_a & set_b)
            union = len(set_a | set_b)
            return inter / union if union else 0.0

