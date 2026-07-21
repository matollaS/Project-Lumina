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
    data = np.asarray(data)
    if data.ndim == 1:
        data = data[:, np.newaxis]

    n_times, n_channels = data.shape
    mask = np.zeros_like(data, dtype=bool)

    for ch in range(n_channels):
        ch_data = data[:, ch]

        # Absolute amplitude difference between consecutive points
        diff = np.abs(np.diff(ch_data, prepend=ch_data[0]))
        amp_flags = diff > amp_thresh

        # Moving standard deviation (window based on t_motion)
        window_size = max(1, int(t_motion * fs))
        # Simple rolling std using uniform filter
        from scipy.ndimage import uniform_filter1d

        c1 = uniform_filter1d(ch_data, size=window_size)
        c2 = uniform_filter1d(ch_data * ch_data, size=window_size)
        std_arr = np.sqrt(np.maximum(c2 - c1 * c1, 0))

        # Global std excluding clear outliers
        global_std = np.std(ch_data)
        std_flags = std_arr > (std_thresh * global_std)

        mask[:, ch] = amp_flags | std_flags

    return mask if mask.shape[1] > 1 else mask[:, 0]


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
    from scipy.interpolate import CubicSpline

    data = np.asarray(data)
    is_1d = data.ndim == 1
    if is_1d:
        data = data[:, np.newaxis]
        mask = mask[:, np.newaxis]

    n_times, n_channels = data.shape
    corrected = data.copy()
    times = np.arange(n_times)

    for ch in range(n_channels):
        m = mask[:, ch]
        if not np.any(m):
            continue
        valid = ~m
        if np.sum(valid) < 2:
            continue

        # Fit cubic spline to valid points
        cs = CubicSpline(times[valid], data[valid, ch], bc_type="natural")
        # Replace only the masked points
        corrected[m, ch] = cs(times[m])

    return corrected[:, 0] if is_1d else corrected


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
    from sklearn.decomposition import PCA

    data = np.asarray(data)
    n_times, n_channels = data.shape

    # We apply PCA only on the motion-corrupted segments to find the motion components
    # Then we project the entire data and remove those components
    m_any = np.any(mask, axis=1) if mask.ndim > 1 else mask

    if not np.any(m_any):
        return data.copy()

    # Extract corrupted data
    corrupted_data = data[m_any]

    # Fit PCA
    pca = PCA(n_components=n_components)
    pca.fit(corrupted_data)

    # Reconstruct whole signal without the top principal components
    # data_proj = data @ components.T
    # data_clean = data - data_proj @ components
    components = pca.components_  # shape (n_components, n_channels)

    projected = data @ components.T
    motion_recon = projected @ components

    corrected = data - motion_recon
    return corrected


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
    import pywt

    data = np.asarray(data)
    is_1d = data.ndim == 1
    if is_1d:
        data = data[:, np.newaxis]

    n_times, n_channels = data.shape
    corrected = np.zeros_like(data)

    for ch in range(n_channels):
        ch_data = data[:, ch]

        # Decompose
        coeffs = pywt.wavedec(ch_data, wavelet, level=level)

        # Soft thresholding based on universal threshold (Donoho & Johnstone)
        # We apply thresholding to detail coefficients
        sigma = np.median(np.abs(coeffs[-1] - np.median(coeffs[-1]))) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(n_times))

        new_coeffs = [coeffs[0]]  # Keep approximation
        for detail in coeffs[1:]:
            new_coeffs.append(pywt.threshold(detail, value=threshold, mode="soft"))

        # Reconstruct
        rec = pywt.waverec(new_coeffs, wavelet)
        # Pad or truncate if lengths don't match exactly due to pywt padding
        if len(rec) > n_times:
            rec = rec[:n_times]
        elif len(rec) < n_times:
            rec = np.pad(rec, (0, n_times - len(rec)), mode="edge")

        corrected[:, ch] = rec

    return corrected[:, 0] if is_1d else corrected
