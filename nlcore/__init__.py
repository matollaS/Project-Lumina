"""
nlcore — NeuroLumina Core
=========================

Open-source Python library for HD-fNIRS and PBM signal processing.

Modules
-------
io          — SNIRF file I/O and data loading
preprocessing — Motion correction, filtering, artifact removal
physiology  — Chromophore conversion (modified Beer-Lambert), PBM metrics
inference   — Research dose-response and individualized response modelling
validation  — Prospective and held-out model evaluation
utils       — MNE-Python compatibility utilities and helpers

Examples
--------
>>> from nlcore import load_snirf
>>> raw = load_snirf("recording.snirf")
>>> raw  # MNE-compatible Raw object
"""

from importlib.metadata import version

from nlcore.inference.response import (
    IndividualDoseResponseModel,
    ResponsePrediction,
    extract_dose_response,
)
from nlcore.io.snirf import load_snirf, save_snirf
from nlcore.physiology.chromophore import (
    compute_hbo_hbr,
    estimate_dpf,
    extinction_matrix,
    modified_beer_lambert,
    optical_density,
)
from nlcore.physiology.pbm import (
    compute_pbm_dose,
    compute_pbm_fluence,
    pbm_metrics,
)
from nlcore.preprocessing.filtering import bandpass_filter, notch_filter
from nlcore.preprocessing.motion import (
    correct_motion_pca,
    correct_motion_spline,
    correct_motion_wavelet,
    detect_motion_artifacts,
)
from nlcore.validation.prospective import ValidationReport, evaluate_unseen_subjects

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
    # Inference — individualized response modelling
    "IndividualDoseResponseModel",
    "ResponsePrediction",
    "extract_dose_response",
    # Validation — held-out generalization
    "ValidationReport",
    "evaluate_unseen_subjects",
]

try:
    __version__ = version("nlcore")
except Exception:
    __version__ = "0.1.0"
