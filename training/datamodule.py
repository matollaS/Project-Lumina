"""
NeuroLumina — fNIRS DataModule for Training
=============================================

PyTorch Lightning-style DataModule for fNIRS brain-state classification,
with explicit support for the fNIRS2MW and Mental Arithmetic benchmark datasets.

Integrates with nlcore (neurolumina-core) for SNIRF loading and preprocessing.

Usage
-----
    >>> from datamodule import fNIRSDataModule
    >>> 
    >>> # With real SNIRF files
    >>> dm = fNIRSDataModule(
    ...     snirf_paths=["sub-001.snirf", "sub-002.snirf"],
    ...     dataset="fnirs2mw",  # or "mental_arithmetic"
    ...     config={"val_strategy": "loso", "batch_size": 32}
    ... )
    >>> dm.prepare_data()
    >>> dm.setup()
    >>> train_loader = dm.train_dataloader()
    >>> 
    >>> # Or with mock data for development
    >>> dm = fNIRSDataModule(dataset="mock", config={"batch_size": 16})
    >>> dm.prepare_data()
"""

import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("neurolumina.training.datamodule")

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    import torch
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    Dataset = object
    DataLoader = None

try:
    from sklearn.model_selection import KFold
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ---------------------------------------------------------------------------
# Dataset configurations
# ---------------------------------------------------------------------------

DATASET_CONFIGS = {
    "fnirs2mw": {
        "description": "fNIRS2MW — Multi-Workload fNIRS Dataset (n-back)",
        "n_subjects": 29,
        "n_optodes": 36,  # 36 optode channels, each has HbO + HbR
        "n_timepoints": 250,  # ~25 seconds at 10 Hz
        "n_classes": 3,  # 0-back, 2-back, 3-back
        "fs": 10.0,
        "tmin": -2.0,
        "tmax": 25.0,
        "baseline": (-2.0, 0.0),
        "bandpass": (0.01, 0.2),
        "label_map": {"0-back": 0, "2-back": 1, "3-back": 2},
        "epochs_per_subject": 90,  # ~90 trials per subject
        "ch_names_prefix": "S",
        "reference": "Bulgheroni et al. (2022) — Scientific Data",
    },
    "mental_arithmetic": {
        "description": "Mental Arithmetic — Binary task vs. rest",
        "n_subjects": 24,
        "n_optodes": 22,  # 22 optode channels, each has HbO + HbR
        "n_timepoints": 300,  # ~30 seconds at 10 Hz
        "n_classes": 2,  # task, rest
        "fs": 10.0,
        "tmin": -2.0,
        "tmax": 30.0,
        "baseline": (-2.0, 0.0),
        "bandpass": (0.01, 0.2),
        "label_map": {"rest": 0, "task": 1},
        "epochs_per_subject": 50,
        "ch_names_prefix": "Ch",
        "reference": "Shin et al. (2018)",
    },
    "mock": {
        "description": "Synthetic data for development/testing",
        "n_subjects": 10,
        "n_optodes": 36,  # 36 simulated optodes, doubled for HbO+HbR
        "n_timepoints": 300,
        "n_classes": 3,
        "fs": 10.0,
        "tmin": -2.0,
        "tmax": 30.0,
        "baseline": (-2.0, 0.0),
        "bandpass": (0.01, 0.2),
        "label_map": {"low": 0, "medium": 1, "high": 2},
        "epochs_per_subject": 50,
        "ch_names_prefix": "mock",
        "reference": "Synthetic — NeuroLumina",
    },
}


def get_dataset_config(dataset_name: str) -> dict:
    """Get configuration for a named dataset.

    Parameters
    ----------
    dataset_name : str
        One of "fnirs2mw", "mental_arithmetic", or "mock".

    Returns
    -------
    config : dict
    """
    name = dataset_name.lower().replace("-", "_").replace(" ", "_")
    if name not in DATASET_CONFIGS:
        available = list(DATASET_CONFIGS.keys())
        raise ValueError(
            f"Unknown dataset '{dataset_name}'. Available: {available}"
        )
    return dict(DATASET_CONFIGS[name])


# ---------------------------------------------------------------------------
# Dataset class
# ---------------------------------------------------------------------------


class fNIRSDataset(Dataset):
    """PyTorch Dataset wrapping preprocessed fNIRS epochs.

    Parameters
    ----------
    data : np.ndarray
        Shape ``(n_epochs, n_channels, n_timepoints)``, dtype float32.
    labels : np.ndarray
        Shape ``(n_epochs,)``, dtype int64.
    metadata : dict, optional
    transform : callable, optional
    """

    def __init__(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        metadata: Optional[dict] = None,
        transform: Optional[callable] = None,
    ):
        self._data_np = data.astype(np.float32)
        self._labels_np = labels.astype(np.int64)
        self.metadata = metadata or {}
        self.transform = transform

        if TORCH_AVAILABLE:
            self.data = torch.from_numpy(self._data_np).float()
            self.labels = torch.from_numpy(self._labels_np).long()
        else:
            self.data = self._data_np
            self.labels = self._labels_np

    def __len__(self) -> int:
        return len(self._data_np)

    def __getitem__(self, idx):
        if TORCH_AVAILABLE:
            x = self.data[idx]
            y = self.labels[idx]
        else:
            x = self._data_np[idx]
            y = self._labels_np[idx]
        if self.transform:
            x = self.transform(x)
        return x, y

    @property
    def n_channels(self) -> int:
        return self.data.shape[1]

    @property
    def n_timepoints(self) -> int:
        return self.data.shape[2]

    @property
    def n_classes(self) -> int:
        return int(np.max(self._labels_np) + 1)


# ---------------------------------------------------------------------------
# Mock data generator (dataset-aware)
# ---------------------------------------------------------------------------


class MockfNIRSGenerator:
    """Generates synthetic fNIRS-like data for development.

    Produces realistic haemodynamic response shapes with pink noise,
    per-subject baseline drift, and class-conditional amplitude scaling.

    Parameters
    ----------
    dataset_config : dict
        Dataset configuration from ``get_dataset_config()``.
    seed : int, default=42
    """

    def __init__(self, dataset_config: dict, seed: int = 42):
        self.cfg = dataset_config
        self.rng = np.random.default_rng(seed)

    def generate(self) -> Dict[str, Any]:
        """Generate synthetic dataset.

        Returns
        -------
        dict with keys: data, labels, subject_ids, metadata
        """
        n_subjects = self.cfg.get("n_subjects", 10)
        n_epochs = self.cfg.get("epochs_per_subject", 50)
        n_optodes = self.cfg.get("n_optodes", 36)
        n_channels = n_optodes * 2  # HbO + HbR per optode
        n_timepoints = self.cfg.get("n_timepoints", 300)
        n_classes = self.cfg.get("n_classes", 3)

        data_list, label_list, subject_list = [], [], []

        for subj in range(n_subjects):
            baseline = self.rng.normal(0, 0.5, size=(1, n_channels, 1))
            for _ in range(n_epochs):
                label = self.rng.integers(0, n_classes)
                t = np.linspace(0, n_timepoints / 10, n_timepoints)
                hrf_peak = 5.0
                hrf = np.exp(-((t - hrf_peak) ** 2) / (2 * 2.0 ** 2))
                hrf = hrf / hrf.max() * (label + 1) * 2.0
                hrf_2d = hrf[np.newaxis, :] * self.rng.uniform(
                    0.5, 1.5, size=(n_channels, 1)
                )
                pink = self._pink_noise(n_timepoints, n_channels)
                white = self.rng.normal(0, 0.1, size=(n_channels, n_timepoints))
                noise = 0.3 * (pink + white)
                data_list.append(baseline + hrf_2d + noise)
                label_list.append(label)
                subject_list.append(subj)

        data = np.concatenate(data_list, axis=0).astype(np.float32)
        labels = np.array(label_list, dtype=np.int64)
        subject_ids = np.array(subject_list, dtype=np.int64)

        return {
            "data": data,
            "labels": labels,
            "subject_ids": subject_ids,
            "metadata": {
                "n_channels": n_channels,
                "n_timepoints": n_timepoints,
                "n_classes": n_classes,
                "fs": self.cfg["fs"],
                "ch_names": [
                    f"{self.cfg['ch_names_prefix']}_{i}_hbo"
                    for i in range(n_optodes)
                ] + [
                    f"{self.cfg['ch_names_prefix']}_{i}_hbr"
                    for i in range(n_optodes)
                ],
                "dataset": self.cfg["description"],
            },
        }

    @staticmethod
    def _pink_noise(n_timepoints: int, n_channels: int) -> np.ndarray:
        white = np.random.normal(0, 1, size=(n_channels, n_timepoints))
        fft_white = np.fft.rfft(white, axis=1)
        freqs = np.fft.rfftfreq(n_timepoints)[np.newaxis, :]
        freqs[0, 0] = 1e-6
        fft_pink = fft_white / np.sqrt(freqs)
        pink = np.fft.irfft(fft_pink, n=n_timepoints, axis=1)
        return pink / np.std(pink)


# ---------------------------------------------------------------------------
# Main DataModule
# ---------------------------------------------------------------------------


class fNIRSDataModule:
    """PyTorch Lightning-style DataModule for fNIRS brain-state data.

    Parameters
    ----------
    snirf_paths : list of str or Path, optional
        Paths to .snirf files. If None, generates mock data.
    dataset : str, default="mock"
        Dataset name: "fnirs2mw", "mental_arithmetic", or "mock".
        Controls default shapes, preprocessing params, and label maps.
    config : dict, optional
        Overrides default configuration.
    """

    def __init__(
        self,
        snirf_paths: Optional[List[Union[str, Path]]] = None,
        dataset: str = "mock",
        config: Optional[dict] = None,
    ):
        self.snirf_paths = snirf_paths or []
        self.dataset_name = dataset

        # Merge dataset defaults with user overrides
        self.dataset_config = get_dataset_config(dataset)
        self.config = dict(self.dataset_config)
        if config:
            self.config.update(config)

        self._data: Optional[Dict[str, Any]] = None
        self._train_dataset: Optional[fNIRSDataset] = None
        self._val_dataset: Optional[fNIRSDataset] = None
        self._test_dataset: Optional[fNIRSDataset] = None

        if not TORCH_AVAILABLE:
            logger.warning(
                "PyTorch is not installed. DataLoaders require it. "
                "Install with: pip install torch"
            )

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------

    def prepare_data(self):
        """Load (or generate) and preprocess all data."""
        if self._data is not None:
            return

        if self.dataset_name == "mock" or len(self.snirf_paths) == 0:
            logger.info(
                f"Generating mock data for '{self.dataset_name}' dataset"
            )
            self._generate_mock_data()
        else:
            self._load_real_data()

        logger.info(
            f"Data loaded: {self._data['data'].shape}, "
            f"{len(np.unique(self._data['labels']))} classes, "
            f"{len(np.unique(self._data['subject_ids']))} subjects"
        )

    def _generate_mock_data(self):
        """Generate synthetic data matching the dataset configuration."""
        gen = MockfNIRSGenerator(self.dataset_config)
        self._data = gen.generate()

    def _load_real_data(self):
        """Load SNIRF files via nlcore."""
        try:
            from nlcore import load_snirf
            from nlcore.physiology.chromophore import compute_hbo_hbr
            from nlcore.preprocessing.filtering import bandpass_filter as bp_filter
        except ImportError:
            logger.warning(
                "nlcore not installed — falling back to mock data. "
                "Install with: pip install -e /home/team/shared/nlcore"
            )
            self._generate_mock_data()
            return

        fs = self.config["fs"]
        bp = self.config["bandpass"]
        tmin = self.config["tmin"]
        tmax = self.config["tmax"]
        baseline = self.config["baseline"]

        all_data, all_labels, all_subjects = [], [], []

        for i, path in enumerate(self.snirf_paths):
            path = Path(path)
            if not path.exists():
                logger.warning(f"File not found: {path}")
                continue

            try:
                raw = load_snirf(str(path))
                raw = compute_hbo_hbr(raw)
                raw = bp_filter(raw, *bp)

                if abs(raw.info["sfreq"] - fs) > 0.5:
                    raw.resample(fs)

                # Extract epochs from annotations
                events = raw.annotations
                if len(events) == 0:
                    logger.warning(f"No events in {path}, skipping.")
                    continue

                # Simple epoch extraction (placeholder — real impl uses mne.Epochs)
                from mne import Epochs
                epochs = Epochs(
                    raw,
                    events=None,
                    tmin=tmin,
                    tmax=tmax,
                    baseline=baseline,
                    preload=True,
                )
                data = epochs.get_data()  # (n_epochs, n_channels, n_timepoints)
                data = (data - data.mean(axis=(0, 2), keepdims=True)) / data.std(
                    axis=(0, 2), keepdims=True
                )

                label_map = self.config["label_map"]
                labels = np.array(
                    [
                        label_map.get(ev["description"], -1)
                        for ev in events
                    ]
                )
                valid = labels >= 0
                data, labels = data[valid], labels[valid]

                all_data.append(data)
                all_labels.append(labels)
                all_subjects.append(np.full(len(data), i))

            except Exception as e:
                logger.error(f"Failed to process {path}: {e}")

        if len(all_data) == 0:
            logger.warning("No real data loaded — falling back to mock.")
            self._generate_mock_data()
            return

        self._data = {
            "data": np.concatenate(all_data, axis=0).astype(np.float32),
            "labels": np.concatenate(all_labels, axis=0).astype(np.int64),
            "subject_ids": np.concatenate(all_subjects, axis=0).astype(np.int64),
            "metadata": {
                "n_channels": all_data[0].shape[1],
                "n_timepoints": all_data[0].shape[2],
                "n_classes": len(np.unique(np.concatenate(all_labels))),
                "fs": fs,
                "dataset": self.dataset_name,
            },
        }

    # -----------------------------------------------------------------------
    # Dataset splitting
    # -----------------------------------------------------------------------

    def setup(self, stage: Optional[str] = None):
        """Split data into train/val sets."""
        if self._data is None:
            self.prepare_data()

        data = self._data["data"]
        labels = self._data["labels"]
        subject_ids = self._data["subject_ids"]

        strategy = self.config.get("val_strategy", "loso")

        if strategy == "loso" and subject_ids is not None:
            unique_subjects = np.unique(subject_ids)
            if len(unique_subjects) < 2:
                self._simple_split(data, labels)
            else:
                val_subject = unique_subjects[-1]
                train_mask = subject_ids != val_subject
                val_mask = subject_ids == val_subject
                self._train_dataset = fNIRSDataset(
                    data[train_mask], labels[train_mask]
                )
                self._val_dataset = fNIRSDataset(
                    data[val_mask], labels[val_mask]
                )
                logger.info(
                    f"LOSO: {len(data[train_mask])} train, "
                    f"{len(data[val_mask])} val (held-out subj {val_subject})"
                )

        elif strategy == "kfold":
            n_folds = self.config.get("n_folds", 5)
            kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
            folds = list(kf.split(data))
            train_idx, val_idx = folds[0]
            self._train_dataset = fNIRSDataset(data[train_idx], labels[train_idx])
            self._val_dataset = fNIRSDataset(data[val_idx], labels[val_idx])
            logger.info(f"K-Fold (fold 0/{n_folds}): {len(train_idx)}/{len(val_idx)}")

        else:
            self._simple_split(data, labels)

    def _simple_split(self, data: np.ndarray, labels: np.ndarray):
        val_ratio = self.config.get("val_ratio", 0.2)
        n_total = len(data)
        n_val = max(1, int(n_total * val_ratio))
        rng = np.random.default_rng(42)
        indices = rng.permutation(n_total)
        train_idx, val_idx = indices[n_val:], indices[:n_val]
        self._train_dataset = fNIRSDataset(data[train_idx], labels[train_idx])
        self._val_dataset = fNIRSDataset(data[val_idx], labels[val_idx])
        logger.info(f"Holdout: {len(train_idx)} train, {len(val_idx)} val")

    # -----------------------------------------------------------------------
    # DataLoaders
    # -----------------------------------------------------------------------

    def _require_torch(self):
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for DataLoader creation. "
                "Install with: pip install torch"
            )

    def train_dataloader(self):
        self._require_torch()
        if self._train_dataset is None:
            self.setup("fit")
        return DataLoader(
            self._train_dataset,
            batch_size=self.config.get("batch_size", 32),
            shuffle=True,
            num_workers=self.config.get("num_workers", 0),
        )

    def val_dataloader(self):
        self._require_torch()
        if self._val_dataset is None:
            self.setup("validate")
        return DataLoader(
            self._val_dataset,
            batch_size=self.config.get("batch_size", 32),
            shuffle=False,
            num_workers=self.config.get("num_workers", 0),
        )

    def test_dataloader(self):
        return self.val_dataloader()

    def get_dataloader(self, batch_size: Optional[int] = None, shuffle: bool = True):
        """Combined DataLoader over all data (for quick testing)."""
        self._require_torch()
        if self._data is None:
            self.prepare_data()
        ds = fNIRSDataset(self._data["data"], self._data["labels"])
        return DataLoader(
            ds,
            batch_size=batch_size or self.config.get("batch_size", 32),
            shuffle=shuffle,
        )

    @property
    def data_shape(self):
        if self._data is None:
            return None
        return self._data["data"].shape

    @property
    def n_classes(self):
        if self._data is None:
            return None
        return len(np.unique(self._data["labels"]))

    @property
    def n_channels(self):
        if self._data is None:
            return None
        return self._data["data"].shape[1]

    @property
    def n_timepoints(self):
        if self._data is None:
            return None
        return self._data["data"].shape[2]


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== fNIRS DataModule Self-Test ===\n")

    for ds_name in ["fnirs2mw", "mental_arithmetic", "mock"]:
        cfg = get_dataset_config(ds_name)
        print(f"--- {cfg['description']} ---")
        print(f"  Subjects: {cfg['n_subjects']}, Channels: {cfg['n_channels']}, "
              f"Classes: {cfg['n_classes']}, Epochs/subj: {cfg['epochs_per_subject']}")

        dm = fNIRSDataModule(dataset=ds_name, config={"batch_size": 8})
        dm.prepare_data()
        print(f"  Generated: {dm.data_shape}")

        if TORCH_AVAILABLE:
            dm.setup()
            loader = dm.train_dataloader()
            x, y = next(iter(loader))
            print(f"  Batch: data={x.shape}, labels={y.shape}")
        else:
            print(f"  Data ready, {dm.n_classes} classes")

        print()

    if not TORCH_AVAILABLE:
        print("Note: PyTorch not installed. Install for DataLoader access:")
        print("  pip install torch")
    else:
        print("All DataLoader tests passed.")

    print("\n=== Self-test complete ===")
