"""
NeuroLumina — Inference API Wrapper
=====================================

Production-ready inference wrapper for the HybridCNNBiLSTM model.
Handles input preprocessing, model loading, prediction, and output formatting.

Designed to be used by the Full-Stack Developer's API server.

Usage
-----
    >>> from inference import fNIRSInferenceEngine
    >>> engine = fNIRSInferenceEngine("models/model_scripted.pt")
    >>> result = engine.predict(hbo_array, hbr_array)
    >>> print(result["cognitive_load"])
    {"class": 2, "label": "high", "confidence": 0.89, "logits": [...]}

API Integration
---------------
    The inference engine is designed for HTTP API use:
    - Load once at server startup
    - Call predict() per request
    - Thread-safe (model.eval() + no_grad)
    - Returns JSON-serializable dicts
"""

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger("neurolumina.inference")

# ---------------------------------------------------------------------------
# Optional torch
# ---------------------------------------------------------------------------
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Dataset label maps (mirrors /home/team/shared/training/datamodule.py)
# ---------------------------------------------------------------------------
DATASET_LABEL_MAPS = {
    "fnirs2mw": {0: "0-back", 1: "2-back", 2: "3-back"},
    "mental_arithmetic": {0: "rest", 1: "task"},
    "mock": {0: "low", 1: "medium", 2: "high"},
}


# ===========================================================================
# Preprocessing
# ===========================================================================


class Preprocessor:
    """Preprocesses raw fNIRS data for model inference.

    Converts raw HbO/HbR arrays into the model's expected tensor format.
    Uses the same preprocessing pipeline as the DataModule.

    Parameters
    ----------
    expected_channels : int, default=72
        Number of expected input channels (36 HbO + 36 HbR).
    expected_timepoints : int, default=300
        Number of expected time samples (30 s at 10 Hz).
    fs : float, default=10.0
        Sampling rate in Hz.
    """

    def __init__(
        self,
        expected_channels: int = 72,
        expected_timepoints: int = 300,
        fs: float = 10.0,
    ):
        self.expected_channels = expected_channels
        self.expected_timepoints = expected_timepoints
        self.fs = fs

        # Normalisation stats (fitted on training data)
        self.channel_mean: np.ndarray | None = None
        self.channel_std: np.ndarray | None = None

    def fit(self, data: np.ndarray):
        """Fit normalisation statistics from training data.

        Parameters
        ----------
        data : np.ndarray
            Shape ``(n_samples, n_channels, n_timepoints)``.
        """
        self.channel_mean = data.mean(axis=(0, 2), keepdims=True)
        self.channel_std = data.std(axis=(0, 2), keepdims=True)
        self.channel_std[self.channel_std < 1e-8] = 1.0
        logger.info(
            f"Preprocessor fitted: mean={self.channel_mean.mean():.3f}, "
            f"std={self.channel_std.mean():.3f}"
        )

    def load_normalisation(self, path: str | Path):
        """Load pre-computed normalisation stats from a .npz file."""
        data = np.load(path)
        self.channel_mean = data["mean"]
        self.channel_std = data["std"]
        logger.info(f"Loaded normalisation stats from {path}")

    def save_normalisation(self, path: str | Path):
        """Save normalisation stats for later inference."""
        np.savez_compressed(
            path,
            mean=self.channel_mean,
            std=self.channel_std,
        )
        logger.info(f"Saved normalisation stats to {path}")

    def __call__(
        self,
        hbo: np.ndarray,
        hbr: np.ndarray,
        normalise: bool = True,
    ) -> np.ndarray:
        """Preprocess raw HbO and HbR arrays into model input tensor.

        Parameters
        ----------
        hbo : np.ndarray
            Shape ``(n_channels,)`` or ``(n_channels, n_timepoints)``.
            Oxyhaemoglobin concentration (μM) time series.
        hbr : np.ndarray
            Shape ``(n_channels,)`` or ``(n_channels, n_timepoints)``.
            Deoxyhaemoglobin concentration (μM) time series.
        normalise : bool, default=True
            Whether to apply z-score normalisation.

        Returns
        -------
        tensor : np.ndarray
            Shape ``(1, n_channels * 2, n_timepoints)``. Ready for model input.
            If single-channel input, broadcasts to ``(1, n_channels * 2, 1)``.
        """
        # Ensure 2D: (n_channels, n_timepoints) or (n_channels,)
        hbo = np.atleast_1d(hbo)
        hbr = np.atleast_1d(hbr)

        # If 1D (single timepoint per channel), reshape to (n_channels, 1)
        if hbo.ndim == 1:
            hbo = hbo[:, np.newaxis]
            hbr = hbr[:, np.newaxis]

        if hbo.shape[0] != hbr.shape[0]:
            raise ValueError(
                f"HbO ({hbo.shape[0]} ch) and HbR ({hbr.shape[0]} ch) "
                f"must have same number of channels"
            )
        if hbo.shape[1] != hbr.shape[1]:
            raise ValueError(
                f"HbO ({hbo.shape[1]} samples) and HbR ({hbr.shape[1]} samples) "
                f"must have same number of timepoints"
            )

        n_optodes = hbo.shape[0]
        n_timepoints = hbo.shape[1]

        # Interleave: [HbO_ch0, HbR_ch0, HbO_ch1, HbR_ch1, ...]
        # This matches the DataModule's "Option A: Interleaved" format
        interleaved = np.empty((n_optodes * 2, n_timepoints), dtype=np.float32)
        interleaved[0::2] = hbo
        interleaved[1::2] = hbr

        # Add batch dimension
        tensor = interleaved[np.newaxis, :, :]  # (1, 2*n_optodes, T)

        # Z-score normalisation
        if normalise and self.channel_mean is not None:
            tensor = (tensor - self.channel_mean) / self.channel_std

        return tensor


# ===========================================================================
# Inference Engine (only available when PyTorch is installed)
# ===========================================================================


if TORCH_AVAILABLE:

    class fNIRSInferenceEngine:
        """Production inference engine for HybridCNNBiLSTM.

        Loads a TorchScript model and provides ``predict()`` for
        real-time brain-state classification.

        Parameters
        ----------
        model_path : str or Path
            Path to TorchScript model (.pt file).
        device : str, default="cpu"
            Device for inference ("cpu" or "cuda").
        label_map : dict, optional
            Mapping from class index to label string.
            Defaults to fNIRS2MW labels if not provided.
        preprocessor : Preprocessor, optional
            Preprocessor instance. Created with defaults if not provided.
        """

        def __init__(
            self,
            model_path: str | Path,
            device: str = "cpu",
            label_map: dict[int, str] | None = None,
            preprocessor: Preprocessor | None = None,
        ):
            self.device = torch.device(
                device if device == "cpu" or torch.cuda.is_available() else "cpu"
            )
            self.label_map = label_map or DATASET_LABEL_MAPS["fnirs2mw"]
            self.preprocessor = preprocessor or Preprocessor()

            # Load model
            model_path = Path(model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")

            self.model = torch.jit.load(str(model_path), map_location=self.device)
            self.model.eval()
            logger.info(f"Loaded model from {model_path} on {self.device}")

        @torch.no_grad()
        def predict(
            self,
            hbo: np.ndarray,
            hbr: np.ndarray,
            normalise: bool = True,
            return_logits: bool = False,
        ) -> dict:
            import time

            t0 = time.time()
            tensor = self.preprocessor(hbo, hbr, normalise=normalise)
            tensor_torch = torch.from_numpy(tensor).to(self.device)
            preprocess_time = (time.time() - t0) * 1000

            t1 = time.time()
            logits = self.model(tensor_torch)
            inference_time = (time.time() - t1) * 1000

            logits_np = logits.cpu().numpy().flatten()
            predicted_class = int(np.argmax(logits_np))
            confidence = float(np.exp(logits_np[predicted_class]) / np.sum(np.exp(logits_np)))
            label = self.label_map.get(predicted_class, f"class_{predicted_class}")

            result = {
                "cognitive_load": {
                    "class": predicted_class,
                    "label": label,
                    "confidence": round(confidence, 4),
                },
                "timing_ms": {
                    "preprocess": round(preprocess_time, 1),
                    "inference": round(inference_time, 1),
                    "total": round(preprocess_time + inference_time, 1),
                },
            }
            if return_logits:
                result["cognitive_load"]["logits"] = [round(v, 4) for v in logits_np.tolist()]
            return result

        def predict_batch(
            self,
            hbo: np.ndarray,
            hbr: np.ndarray,
            normalise: bool = True,
            return_logits: bool = False,
        ) -> list[dict]:
            batch_size = hbo.shape[0]
            results = []
            for i in range(batch_size):
                result = self.predict(
                    hbo[i],
                    hbr[i],
                    normalise=normalise,
                    return_logits=return_logits,
                )
                result["sample_id"] = i
                results.append(result)
            return results

        def predict_from_epochs(
            self,
            epochs: np.ndarray,
            ch_names: list[str] | None = None,
        ) -> dict:
            n_epochs = epochs.shape[0]
            all_results = []
            for i in range(n_epochs):
                n_optodes = epochs.shape[1] // 2
                hbo = epochs[i, 0::2, :]
                hbr = epochs[i, 1::2, :]
                result = self.predict(hbo, hbr)
                result["epoch_id"] = i
                all_results.append(result)

            classes = [r["cognitive_load"]["class"] for r in all_results]
            confidences = [r["cognitive_load"]["confidence"] for r in all_results]
            label_counts = {}
            for c in classes:
                label = self.label_map.get(c, f"class_{c}")
                label_counts[label] = label_counts.get(label, 0) + 1

            return {
                "epochs": all_results,
                "aggregate": {
                    "n_epochs": n_epochs,
                    "predicted_labels": [self.label_map.get(c, f"class_{c}") for c in classes],
                    "most_common": max(label_counts, key=label_counts.get),
                    "mean_confidence": round(float(np.mean(confidences)), 4),
                },
            }

else:
    # Stub when torch is not available
    class fNIRSInferenceEngine:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PyTorch is required for fNIRSInferenceEngine. Install with: pip install torch"
            )


# ===========================================================================
# CLI
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== fNIRS Inference Engine Self-Test ===\n")

    # Test with mock data
    print("Generating mock inference data...")
    n_optodes = 36
    n_timepoints = 300
    rng = np.random.default_rng(42)

    # Simulate realistic HbO/HbR values
    hbo = rng.normal(2.0, 0.5, size=(n_optodes, n_timepoints)).astype(np.float32)
    hbr = rng.normal(1.0, 0.3, size=(n_optodes, n_timepoints)).astype(np.float32)

    # Add a simulated HRF-like increase for "high load"
    t = np.linspace(0, n_timepoints / 10, n_timepoints)
    hrf = 3.0 * np.exp(-((t - 5.0) ** 2) / (2 * 2.0**2))
    hbo += hrf[np.newaxis, :]  # boost HbO across all channels

    print(f"  HbO: {hbo.shape}, range [{hbo.min():.2f}, {hbo.max():.2f}]")
    print(f"  HbR: {hbr.shape}, range [{hbr.min():.2f}, {hbr.max():.2f}]")

    # Preprocess
    preprocessor = Preprocessor(
        expected_channels=n_optodes * 2,
        expected_timepoints=n_timepoints,
    )
    tensor = preprocessor(hbo, hbr, normalise=False)
    print(f"  Preprocessed tensor: {tensor.shape}")

    # Fit normalisation
    preprocessor.fit(tensor)
    tensor_norm = preprocessor(hbo, hbr, normalise=True)
    print(f"  Normalised tensor: mean={tensor_norm.mean():.3f}, std={tensor_norm.std():.3f}")

    print("\n  Preprocessor API tested OK")
    print(f"  Expected input: (1, {n_optodes * 2}, {n_timepoints})")
    print("  Expected output: (1, n_classes) logits")

    print("\n=== Self-test complete ===")
    print("\nNote: To test full inference pipeline, export a model first:")
    print("  python export.py --checkpoint checkpoints/best_model.pt --test")
    print('  python -c "from inference import fNIRSInferenceEngine; ..."')
