"""PyTorch ``Dataset`` and word-level ``Tokenizer`` for aspect sentiment training.

Expects a labelled CSV with columns: ``text``, ``price``, ``quality``, ``shipping``, ``service``
(each aspect label is a float in [0, 1]). Used by ``ml.aspect.train``.
"""

import json
from collections import Counter

import torch
from torch.utils.data import DataLoader, Dataset

ASPECTS = ["price", "quality", "shipping", "service"]


class Tokenizer:
    """Simple word-level tokenizer — builds vocabulary from training corpus."""

    def __init__(self, vocab_size: int = 10000):
        self.vocab_size = vocab_size
        self.word2idx: dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.idx2word: dict[int, str] = {0: "<PAD>", 1: "<UNK>"}

    def build_vocab(self, texts: list[str]) -> None:
        """Populate ``word2idx`` from the most frequent words (up to ``vocab_size``)."""
        counts = Counter(word for text in texts for word in text.lower().split())
        for word, _ in counts.most_common(self.vocab_size - 2):
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word

    def encode(self, text: str, max_len: int = 200) -> list[int]:
        """Tokenise and pad/truncate to fixed length (``<UNK>`` = 1, ``<PAD>`` = 0)."""
        tokens = [self.word2idx.get(w, 1) for w in text.lower().split()[:max_len]]
        return tokens + [0] * (max_len - len(tokens))

    def save(self, path: str) -> None:
        """Persist vocabulary as JSON (``aspect_vocab.json``)."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.word2idx, f)

    @classmethod
    def load(cls, path: str) -> "Tokenizer":
        """Load vocabulary saved by ``save()``."""
        tokenizer = cls()
        with open(path, encoding="utf-8") as f:
            tokenizer.word2idx = json.load(f)
        tokenizer.idx2word = {int(v): k for k, v in tokenizer.word2idx.items()}
        return tokenizer


class AspectDataset(Dataset):
    """Multi-label aspect sentiment dataset backed by a pandas DataFrame."""

    def __init__(self, df, tokenizer: Tokenizer, max_len: int = 200):
        self.encodings = [tokenizer.encode(text, max_len) for text in df["text"]]
        self.labels = df[ASPECTS].values.astype(float)

    def __len__(self) -> int:
        return len(self.encodings)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return (
            torch.tensor(self.encodings[idx], dtype=torch.long),
            torch.tensor(self.labels[idx], dtype=torch.float32),
        )


def build_dataloader(
    dataset: Dataset,
    batch_size: int = 32,
    shuffle: bool = True,
) -> DataLoader:
    """Create a PyTorch ``DataLoader`` with sensible defaults for training."""
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
