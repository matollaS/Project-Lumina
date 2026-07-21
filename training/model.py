"""
NeuroLumina — Hybrid CNN-BiLSTM Models for fNIRS Brain-State Classification
=============================================================================

Implements the model architectures described in the ML architecture plan:
1. **HybridCNNBiLSTM** (primary) — Conv1D + BiLSTM for general fNIRS classification
2. **SpatiotemporalCNN** (variant A) — Conv3D over optode montage + BiLSTM
3. **MultiTaskModel** (extension) — Shared backbone + multiple task heads

All models expect input tensors of shape ``(batch, n_channels, n_timepoints)``
or ``(batch, 2, H, W, T)`` for the spatiotemporal variant.

Usage
-----
    >>> from model import HybridCNNBiLSTM
    >>> model = HybridCNNBiLSTM(n_channels=72, n_timepoints=300, n_classes=3)
    >>> import torch
    >>> x = torch.randn(16, 72, 300)
    >>> logits = model(x)  # (16, 3)
"""

import logging

logger = logging.getLogger("neurolumina.training.model")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

    # Stub nn for docstring/testing
    class nn:
        class Module:
            pass

    class F:
        pass

    logger.warning("PyTorch not installed. Model classes cannot be instantiated.")


# ===========================================================================
# Utility
# ===========================================================================


def count_parameters(model) -> int:
    """Count trainable parameters in a model."""
    if not TORCH_AVAILABLE:
        return 0
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def _require_torch():
    if not TORCH_AVAILABLE:
        raise ImportError(
            "PyTorch is required for model instantiation. Install with: pip install torch"
        )


# ===========================================================================
# Primary: HybridCNNBiLSTM
# ===========================================================================


class HybridCNNBiLSTM(nn.Module):
    """Hybrid CNN-BiLSTM for fNIRS brain-state classification.

    Architecture:
        Conv1D (64, k=5) → BatchNorm → ReLU → MaxPool(2)
        → Conv1D (128, k=3) → BatchNorm → ReLU → MaxPool(2)
        → BiLSTM (128 units) → BiLSTM (64 units)
        → Dense (64) → Dropout(0.4) → Softmax

    Parameters
    ----------
    n_channels : int
        Number of input channels (e.g. 72 for 36 HbO + 36 HbR).
    n_timepoints : int
        Number of time samples per epoch.
    n_classes : int
        Number of output classes.
    dropout : float, default=0.4
        Dropout rate for the classification head.
    """

    def __init__(
        self,
        n_channels: int = 72,
        n_timepoints: int = 300,
        n_classes: int = 3,
        dropout: float = 0.4,
    ):
        _require_torch()
        super().__init__()

        self.n_channels = n_channels
        self.n_timepoints = n_timepoints
        self.n_classes = n_classes

        # --- CNN feature extractor ---
        self.cnn = nn.Sequential(
            # Block 1
            nn.Conv1d(n_channels, 64, kernel_size=5, padding="same"),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            # Block 2
            nn.Conv1d(64, 128, kernel_size=3, padding="same"),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )

        # Compute LSTM input size after CNN + pooling
        # MaxPool1d(2) x2 → temporal dim divided by 4
        self._lstm_input_size = 128
        self._seq_len = n_timepoints // 4

        # --- BiLSTM sequence model ---
        self.lstm = nn.LSTM(
            input_size=self._lstm_input_size,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.2,
        )

        # --- Classifier ---
        self.classifier = nn.Sequential(
            nn.Linear(128 * 2, 64),  # *2 for bidirectional
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, n_classes),
        )

        self._init_weights()

    def _init_weights(self):
        """Initialize weights using He/Kaiming initialization."""
        for m in self.modules():
            if isinstance(m, (nn.Conv1d, nn.Linear)):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        """Forward pass.

        Parameters
        ----------
        x : torch.Tensor
            Shape ``(batch, n_channels, n_timepoints)``.

        Returns
        -------
        logits : torch.Tensor
            Shape ``(batch, n_classes)``.
        """
        # CNN feature extraction
        x = self.cnn(x)  # (batch, 128, T/4)

        # Permute for LSTM: (batch, features, time) → (batch, time, features)
        x = x.permute(0, 2, 1)

        # BiLSTM
        x, _ = self.lstm(x)  # (batch, T/4, 256)

        # Take last time step
        x = x[:, -1, :]  # (batch, 256)

        # Classifier
        x = self.classifier(x)  # (batch, n_classes)
        return x


# ===========================================================================
# Variant A: SpatiotemporalCNN (3D convolutions over optode montage)
# ===========================================================================


class SpatiotemporalCNN(nn.Module):
    """Spatiotemporal CNN with Conv3D over optode montage + BiLSTM.

    Expects input with known optode positions arranged on a 2D grid.

    Parameters
    ----------
    grid_h : int
        Height of optode spatial grid (e.g. 8).
    grid_w : int
        Width of optode spatial grid (e.g. 8).
    n_timepoints : int
        Number of time samples.
    n_classes : int
        Number of output classes.
    n_chromophores : int, default=2
        Number of chromophore types (HbO + HbR).
    """

    def __init__(
        self,
        grid_h: int = 8,
        grid_w: int = 8,
        n_timepoints: int = 300,
        n_classes: int = 3,
        n_chromophores: int = 2,
    ):
        _require_torch()
        super().__init__()

        self.grid_h = grid_h
        self.grid_w = grid_w
        self.n_timepoints = n_timepoints
        self.n_classes = n_classes
        self.n_chromophores = n_chromophores

        # Conv3D: (batch, C, D, H, W) where C=n_chromophores, D=time
        self.conv3d = nn.Sequential(
            nn.Conv3d(n_chromophores, 32, kernel_size=(5, 3, 3), padding="same"),
            nn.BatchNorm3d(32),
            nn.ReLU(),
            nn.MaxPool3d((2, 1, 1)),
            nn.Conv3d(32, 64, kernel_size=(3, 3, 3), padding="same"),
            nn.BatchNorm3d(64),
            nn.ReLU(),
            nn.MaxPool3d((2, 1, 1)),
        )

        # LSTM input size after Conv3D
        # time dim: n_timepoints // 4
        self._lstm_input_size = 64 * grid_h * grid_w

        self.lstm = nn.LSTM(
            input_size=self._lstm_input_size,
            hidden_size=128,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0.0,
        )

        self.classifier = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        """Forward pass.

        Parameters
        ----------
        x : torch.Tensor
            Shape ``(batch, n_chromophores, n_timepoints, grid_h, grid_w)``.

        Returns
        -------
        logits : torch.Tensor (batch, n_classes)
        """
        # Conv3D: (B, C, T, H, W) → (B, 64, T/4, H, W)
        x = self.conv3d(x)

        # Reshape for LSTM: (B, T/4, features)
        B, C, T, H, W = x.shape
        x = x.permute(0, 2, 1, 3, 4).reshape(B, T, C * H * W)

        # BiLSTM
        x, _ = self.lstm(x)
        x = x[:, -1, :]

        return self.classifier(x)


# ===========================================================================
# Variant B: Multi-Task Model
# ===========================================================================


class MultiTaskHead(nn.Module):
    """Single task head for multi-task learning."""

    def __init__(self, input_dim: int, output_dim: int, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class MultiTaskModel(nn.Module):
    """Multi-task model with shared CNN-BiLSTM backbone.

    Supports simultaneous classification (categorical) and
    regression (continuous fatigue/recovery scoring).

    Parameters
    ----------
    n_channels : int
    n_timepoints : int
    task_config : dict
        Dictionary mapping task names to (output_dim, task_type).
        E.g.:
            {
                "cognitive_load": (3, "classification"),
                "fatigue": (1, "regression"),
                "attention": (1, "regression"),
            }
    """

    def __init__(
        self,
        n_channels: int = 72,
        n_timepoints: int = 300,
        task_config: dict[str, tuple[int, str]] | None = None,
    ):
        _require_torch()
        super().__init__()

        if task_config is None:
            task_config = {
                "cognitive_load": (3, "classification"),
            }

        self.task_config = task_config

        # Shared backbone (same as HybridCNNBiLSTM)
        self.backbone_cnn = nn.Sequential(
            nn.Conv1d(n_channels, 64, kernel_size=5, padding="same"),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, padding="same"),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )

        self.backbone_lstm = nn.LSTM(
            input_size=128,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.2,
        )

        # Task-specific heads
        self.task_heads = nn.ModuleDict()
        for task_name, (out_dim, task_type) in task_config.items():
            self.task_heads[task_name] = MultiTaskHead(256, out_dim)

    def forward(self, x):
        """Forward pass.

        Returns
        -------
        dict mapping task_name → output tensor
        """
        x = self.backbone_cnn(x)
        x = x.permute(0, 2, 1)
        x, _ = self.backbone_lstm(x)
        x = x[:, -1, :]

        return {name: head(x) for name, head in self.task_heads.items()}


# ===========================================================================
# Model factory
# ===========================================================================

MODEL_REGISTRY = {
    "hybrid_cnn_bilstm": HybridCNNBiLSTM,
    "spatiotemporal_cnn": SpatiotemporalCNN,
    "multi_task": MultiTaskModel,
}


def create_model(
    model_name: str = "hybrid_cnn_bilstm",
    n_channels: int = 72,
    n_timepoints: int = 300,
    n_classes: int = 3,
    **kwargs,
) -> nn.Module:
    """Create a model by name.

    Parameters
    ----------
    model_name : str
        One of "hybrid_cnn_bilstm", "spatiotemporal_cnn", "multi_task".
    n_channels : int
    n_timepoints : int
    n_classes : int
    **kwargs
        Additional arguments passed to the model constructor.

    Returns
    -------
    model : nn.Module
    """
    _require_torch()

    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{model_name}'. Available: {list(MODEL_REGISTRY.keys())}")

    model_cls = MODEL_REGISTRY[model_name]

    if model_name == "hybrid_cnn_bilstm":
        return model_cls(
            n_channels=n_channels,
            n_timepoints=n_timepoints,
            n_classes=n_classes,
            **kwargs,
        )
    elif model_name == "spatiotemporal_cnn":
        return model_cls(
            n_timepoints=n_timepoints,
            n_classes=n_classes,
            **kwargs,
        )
    elif model_name == "multi_task":
        return model_cls(
            n_channels=n_channels,
            n_timepoints=n_timepoints,
            task_config=kwargs.get(
                "task_config",
                {
                    "cognitive_load": (n_classes, "classification"),
                },
            ),
        )


# ===========================================================================
# Self-test
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if not TORCH_AVAILABLE:
        print("PyTorch not available. Install with: pip install torch")
        exit(0)

    print("=== Model Architecture Verification ===\n")

    # Test 1: HybridCNNBiLSTM
    print("--- HybridCNNBiLSTM ---")
    model = HybridCNNBiLSTM(n_channels=72, n_timepoints=300, n_classes=3)
    x = torch.randn(8, 72, 300)
    y = model(x)
    print(f"  Input:  {tuple(x.shape)}")
    print(f"  Output: {tuple(y.shape)}")
    print(f"  Params: {count_parameters(model):,}")
    assert y.shape == (8, 3)
    print("  PASS")

    # Test 2: SpatiotemporalCNN
    print("\n--- SpatiotemporalCNN ---")
    model2 = SpatiotemporalCNN(grid_h=8, grid_w=8, n_timepoints=300, n_classes=3)
    x2 = torch.randn(8, 2, 300, 8, 8)
    y2 = model2(x2)
    print(f"  Input:  {tuple(x2.shape)}")
    print(f"  Output: {tuple(y2.shape)}")
    print(f"  Params: {count_parameters(model2):,}")
    assert y2.shape == (8, 3)
    print("  PASS")

    # Test 3: MultiTaskModel
    print("\n--- MultiTaskModel ---")
    task_config = {
        "cognitive_load": (3, "classification"),
        "fatigue": (1, "regression"),
        "attention": (1, "regression"),
    }
    model3 = MultiTaskModel(n_channels=72, n_timepoints=300, task_config=task_config)
    x3 = torch.randn(8, 72, 300)
    y3 = model3(x3)
    print(f"  Input:  {tuple(x3.shape)}")
    for name, out in y3.items():
        print(f"  {name}: {tuple(out.shape)}")
    print(f"  Params: {count_parameters(model3):,}")
    assert y3["cognitive_load"].shape == (8, 3)
    assert y3["fatigue"].shape == (8, 1)
    assert y3["attention"].shape == (8, 1)
    print("  PASS")

    # Test 4: Model factory
    print("\n--- Model Factory ---")
    for name in MODEL_REGISTRY:
        m = create_model(name, n_channels=72, n_timepoints=300, n_classes=3)
        print(f"  {name}: {count_parameters(m):,} params")

    print("\n=== All tests passed! ===")
