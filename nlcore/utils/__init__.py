"""Utility functions for MNE-Python compatibility and general helpers."""
from .mne_compat import raw_to_mne, mne_to_raw, SourceDetectorMap

__all__ = ["raw_to_mne", "mne_to_raw", "SourceDetectorMap"]
