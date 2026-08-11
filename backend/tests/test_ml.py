"""Unit tests for ML helpers and optional model inference."""

from pathlib import Path

import numpy as np
import pytest

from ml.fake_detector import rating_text_mismatch
from ml.pipeline import TextFeatureExtractor, build_feature_pipeline, preprocess_text

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml" / "models"
HAS_FAKE_MODEL = (MODEL_DIR / "xgb_model.pkl").exists() and (
    MODEL_DIR / "tfidf_vectorizer.pkl"
).exists()
HAS_ASPECT_MODEL = (MODEL_DIR / "aspect_model.pt").exists() and (
    MODEL_DIR / "aspect_vocab.json"
).exists()


def test_preprocess_text_normalises() -> None:
    raw = "Check https://spam.example/NOW!!! Great Product???"
    clean = preprocess_text(raw)
    assert "http" not in clean
    assert clean == clean.lower()
    assert "great product" in clean


def test_rating_text_mismatch_flags_disagreement() -> None:
    assert rating_text_mismatch(5, 0.2) == 1
    assert rating_text_mismatch(1, 0.9) == 1
    assert rating_text_mismatch(5, 0.85) == 0
    assert rating_text_mismatch(3, 0.5) == 0


def test_text_feature_extractor_shape() -> None:
    extractor = TextFeatureExtractor()
    features = extractor.fit_transform(["Amazing product!!!", "meh"])
    assert features.shape == (2, 7)
    assert np.all(np.isfinite(features))


def test_build_feature_pipeline_fit_transform() -> None:
    pipeline = build_feature_pipeline()
    texts = [
        "Fantastic quality and fast shipping.",
        "Terrible service, never again.",
        "Okay price but average build.",
    ]
    matrix = pipeline.fit_transform(texts)
    assert matrix.shape[0] == 3
    assert matrix.shape[1] > 7


@pytest.mark.skipif(not HAS_FAKE_MODEL, reason="Fake detector artifacts not trained locally")
def test_fake_detector_predict_returns_prob() -> None:
    from ml.fake_detector import predict

    result = predict(
        "BUY NOW CLICK HERE AMAZING DEAL FREE MONEY!!!",
        rating=5,
        sentiment_score=0.95,
    )
    assert "is_fake" in result
    assert "fake_prob" in result
    assert 0.0 <= result["fake_prob"] <= 1.0
    assert isinstance(result["is_fake"], bool)


@pytest.mark.skipif(not HAS_ASPECT_MODEL, reason="Aspect model artifacts not trained locally")
def test_aspect_predict_returns_four_scores() -> None:
    from ml.aspect.infer import predict_aspects

    scores = predict_aspects(
        "Great price and excellent quality, but shipping was slow and support was rude."
    )
    assert set(scores.keys()) == {"price", "quality", "shipping", "service"}
    for value in scores.values():
        assert 0.0 <= value <= 1.0
