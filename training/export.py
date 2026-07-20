"""
NeuroLumina — Model Export Script (TorchScript)
=================================================

Converts a trained HybridCNNBiLSTM PyTorch model to TorchScript format
for production inference (no Python dependency required at runtime).

Produces:
- ``model_scripted.pt`` — TorchScript-scripted model (preferred, dynamic shapes)
- ``model_traced.pt`` — TorchScript-traced model (fixed input size, faster)

Usage
-----
    # Export a trained model checkpoint
    python export.py --checkpoint checkpoints/best_model.pt --output models/

    # Export with specific input dimensions
    python export.py --checkpoint model.pt --n_channels 72 --n_timepoints 250 --n_classes 3

    # Test the exported model
    python export.py --checkpoint model.pt --test
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("export")

# ---------------------------------------------------------------------------
# Optional torch
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Local
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from model import HybridCNNBiLSTM, count_parameters  # noqa: E402


def export_to_torchscript(
    model: nn.Module,
    output_path: Path,
    n_channels: int = 72,
    n_timepoints: int = 300,
    method: str = "script",
) -> Tuple[Path, Optional[Path]]:
    """Export a PyTorch model to TorchScript.

    Parameters
    ----------
    model : nn.Module
        Trained model instance.
    output_path : Path
        Directory to save exported models.
    n_channels : int
        Number of input channels.
    n_timepoints : int
        Number of time samples per window.
    method : str
        "script" for scripting (dynamic shapes) or "trace" for tracing (fixed shape).

    Returns
    -------
    scripted_path : Path
    traced_path : Path or None
    """
    output_path.mkdir(parents=True, exist_ok=True)
    model.eval()

    paths = {}

    # Method 1: Scripting (preferred — handles dynamic input shapes)
    if method in ("script", "both"):
        logger.info("Exporting via TorchScript scripting...")
        try:
            scripted = torch.jit.script(model)
            scripted_path = output_path / "model_scripted.pt"
            scripted.save(str(scripted_path))
            logger.info(f"  Saved: {scripted_path}")
            paths["scripted"] = scripted_path
        except Exception as e:
            logger.warning(f"Scripting failed: {e}")
            paths["scripted"] = None

    # Method 2: Tracing (faster, but input shape must be fixed)
    if method in ("trace", "both"):
        logger.info("Exporting via TorchScript tracing...")
        try:
            dummy_input = torch.randn(1, n_channels, n_timepoints)
            traced = torch.jit.trace(model, dummy_input)
            traced_path = output_path / "model_traced.pt"
            traced.save(str(traced_path))
            logger.info(f"  Saved: {traced_path}")
            paths["traced"] = traced_path
        except Exception as e:
            logger.warning(f"Tracing failed: {e}")
            paths["traced"] = None

    return paths.get("scripted"), paths.get("traced")


def load_checkpoint(
    checkpoint_path: Path,
    n_channels: int,
    n_timepoints: int,
    n_classes: int,
    device: torch.device = torch.device("cpu"),
) -> nn.Module:
    """Load a trained model from a checkpoint.

    Parameters
    ----------
    checkpoint_path : Path
        Path to ``.pt`` checkpoint file.
    n_channels, n_timepoints, n_classes : int
        Model architecture dimensions.
    device : torch.device

    Returns
    -------
    model : nn.Module
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model = HybridCNNBiLSTM(
        n_channels=n_channels,
        n_timepoints=n_timepoints,
        n_classes=n_classes,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    logger.info(
        f"Loaded checkpoint from {checkpoint_path} "
        f"(epoch {checkpoint.get('epoch', '?')}, "
        f"val_acc={checkpoint.get('best_val_acc', '?'):.3f})"
    )
    return model


def test_exported_model(model_path: Path, n_channels: int = 72, n_timepoints: int = 300):
    """Load a TorchScript model and run a test inference.

    Parameters
    ----------
    model_path : Path
        Path to ``.pt`` TorchScript file.
    """
    logger.info(f"Testing TorchScript model: {model_path}")
    model = torch.jit.load(str(model_path))
    model.eval()

    # Test with batch size 1
    dummy = torch.randn(1, n_channels, n_timepoints)
    with torch.no_grad():
        output = model(dummy)

    logger.info(f"  Input shape:  {tuple(dummy.shape)}")
    logger.info(f"  Output shape: {tuple(output.shape)}")
    logger.info(f"  Output logits: {output[0].tolist()}")
    logger.info("  Test PASSED")

    # Test with batch size 8
    dummy_batch = torch.randn(8, n_channels, n_timepoints)
    with torch.no_grad():
        output_batch = model(dummy_batch)

    logger.info(f"  Batch (8) output shape: {tuple(output_batch.shape)}")
    logger.info("  Batch test PASSED")

    return output


def main(args):
    if not TORCH_AVAILABLE:
        logger.error("PyTorch is required for model export.")
        sys.exit(1)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    if args.checkpoint:
        # Load from checkpoint
        ckpt_path = Path(args.checkpoint)
        if not ckpt_path.exists():
            logger.error(f"Checkpoint not found: {ckpt_path}")
            sys.exit(1)

        model = load_checkpoint(
            ckpt_path,
            n_channels=args.n_channels,
            n_timepoints=args.n_timepoints,
            n_classes=args.n_classes,
            device=device,
        )
    else:
        # Create an untrained model (for testing the export pipeline)
        logger.warning("No checkpoint provided — creating untrained model for export test.")
        model = HybridCNNBiLSTM(
            n_channels=args.n_channels,
            n_timepoints=args.n_timepoints,
            n_classes=args.n_classes,
        )

    logger.info(f"Model: {type(model).__name__} | Params: {count_parameters(model):,}")

    # Export
    output_path = Path(args.output)
    scripted_path, traced_path = export_to_torchscript(
        model,
        output_path,
        n_channels=args.n_channels,
        n_timepoints=args.n_timepoints,
        method=args.method,
    )

    # Test
    if args.test and scripted_path:
        test_exported_model(scripted_path, args.n_channels, args.n_timepoints)
    if args.test and traced_path:
        test_exported_model(traced_path, args.n_channels, args.n_timepoints)

    # Save metadata
    metadata = {
        "model": "HybridCNNBiLSTM",
        "n_channels": args.n_channels,
        "n_timepoints": args.n_timepoints,
        "n_classes": args.n_classes,
        "params": count_parameters(model),
        "export_method": args.method,
        "exports": {
            "scripted": str(scripted_path) if scripted_path else None,
            "traced": str(traced_path) if traced_path else None,
        },
    }
    meta_path = output_path / "export_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {meta_path}")

    logger.info("Export complete.")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NeuroLumina — Export HybridCNNBiLSTM to TorchScript"
    )
    parser.add_argument(
        "--checkpoint", type=str, default=None,
        help="Path to trained model checkpoint (.pt)",
    )
    parser.add_argument(
        "--output", type=str, default="models",
        help="Output directory for exported models (default: models)",
    )
    parser.add_argument(
        "--n_channels", type=int, default=72,
        help="Number of input channels (default: 72)",
    )
    parser.add_argument(
        "--n_timepoints", type=int, default=300,
        help="Number of time samples (default: 300)",
    )
    parser.add_argument(
        "--n_classes", type=int, default=3,
        help="Number of output classes (default: 3)",
    )
    parser.add_argument(
        "--method", type=str, default="both",
        choices=["script", "trace", "both"],
        help="Export method: script, trace, or both (default: both)",
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run test inference on exported model",
    )
    parser.add_argument(
        "--device", type=str, default="cpu",
        help="Device to use (default: cpu)",
    )
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    main(args)