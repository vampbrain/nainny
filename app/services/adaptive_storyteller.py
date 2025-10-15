"""
Adaptive storyteller: rewriter that adapts stories for culture and age.

This module prefers using a seq2seq model (Flan-T5) when available but
falls back to a lightweight rule-based adaptor when transformers/torch
are not installed (useful for fast tests and environments without GPUs).
"""
from typing import Dict, Any

_HAS_TRANSFORMERS = False
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    _HAS_TRANSFORMERS = True
except Exception:
    # transformers not available; we will use a simple fallback method
    _HAS_TRANSFORMERS = False


class AdaptiveStoryteller:
    """Generate culturally- and age-appropriate story variants.

    If a transformer model is available it will be used. Otherwise a small
    rule-based rewriter is used (deterministic and fast, suitable for tests).
    """

    def __init__(self, model_name: str = "google/flan-t5-small"):
        self.model_name = model_name
        self.use_model = False
        if _HAS_TRANSFORMERS:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                # put model in eval mode
                self.model.eval()
                self.use_model = True
            except Exception:
                # silently fall back
                self.use_model = False

    def adapt(
        self,
        story_text: str,
        target_culture: str,
        target_age: str,
        concept_features: Dict[str, Any] = None,
        max_new_tokens: int = 256,
    ) -> str:
        """Return an adapted story string.

        Uses the loaded seq2seq model if available; otherwise applies
        a deterministic, conservative set of transformations:
        - Shorten sentences for younger ages
        - Replace culturally-specific keywords if mapping provided in concept_features
        - Add a header mentioning target culture/age
        """
        if self.use_model:
            # prepare a compact prompt containing concept hints
            concept_summary = ""
            if concept_features:
                keys = list(concept_features.keys())[:6]
                concept_summary = "Key concepts: " + ", ".join(keys) + ".\n"

            prompt = (
                f"Rewrite the following story for a {target_age} audience in the "
                f"{target_culture} culture. {concept_summary}Story:\n{story_text}"
            )
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=0.7,
                    top_p=0.95,
                )
            adapted = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return adapted

        # Fallback rule-based adaptation (quick and deterministic)
        adapted = story_text.strip()

        # Shorten for children: keep sentences short
        if any(t in target_age.lower() for t in ("child", "3-5", "6-8")):
            # naive split into sentences and truncate long ones
            import re

            sentences = re.split(r'(?<=[.!?]) +', adapted)
            short_sentences = []
            for s in sentences:
                words = s.split()
                if len(words) > 20:
                    short_sentences.append(" ".join(words[:18]) + "...")
                else:
                    short_sentences.append(s)
            adapted = " ".join(short_sentences)

        # Apply simple cultural keyword replacements if provided
        if concept_features and isinstance(concept_features, dict):
            for k, v in concept_features.items():
                try:
                    # v may suggest target concept name(s)
                    if isinstance(v, str):
                        adapted = adapted.replace(k, v)
                    elif isinstance(v, list) and v:
                        adapted = adapted.replace(k, v[0])
                except Exception:
                    pass

        # Tag the adapted story with a note (keeps output explicit for tests)
        header = f"(Adapted for {target_culture} / {target_age})\n"
        return header + adapted


__all__ = ["AdaptiveStoryteller"]
