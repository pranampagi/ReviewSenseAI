"""XGBoost fake review classifier — load saved model and run inference."""

import pickle
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from ml.pipeline import preprocess_text

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

_model = None
_pipeline = None


def rating_text_mismatch(rating: int, sentiment_score: float) -> int:
    """1 when star rating strongly disagrees with sentiment score (spam signal)."""
    if rating >= 4 and sentiment_score < 0.4:
        return 1
    if rating <= 2 and sentiment_score > 0.7:
        return 1
    return 0


def _append_mismatch_column(features, mismatch: int | list[int]):
    """Horizontally stack TF-IDF features with the rating/sentiment mismatch column."""
    values = mismatch if isinstance(mismatch, list) else [mismatch]
    extra = np.array(values).reshape(-1, 1)
    if sp.issparse(features):
        return sp.hstack([features, sp.csr_matrix(extra)])
    return np.hstack([features, extra])


def _load() -> None:
    global _model, _pipeline
    if _model is None:
        with open(MODEL_DIR / "xgb_model.pkl", "rb") as f:
            _model = pickle.load(f)
        with open(MODEL_DIR / "tfidf_vectorizer.pkl", "rb") as f:
            _pipeline = pickle.load(f)


def predict(text: str, rating: int, sentiment_score: float) -> dict:
    """Return ``{"is_fake": bool, "fake_prob": float}`` for a single review."""
    _load()
    clean = preprocess_text(text)
    features = _pipeline.transform([clean])
    mismatch = rating_text_mismatch(rating, sentiment_score)
    full_features = _append_mismatch_column(features, mismatch)
    prob = float(_model.predict_proba(full_features)[0][1])
    return {"is_fake": prob > 0.5, "fake_prob": round(prob, 4)}
