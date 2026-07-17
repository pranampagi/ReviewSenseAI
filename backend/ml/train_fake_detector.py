"""Train the XGBoost fake-review detector and save model artifacts.

Usage::

    cd backend
    python -m ml.train_fake_detector --data ml/data/sample_fake_reviews.csv

CSV columns:
    - text (str): review body
    - label (int): 0 = real, 1 = fake
    - rating (int, optional): 1–5 star rating for mismatch feature
    - sentiment_score (float, optional): 0–1 score for mismatch feature

Artifacts written to ``ml/models/xgb_model.pkl`` and ``ml/models/tfidf_vectorizer.pkl``.
"""

import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from ml.fake_detector import _append_mismatch_column, rating_text_mismatch
from ml.pipeline import MODEL_DIR, build_feature_pipeline, preprocess_text

MODEL_DIR.mkdir(exist_ok=True)


def _mismatch_series(df: pd.DataFrame) -> list[int]:
    """Compute mismatch column from CSV rating/sentiment columns (defaults to 0)."""
    ratings = df["rating"].fillna(3).astype(int) if "rating" in df.columns else pd.Series([3] * len(df))
    scores = (
        df["sentiment_score"].fillna(0.5).astype(float)
        if "sentiment_score" in df.columns
        else pd.Series([0.5] * len(df))
    )
    return [rating_text_mismatch(int(r), float(s)) for r, s in zip(ratings, scores, strict=True)]


def train(data_path: str) -> None:
    """Fit the feature pipeline + XGBoost model and persist pickles."""
    df = pd.read_csv(data_path)
    df["clean"] = df["text"].apply(preprocess_text)

    X_train, X_test, y_train, y_test, train_df, test_df = train_test_split(
        df["clean"],
        df["label"],
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    pipeline = build_feature_pipeline()
    X_train_feat = pipeline.fit_transform(X_train)
    X_test_feat = pipeline.transform(X_test)

    train_mismatch = _mismatch_series(train_df)
    test_mismatch = _mismatch_series(test_df)
    X_train_feat = _append_mismatch_column(X_train_feat, train_mismatch)
    X_test_feat = _append_mismatch_column(X_test_feat, test_mismatch)

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train_feat, y_train, eval_set=[(X_test_feat, y_test)], verbose=50)

    print(classification_report(y_test, model.predict(X_test_feat)))

    with open(MODEL_DIR / "xgb_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(MODEL_DIR / "tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(pipeline, f)
    print("Models saved to", MODEL_DIR)


def generate_synthetic_csv(path: Path, n_per_class: int = 100) -> None:
    """Write a small labelled CSV for local training when no Kaggle dataset is available."""
    rows: list[dict] = []
    real_templates = [
        "Solid product for the price, works as described.",
        "Good quality but shipping took a week.",
        "Average experience, nothing special.",
        "Happy with purchase, would recommend to friends.",
        "Decent build, minor issues with packaging.",
        "Great product, fast shipping and excellent quality!",
        "Love it!",
        "Good value for money",
        "I recently purchased this and I'm absolutely loving it!",
        "Absolutely fantastic monitor for the price!",
        "The display itself is decent, but my experience was terrible.",
        "I am so happy with this bag. It is a good bag.",
        "It's an okay backpack, but definitely overpriced.",
        "Works great!",
        "Not bad, but could be better.",
        "Exactly what I needed.",
        "Five stars!",
        "Would buy again.",
    ]
    fake_templates = [
        "BEST PRODUCT EVER!!! BUY NOW!!! FIVE STARS!!!",
        "Amazing amazing amazing totally legit not fake at all!!!",
        "Perfect perfect perfect click here for discount!!!",
        "LOVE LOVE LOVE this changed my life must buy!!!",
        "Greatest item on earth five stars always!!!",
        "Click the link in my bio for 90% off this product!!!",
        "Make $5000 a day working from home using this item!",
        "SCAM SCAM SCAM DO NOT BUY THIS!!!",
        "I am a bot and this is a fake review.",
    ]

    for i in range(n_per_class):
        rows.append(
            {
                "text": f"{real_templates[i % len(real_templates)]} Review #{i}.",
                "label": 0,
                "rating": 3 + (i % 3),
                "sentiment_score": 0.55 + (i % 4) * 0.1,
            }
        )
        rows.append(
            {
                "text": f"{fake_templates[i % len(fake_templates)]} #{i}",
                "label": 1,
                "rating": 5,
                "sentiment_score": 0.15,
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Wrote synthetic dataset ({len(rows)} rows) to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train fake review XGBoost classifier")
    parser.add_argument("--data", help="Path to labelled CSV (text, label, …)")
    parser.add_argument(
        "--generate-synthetic",
        action="store_true",
        help="Write ml/data/sample_fake_reviews.csv then train on it",
    )
    args = parser.parse_args()

    if args.generate_synthetic:
        data_file = Path(__file__).parent / "data" / "sample_fake_reviews.csv"
        generate_synthetic_csv(data_file)
        train(str(data_file))
    elif args.data:
        train(args.data)
    else:
        parser.error("Provide --data PATH or --generate-synthetic")
