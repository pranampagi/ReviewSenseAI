"""Load trained biLSTM checkpoint and run per-aspect sentiment inference."""

from pathlib import Path

import torch

from ml.aspect.dataset import ASPECTS, Tokenizer
from ml.aspect.model import AspectSentimentModel

MODEL_DIR = Path(__file__).parent.parent / "models"
DEVICE = "cpu"
VOCAB_SIZE = 10000  # Must match ``ml.aspect.train`` embedding table size

_model: AspectSentimentModel | None = None
_tokenizer: Tokenizer | None = None


def _load() -> None:
    """Lazy-load vocabulary and model weights (``aspect_vocab.json``, ``aspect_model.pt``)."""
    global _model, _tokenizer
    if _model is None:
        _tokenizer = Tokenizer.load(str(MODEL_DIR / "aspect_vocab.json"))
        _model = AspectSentimentModel(vocab_size=VOCAB_SIZE)
        state = torch.load(MODEL_DIR / "aspect_model.pt", map_location=DEVICE, weights_only=True)
        _model.load_state_dict(state)
        _model.eval()


def predict_aspects(text: str) -> dict:
    """Return per-aspect scores in [0, 1] for price, quality, shipping, and service."""
    _load()
    assert _tokenizer is not None and _model is not None
    tokens = torch.tensor([_tokenizer.encode(text)], dtype=torch.long)
    with torch.no_grad():
        scores = _model(tokens)[0].tolist()
    return {aspect: round(float(score), 4) for aspect, score in zip(ASPECTS, scores, strict=True)}
