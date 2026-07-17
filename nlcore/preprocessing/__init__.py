"""HD-fNIRS preprocessing: filtering, motion correction, artifact removal."""
from .filtering import bandpass_filter, notch_filter
from .motion import (
    detect_motion_artifacts,
    correct_motion_spline,
    correct_motion_pca,
    correct_motion_wavelet,
)

__all__ = [
    "bandpass_filter",
    "notch_filter",
    "detect_motion_artifacts",
    "correct_motion_spline",
    "correct_motion_pca",
    "correct_motion_wavelet",
]
