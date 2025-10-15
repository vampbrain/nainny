"""
Lightweight story evaluator using sentence-transformers for semantic similarity
and simple heuristics for simplicity and cultural keyword presence.
"""
from typing import List
import re

_HAS_SENTE = False
try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SENTE = True
except Exception:
    _HAS_SENTE = False


class StoryEvaluator:
    """Evaluate adapted stories and return numeric scores."""

    def __init__(self):
        if _HAS_SENTE:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.model = None
        else:
            self.model = None

    def semantic_score(self, original: str, adapted: str) -> float:
        if self.model:
            e1 = self.model.encode(original, convert_to_tensor=True)
            e2 = self.model.encode(adapted, convert_to_tensor=True)
            return float(util.cos_sim(e1, e2).item())
        # fallback: simple word overlap
        o_words = set(re.findall(r"\w+", original.lower()))
        a_words = set(re.findall(r"\w+", adapted.lower()))
        if not o_words:
            return 0.0
        overlap = len(o_words & a_words) / float(len(o_words))
        return float(overlap)

    def simplicity_score(self, text: str) -> float:
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
        if not sentences:
            return 0.0
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        # shorter is simpler; map to 0..1 roughly
        return max(0.0, min(1.0, 2.0 / (avg + 1e-5)))

    def composite_score(self, base: str, adapted: str, target_culture: str) -> float:
        sem = self.semantic_score(base, adapted)
        simp = self.simplicity_score(adapted)
        culture_boost = 0.1 if target_culture.lower() in adapted.lower() else 0.0
        return float((0.7 * sem) + (0.2 * simp) + culture_boost)


__all__ = ["StoryEvaluator"]
