"""Aspect sentiment inference (stub until the PyTorch model is trained)."""

ASPECTS = ["price", "quality", "shipping", "service"]


def predict_aspects(text: str) -> dict:
    """Return neutral placeholder scores for all four product aspects.

    Replaced by the trained biLSTM model in the future updates.
    """
    _ = text
    return {aspect: 0.5 for aspect in ASPECTS}
