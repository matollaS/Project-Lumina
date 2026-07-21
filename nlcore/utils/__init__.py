"""Utility functions for MNE-Python compatibility and general helpers."""

from .mne_compat import SourceDetectorMap, mne_to_raw, raw_to_mne

__all__ = ["raw_to_mne", "mne_to_raw", "SourceDetectorMap"]
