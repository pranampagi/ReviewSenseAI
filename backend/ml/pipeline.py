"""Scikit-learn text preprocessing for the fake-review XGBoost model.

Combines TF-IDF (unigrams + bigrams) with hand-crafted numeric features
(char count, caps ratio, etc.). Training saves the fitted pipeline to
``ml/models/tfidf_vectorizer.pkl`` (see ``train_fake_detector.py``, in later updates).
"""

import pickle
import re
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

MODEL_DIR = Path(__file__).parent / "models"


class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract numeric behavioural/linguistic features from raw review strings."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for text in X:
            words = text.split()
            features.append(
                [
                    len(text),
                    len(words),
                    np.mean([len(w) for w in words]) if words else 0,
                    sum(c.isupper() for c in text) / max(len(text), 1),
                    text.count("!"),
                    text.count("?"),
                    len(set(words)) / max(len(words), 1),
                ]
            )
        return np.array(features)


def build_feature_pipeline() -> FeatureUnion:
    """Return an unfitted FeatureUnion (TF-IDF + hand-crafted features)."""
    return FeatureUnion(
        [
            (
                "tfidf",
                TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True),
            ),
            ("hand_crafted", TextFeatureExtractor()),
        ]
    )


def load_tfidf() -> FeatureUnion:
    """Load the fitted feature pipeline saved during fake-detector training."""
    path = MODEL_DIR / "tfidf_vectorizer.pkl"
    with open(path, "rb") as f:
        return pickle.load(f)


def preprocess_text(text: str) -> str:
    """Normalise review text before vectorisation (lowercase, strip URLs/noise)."""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z0-9\s!?.,]", "", text)
    return text.strip()
