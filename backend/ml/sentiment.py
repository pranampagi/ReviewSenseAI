"""HuggingFace DistilBERT sentiment analysis wrapper.

Model ID defaults to ``distilbert-base-uncased-finetuned-sst-2-english`` (see ``HF_MODEL_ID``).
The pipeline is loaded once at app startup and reused for all requests.
"""

from transformers import pipeline as hf_pipeline

from app.config import settings

_pipeline = None


def get_sentiment_pipeline():
    """Return the module-level sentiment pipeline, downloading the model on first call."""
    global _pipeline
    if _pipeline is None:
        _pipeline = hf_pipeline(
            "sentiment-analysis",
            model=settings.hf_model_id,
            truncation=True,
            max_length=512,
        )
    return _pipeline


def analyse(text: str) -> dict:
    """Classify review text as POSITIVE or NEGATIVE with a positivity score.

    Returns ``{"sentiment": "POSITIVE"|"NEGATIVE", "sentiment_score": float}``.
    """
    result = get_sentiment_pipeline()(text[:1000])[0]
    score = float(result["score"])
    if result["label"] == "NEGATIVE":
        score = 1.0 - score

    return {
        "sentiment": result["label"],
        "sentiment_score": round(score, 4),
    }
