"""Motion artifact detection and correction for fNIRS signals.

Head motion causes sharp, large-amplitude transients in fNIRS time
series.  This module provides:

* **Detection** — identify corrupted segments using amplitude
  thresholds and derivative-based methods.
* **Correction** — repair corrupted segments with spline interpolation,
  wavelet thresholding, or PCA-based approaches.

References
----------
.. [1] Scholkmann, F., et al. (2010). A new method for motion artifact
       suppression in fNIRS. *Physiol. Meas.*, 31(5), 649.
.. [2] Brigadoi, S., et al. (2014). Motion artifacts in fNIRS: a
       comparison of correction techniques. *NeuroImage*, 85, 181–191.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


def detect_motion_artifacts(
    data: np.ndarray,
    fs: float,
    *,
    amp_thresh: float = 0.5,
    std_thresh: float = 3.0,
    t_motion: float = 1.0,
) -> np.ndarray:
    """Identify time points corrupted by motion artifacts.

    Uses a combined amplitude-change and moving-standard-deviation
    criterion [1]_.

    Parameters
    ----------
    data : np.ndarray
        Signal, shape ``(n_times,)`` or ``(n_times, n_channels)``.
    fs : float
        Sampling frequency in Hz.
    amp_thresh : float
        Amplitude-change threshold (in signal units).  Segments where
        ``|x[t] - x[t-1]| > amp_thresh`` are flagged.
    std_thresh : float
        Number of standard deviations above which the moving std
        triggers a flag.
    t_motion : float
        Minimum duration (seconds) of a motion epoch.

    Returns
    -------
    mask : np.ndarray of bool
        Boolean mask of shape ``(n_times,)`` or ``(n_times, n_channels)``,
        ``True`` where artifacts are detected.
    """
    ...


def correct_motion_spline(
    data: np.ndarray,
    mask: np.ndarray,
    *,
    order: int = 3,
    axis: int = 0,
) -> np.ndarray:
    """Repair motion-artifact segments using cubic spline interpolation.

    The masked samples are removed and the gap is filled by a cubic
    spline fitted to the surrounding clean samples (cf. [1]_).

    Parameters
    ----------
    data : np.ndarray
        Signal, shape ``(n_times,)`` or ``(n_times, n_channels)``.
    mask : np.ndarray of bool
        Boolean mask, same shape as *data*, where ``True`` marks
        samples to be interpolated.
    order : int
        Spline order (default 3, cubic).
    axis : int
        Time axis (default 0).

    Returns
    -------
    corrected : np.ndarray
        Motion-corrected signal, same shape as *data*.
    """
    ...


def correct_motion_pca(
    data: np.ndarray,
    mask: np.ndarray,
    *,
    n_components: int = 5,
    axis: int = 0,
) -> np.ndarray:
    """Remove motion artifacts via PCA on the channel covariance.

    Assumes that motion artifacts are spatially correlated across many
    channels and can be removed by subtracting the top principal
    components computed from the motion-corrupted segments [2]_.

    Parameters
    ----------
    data : np.ndarray
        Signal, shape ``(n_times, n_channels)``.
    mask : np.ndarray of bool
        Boolean mask, same shape as *data*.
    n_components : int
        Number of principal components to remove (default 5).
    axis : int
        Time axis (default 0).

    Returns
    -------
    corrected : np.ndarray
        PCA-corrected signal, same shape as *data*.
    """
    ...


def correct_motion_wavelet(
    data: np.ndarray,
    mask: np.ndarray,
    *,
    wavelet: str = "db4",
    level: int = 5,
    axis: int = 0,
) -> np.ndarray:
    """Suppress motion artifacts using wavelet thresholding.

    Decomposes the signal with a discrete wavelet transform and applies
    soft thresholding to coefficients in the detail levels that are
    dominated by motion energy.

    Parameters
    ----------
    data : np.ndarray
        Signal, shape ``(n_times,)`` or ``(n_times, n_channels)``.
    mask : np.ndarray of bool
        Boolean mask, ``True`` marks corrupted samples.
    wavelet : str
        Wavelet name, e.g. ``'db4'`` (default).
    level : int
        Decomposition level.
    axis : int
        Time axis (default 0).

    Returns
    -------
    corrected : np.ndarray
        Wavelet-corrected signal, same shape as *data*.

    Notes
    -----
    Requires PyWavelets (``pywt``) to be installed.
    """
    ...
