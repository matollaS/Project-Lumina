"""
NeuroLumina — Baseline Training Script
========================================

Trains the HybridCNNBiLSTM model on synthetic fNIRS data for
brain-state classification.

Usage
-----
    # Train on mock data (no SNIRF files needed)
    python train.py

    # Train with real data
    python train.py --dataset fnirs2mw --snirf_paths data/sub-*.snirf

    # Override defaults
    python train.py --epochs 50 --batch_size 32 --lr 1e-3

    # Resume from checkpoint
    python train.py --resume checkpoints/epoch=20.pt
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train")

# ---------------------------------------------------------------------------
# Optional torch import
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.tensorboard import SummaryWriter
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from datamodule import fNIRSDataModule  # noqa: E402
from model import HybridCNNBiLSTM, count_parameters  # noqa: E402


# ===========================================================================
# Training helpers
# ===========================================================================


def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    """Compute classification accuracy."""
    preds = logits.argmax(dim=1)
    return (preds == targets).float().mean().item()


class AverageMeter:
    """Tracks running average of metrics."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val: float, n: int = 1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
) -> Dict[str, float]:
    """Train for one epoch.

    Returns
    -------
    dict with keys: loss, accuracy
    """
    model.train()
    losses = AverageMeter()
    accs = AverageMeter()

    t0 = time.time()
    for batch_idx, (x, y) in enumerate(loader):
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()

        acc = accuracy(logits, y)
        losses.update(loss.item(), x.size(0))
        accs.update(acc, x.size(0))

        if batch_idx % 10 == 0:
            logger.info(
                f"  Epoch {epoch:3d} | Batch {batch_idx:3d}/{len(loader)} | "
                f"Loss: {losses.val:.4f} | Acc: {accs.val:.3f}"
            )

    logger.info(
        f"  >>> Epoch {epoch:3d} done | "
        f"Loss: {losses.avg:.4f} | Acc: {accs.avg:.3f} | "
        f"Time: {time.time() - t0:.1f}s"
    )
    return {"loss": losses.avg, "accuracy": accs.avg}


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
    split: str = "val",
) -> Dict[str, float]:
    """Evaluate model on validation set.

    Returns
    -------
    dict with keys: loss, accuracy
    """
    model.eval()
    losses = AverageMeter()
    accs = AverageMeter()

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        loss = criterion(logits, y)
        acc = accuracy(logits, y)

        losses.update(loss.item(), x.size(0))
        accs.update(acc, x.size(0))

    logger.info(
        f"  [{split}] Loss: {losses.avg:.4f} | Acc: {accs.avg:.3f}"
    )
    return {"loss": losses.avg, "accuracy": accs.avg}


# ===========================================================================
# Main training loop
# ===========================================================================


def main(args):
    if not TORCH_AVAILABLE:
        logger.error("PyTorch is required for training.")
        sys.exit(1)

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    if device.type == "cuda":
        logger.info(f"  GPU: {torch.cuda.get_device_name(0)}")

    # Data
    logger.info(f"Loading dataset: {args.dataset}")
    dm = fNIRSDataModule(
        snirf_paths=args.snirf_paths,
        dataset=args.dataset,
        config={
            "batch_size": args.batch_size,
            "val_strategy": args.val_strategy,
            "n_folds": args.n_folds,
            "num_workers": args.num_workers,
        },
    )
    dm.prepare_data()
    dm.setup()

    logger.info(
        f"  Train: {len(dm._train_dataset)} samples, "
        f"Val: {len(dm._val_dataset)} samples"
    )
    logger.info(
        f"  Shape: {dm.data_shape}, Classes: {dm.n_classes}"
    )

    train_loader = dm.train_dataloader()
    val_loader = dm.val_dataloader()

    # Model
    n_channels = dm.n_channels
    n_timepoints = dm.n_timepoints
    n_classes = dm.n_classes

    model = HybridCNNBiLSTM(
        n_channels=n_channels,
        n_timepoints=n_timepoints,
        n_classes=n_classes,
        dropout=args.dropout,
    ).to(device)

    logger.info(
        f"Model: HybridCNNBiLSTM | "
        f"Params: {count_parameters(model):,} | "
        f"Input: ({n_channels}, {n_timepoints}) → {n_classes} classes"
    )

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=5,
        min_lr=1e-6,
        verbose=True,
    )

    # Checkpoint directory
    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # Training
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting training for {args.epochs} epochs")
    logger.info(f"  Batch size: {args.batch_size}")
    logger.info(f"  Learning rate: {args.lr}")
    logger.info(f"  Weight decay: {args.weight_decay}")
    logger.info(f"  Dropout: {args.dropout}")
    logger.info(f"{'='*60}\n")

    best_val_loss = float("inf")
    best_val_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    start_epoch = 1
    if args.resume:
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
        best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        best_val_acc = checkpoint.get("best_val_acc", 0.0)
        logger.info(f"Resumed from checkpoint: {args.resume} (epoch {start_epoch-1})")

    for epoch in range(start_epoch, args.epochs + 1):
        # Train
        train_metrics = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch
        )

        # Validate
        val_metrics = evaluate(model, val_loader, criterion, device, "val")

        # Update LR scheduler
        scheduler.step(val_metrics["loss"])

        # Save history
        history["train_loss"].append(train_metrics["loss"])
        history["train_acc"].append(train_metrics["accuracy"])
        history["val_loss"].append(val_metrics["loss"])
        history["val_acc"].append(val_metrics["accuracy"])

        # Save best model
        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            best_val_loss = val_metrics["loss"]
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_loss": best_val_loss,
                "best_val_acc": best_val_acc,
                "args": vars(args),
            }
            ckpt_path = ckpt_dir / "best_model.pt"
            torch.save(checkpoint, ckpt_path)
            logger.info(f"  *** New best model saved: acc={best_val_acc:.3f}")

        # Periodic checkpoint
        if epoch % 10 == 0:
            ckpt_path = ckpt_dir / f"epoch_{epoch}.pt"
            torch.save(checkpoint, ckpt_path)

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("Training complete!")
    logger.info(f"  Best val accuracy: {best_val_acc:.3f}")
    logger.info(f"  Best val loss:     {best_val_loss:.4f}")
    logger.info(f"  Final train acc:   {history['train_acc'][-1]:.3f}")
    logger.info(f"  Final val acc:     {history['val_acc'][-1]:.3f}")
    logger.info(f"  Model saved to:    {ckpt_dir / 'best_model.pt'}")
    logger.info(f"{'='*60}\n")

    # Save history
    history_path = ckpt_dir / "history.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    logger.info(f"Training history saved to: {history_path}")

    # Save args
    args_path = ckpt_dir / "args.json"
    with open(args_path, "w") as f:
        json.dump(vars(args), f, indent=2)
    logger.info(f"Training args saved to: {args_path}")


# ===========================================================================
# CLI
# ===========================================================================

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NeuroLumina — Train HybridCNNBiLSTM on fNIRS data"
    )

    # Data
    parser.add_argument(
        "--dataset",
        type=str,
        default="mock",
        choices=["mock", "fnirs2mw", "mental_arithmetic"],
        help="Dataset to use (default: mock)",
    )
    parser.add_argument(
        "--snirf_paths",
        type=str,
        nargs="*",
        default=None,
        help="Paths to .snirf files (optional, uses mock if empty)",
    )
    parser.add_argument(
        "--val_strategy",
        type=str,
        default="holdout",
        choices=["holdout", "loso", "kfold"],
        help="Validation strategy (default: holdout)",
    )
    parser.add_argument(
        "--n_folds",
        type=int,
        default=5,
        help="Number of folds for k-fold CV (default: 5)",
    )

    # Training
    parser.add_argument(
        "--epochs", type=int, default=30, help="Number of epochs (default: 30)"
    )
    parser.add_argument(
        "--batch_size", type=int, default=32, help="Batch size (default: 32)"
    )
    parser.add_argument(
        "--lr", type=float, default=1e-3, help="Learning rate (default: 1e-3)"
    )
    parser.add_argument(
        "--weight_decay",
        type=float,
        default=1e-4,
        help="Weight decay (default: 1e-4)",
    )
    parser.add_argument(
        "--dropout", type=float, default=0.4, help="Dropout rate (default: 0.4)"
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=0,
        help="DataLoader workers (default: 0)",
    )

    # Checkpoints
    parser.add_argument(
        "--checkpoint_dir",
        type=str,
        default="checkpoints",
        help="Checkpoint directory (default: checkpoints)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Resume from checkpoint path",
    )

    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    main(args)
