"""
nlcore — NeuroLumina Core
=========================

Open-source Python library for HD-fNIRS and PBM signal processing.

Modules
-------
io          — SNIRF file I/O and data loading
preprocessing — Motion correction, filtering, artifact removal
physiology  — Chromophore conversion (modified Beer-Lambert), PBM metrics
utils       — MNE-Python compatibility utilities and helpers

Examples
--------
>>> from nlcore import load_snirf
>>> raw = load_snirf("recording.snirf")
>>> raw  # MNE-compatible Raw object
"""

from importlib.metadata import version

from nlcore.io.snirf import load_snirf, save_snirf
from nlcore.preprocessing.filtering import bandpass_filter, notch_filter
from nlcore.preprocessing.motion import (
    detect_motion_artifacts,
    correct_motion_spline,
    correct_motion_pca,
    correct_motion_wavelet,
)
from nlcore.physiology.chromophore import (
    optical_density,
    modified_beer_lambert,
    compute_hbo_hbr,
    extinction_matrix,
    estimate_dpf,
)
from nlcore.physiology.pbm import (
    compute_pbm_dose,
    compute_pbm_fluence,
    pbm_metrics,
)

__all__ = [
    # I/O
    "load_snirf",
    "save_snirf",
    # Preprocessing — filtering
    "bandpass_filter",
    "notch_filter",
    # Preprocessing — motion
    "detect_motion_artifacts",
    "correct_motion_spline",
    "correct_motion_pca",
    "correct_motion_wavelet",
    # Physiology — chromophore
    "optical_density",
    "modified_beer_lambert",
    "compute_hbo_hbr",
    "extinction_matrix",
    "estimate_dpf",
    # Physiology — PBM
    "compute_pbm_dose",
    "compute_pbm_fluence",
    "pbm_metrics",
]

try:
    __version__ = version("nlcore")
except Exception:
    __version__ = "0.1.0"
