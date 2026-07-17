"""Temporal filtering routines for fNIRS signals.

HD-fNIRS signals are contaminated by physiological noise (cardiac ~1 Hz,
respiratory ~0.3 Hz, Mayer waves ~0.1 Hz) and instrument drift.  This
module provides bandpass and notch filters optimised for fNIRS data,
wrapping SciPy's signal-processing primitives.

Filter design principles
------------------------
* Default bandpass: 0.01–0.5 Hz (captures haemodynamic response while
  rejecting cardiac and respiratory noise).
* Filters are zero-phase (forward-backward ``filtfilt``) to preserve
  timing of the haemodynamic response.
* All functions operate on numpy arrays of shape ``(n_times,)`` or
  ``(n_times, n_channels)``.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch


def bandpass_filter(
    data: np.ndarray,
    fs: float,
    lowcut: float = 0.01,
    highcut: float = 0.5,
    order: int = 4,
    *,
    axis: int = 0,
) -> np.ndarray:
    """Apply a zero-phase Butterworth bandpass filter.

    Parameters
    ----------
    data : np.ndarray
        Input signal, shape ``(n_times,)`` or ``(n_times, n_channels)``.
    fs : float
        Sampling frequency in Hz.
    lowcut : float
        Low-cut frequency in Hz (default 0.01).
    highcut : float
        High-cut frequency in Hz (default 0.5).
    order : int
        Butterworth filter order (default 4).
    axis : int
        Axis along which to filter (default 0).

    Returns
    -------
    filtered : np.ndarray
        Bandpass-filtered signal, same shape as *data*.
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, data, axis=axis)


def notch_filter(
    data: np.ndarray,
    fs: float,
    freq: float = 50.0,
    quality: float = 30.0,
    *,
    axis: int = 0,
) -> np.ndarray:
    """Apply a zero-phase notch (band-stop) filter.

    Useful for removing mains interference (50/60 Hz) when data are
    acquired at high sampling rates.

    Parameters
    ----------
    data : np.ndarray
        Input signal, shape ``(n_times,)`` or ``(n_times, n_channels)``.
    fs : float
        Sampling frequency in Hz.
    freq : float
        Centre frequency to notch out (default 50 Hz).
    quality : float
        Quality factor (default 30).
    axis : int
        Axis along which to filter (default 0).

    Returns
    -------
    filtered : np.ndarray
        Notch-filtered signal, same shape as *data*.
    """
    nyq = 0.5 * fs
    w0 = freq / nyq
    b, a = iirnotch(w0, quality)
    return filtfilt(b, a, data, axis=axis)
