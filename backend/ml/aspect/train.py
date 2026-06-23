"""Train the biLSTM aspect sentiment model and save the best checkpoint.

Usage::

    cd backend
    python -m ml.aspect.train --data path/to/aspect_reviews.csv --epochs 10
    python -m ml.aspect.train --generate-synthetic --epochs 3

CSV columns: ``text`` (str), ``price``, ``quality``, ``shipping``, ``service`` (float 0–1).

Artifacts: ``ml/models/aspect_model.pt``, ``ml/models/aspect_vocab.json``.
"""

import argparse
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, random_split

from ml.aspect.dataset import ASPECTS, AspectDataset, Tokenizer
from ml.aspect.model import AspectSentimentModel

MODEL_DIR = Path(__file__).parent.parent / "models"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
VOCAB_SIZE = 10000


def train(data_path: str, epochs: int = 10, batch_size: int = 32, lr: float = 1e-3) -> None:
    """Fit tokenizer + model; persist best checkpoint by validation loss."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path).dropna(subset=["text"])
    tokenizer = Tokenizer(vocab_size=VOCAB_SIZE)
    tokenizer.build_vocab(df["text"].tolist())
    tokenizer.save(str(MODEL_DIR / "aspect_vocab.json"))

    dataset = AspectDataset(df, tokenizer)
    val_size = max(1, int(len(dataset) * 0.15))
    train_ds, val_ds = random_split(dataset, [len(dataset) - val_size, val_size])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    model = AspectSentimentModel(vocab_size=VOCAB_SIZE).to(DEVICE)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.BCELoss()

    best_val_loss = float("inf")
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in val_loader:
                val_loss += criterion(model(x.to(DEVICE)), y.to(DEVICE)).item()
        val_loss /= max(len(val_loader), 1)
        scheduler.step()

        print(
            f"Epoch {epoch}/{epochs} | "
            f"train_loss={total_loss / max(len(train_loader), 1):.4f} | "
            f"val_loss={val_loss:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), MODEL_DIR / "aspect_model.pt")
            print(f"  Saved best model (val_loss={val_loss:.4f})")

    print("Training complete. Artifacts in", MODEL_DIR)


def generate_synthetic_csv(path: Path, n: int = 200) -> None:
    """Write a small aspect-labelled CSV for local training without a real dataset."""
    templates = [
        (
            "The price is too high but quality is excellent and shipping was fast.",
            [0.2, 0.9, 0.85, 0.7],
        ),
        (
            "Cheap product, terrible build quality, arrived late with poor service.",
            [0.8, 0.15, 0.2, 0.25],
        ),
        (
            "Fair price, decent quality, standard shipping, helpful customer service.",
            [0.6, 0.6, 0.55, 0.75],
        ),
        (
            "Expensive but worth it for the premium quality and express delivery.",
            [0.3, 0.95, 0.9, 0.8],
        ),
        (
            "Great deal on price, average quality, slow shipping, okay support.",
            [0.85, 0.5, 0.35, 0.5],
        ),
    ]
    rows = []
    for i in range(n):
        text, labels = templates[i % len(templates)]
        row = {"text": f"{text} Review #{i}."}
        for aspect, score in zip(ASPECTS, labels, strict=True):
            row[aspect] = score
        rows.append(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Wrote synthetic aspect dataset ({n} rows) to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train aspect sentiment biLSTM model")
    parser.add_argument("--data", help="Path to labelled aspect CSV")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--generate-synthetic",
        action="store_true",
        help="Write ml/data/sample_aspect_reviews.csv then train on it",
    )
    args = parser.parse_args()

    if args.generate_synthetic:
        data_file = Path(__file__).parent.parent / "data" / "sample_aspect_reviews.csv"
        generate_synthetic_csv(data_file)
        train(str(data_file), epochs=args.epochs, batch_size=args.batch_size)
    elif args.data:
        train(args.data, epochs=args.epochs, batch_size=args.batch_size)
    else:
        parser.error("Provide --data PATH or --generate-synthetic")
