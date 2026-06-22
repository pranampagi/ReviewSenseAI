"""PyTorch biLSTM + attention architecture for multi-label aspect sentiment.

Output: four sigmoid scores in [0, 1] for price, quality, shipping, and service.
Trained via ``ml.aspect.train`` and loaded at inference.
"""

import torch
import torch.nn as nn


class Attention(nn.Module):
    """Single-head attention over LSTM time steps."""

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Linear(hidden_dim, 1)

    def forward(self, lstm_out: torch.Tensor) -> torch.Tensor:
        """lstm_out: (batch, seq, hidden) → context: (batch, hidden)."""
        scores = self.attn(lstm_out).squeeze(-1)
        weights = torch.softmax(scores, dim=1).unsqueeze(-1)
        return (lstm_out * weights).sum(dim=1)


class AspectSentimentModel(nn.Module):
    """Embedding → biLSTM → attention → linear → sigmoid (4 aspect scores)."""

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 128,
        hidden: int = 256,
        num_aspects: int = 4,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.dropout = nn.Dropout(0.3)
        self.lstm = nn.LSTM(
            embed_dim,
            hidden,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3,
        )
        self.attention = Attention(hidden * 2)
        self.classifier = nn.Linear(hidden * 2, num_aspects)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, seq) token ids → (batch, 4) aspect scores."""
        emb = self.dropout(self.embedding(x))
        lstm_out, _ = self.lstm(emb)
        context = self.attention(lstm_out)
        return self.sigmoid(self.classifier(context))
