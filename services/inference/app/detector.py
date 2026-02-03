"""AI-generated image detection using a HuggingFace ViT-based classifier."""

from __future__ import annotations

import io
import logging

from PIL import Image

from app.config import settings

logger = logging.getLogger("verifai.detector")

# Lazy-loaded model and processor
_model = None
_processor = None


def _load_model():
    """Load the model and processor on first use."""
    global _model, _processor

    if _model is not None:
        return

    try:
        from transformers import AutoFeatureExtractor, AutoModelForImageClassification

        logger.info("Loading model %s...", settings.model_name)
        _processor = AutoFeatureExtractor.from_pretrained(
            settings.model_name,
            cache_dir=settings.model_cache_dir,
        )
        _model = AutoModelForImageClassification.from_pretrained(
            settings.model_name,
            cache_dir=settings.model_cache_dir,
        )
        _model.eval()
        logger.info("Model loaded successfully.")
    except Exception:
        logger.exception("Failed to load model %s", settings.model_name)
        _model = None
        _processor = None


def detect(image_bytes: bytes) -> int | None:
    """Run AI-detection inference on the supplied image.

    Returns an integer 0-100 representing AI likelihood, or None if
    the detector is unavailable.
    """
    try:
        _load_model()

        if _model is None or _processor is None:
            logger.warning("Model not available, returning None")
            return None

        import torch

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Resize if too large to avoid OOM on CPU
        max_dim = settings.max_image_dimension
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)

        inputs = _processor(images=img, return_tensors="pt")

        with torch.inference_mode():
            outputs = _model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)

        # The model has two classes: "human" (real) and "ai" (generated)
        # Label mapping: 0 = "human", 1 = "ai" (for umm-maybe/AI-image-detector)
        labels = _model.config.id2label
        ai_index = None
        for idx, label in labels.items():
            if "ai" in label.lower() or "artificial" in label.lower() or "fake" in label.lower():
                ai_index = int(idx)
                break

        if ai_index is None:
            # Fallback: assume last class is "ai"
            ai_index = len(labels) - 1

        ai_prob = probs[0][ai_index].item()
        score = int(round(ai_prob * 100))
        score = max(0, min(100, score))

        logger.info("Detection score: %d (AI probability: %.4f)", score, ai_prob)
        return score

    except Exception:
        logger.exception("Detection failed")
        return None
