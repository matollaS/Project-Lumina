"""SNIRF-compatible file I/O for HD-fNIRS data.

This module provides readers and writers for the Shared Near-Infrared
Spectroscopy Format (SNIRF), an HDF5-based standard for fNIRS data.
It produces numpy arrays and MNE-compatible structures.
"""

from .snirf import SnirfFile, load_snirf, save_snirf

__all__ = ["load_snirf", "save_snirf", "SnirfFile"]
