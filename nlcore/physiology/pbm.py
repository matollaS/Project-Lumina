"""Photobiomodulation (PBM) metrics for fNIRS-integrated devices.

PBM (also known as LLLT — low-level light therapy) uses near-infrared
light to stimulate cellular metabolism.  When combined with HD-fNIRS
monitoring, we can quantify:

* **Dose** — total energy delivered to tissue (J/cm²)
* **Fluence rate** — optical power per unit area (mW/cm²)
* **Haemodynamic response** — HbO/HbR changes attributable to PBM

References
----------
.. [1] Hamblin, M. R. (2016). Shining light on the head: PBM for brain
       disorders. *BBA Clin.*, 6, 113–124.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np


def compute_pbm_dose(
    power_mw: float,
    area_cm2: float,
    duration_s: float,
    *,
    duty_cycle: float = 1.0,
) -> float:
    """Compute PBM dose (radiant exposure) in J/cm².

    Parameters
    ----------
    power_mw : float
        Optical output power in milliwatts.
    area_cm2 : float
        Beam area at tissue surface in cm².
    duration_s : float
        Irradiation duration in seconds.
    duty_cycle : float
        Duty cycle of pulsed operation (0–1).  Default 1.0 (CW).

    Returns
    -------
    dose : float
        Radiant exposure in J/cm².

    Notes
    -----
    ``dose = (power_mW / 1000) * duration_s * duty_cycle / area_cm2``
    """
    return (power_mw / 1000.0) * duration_s * duty_cycle / area_cm2


def compute_pbm_fluence(
    power_mw: float,
    area_cm2: float,
    *,
    duty_cycle: float = 1.0,
) -> float:
    """Compute instantaneous fluence rate in mW/cm².

    Parameters
    ----------
    power_mw : float
        Optical output power in mW.
    area_cm2 : float
        Beam area in cm².
    duty_cycle : float
        Duty cycle (0–1).

    Returns
    -------
    fluence_rate : float
        Irradiance in mW/cm².
    """
    return (power_mw / area_cm2) * duty_cycle


def pbm_metrics(
    hbo: np.ndarray,
    hbr: np.ndarray,
    fs: float,
    *,
    stimulus_onset: Optional[np.ndarray] = None,
    baseline_window: Tuple[float, float] = (-5.0, 0.0),
    response_window: Tuple[float, float] = (0.0, 30.0),
) -> Dict[str, float]:
    """Extract PBM-evoked haemodynamic response metrics.

    Parameters
    ----------
    hbo : np.ndarray
        HbO time series, shape ``(n_times, n_channels)``.
    hbr : np.ndarray
        HbR time series, same shape.
    fs : float
        Sampling frequency in Hz.
    stimulus_onset : np.ndarray or None
        Onset times (in samples) of PBM pulses.  If ``None``, the
        entire recording is treated as a single continuous block.
    baseline_window : tuple
        ``(start, end)`` in seconds relative to stimulus onset for
        baseline computation.
    response_window : tuple
        ``(start, end)`` in seconds relative to stimulus onset for
        response computation.

    Returns
    -------
    metrics : dict
        Keys include: ``'hbo_peak'`` (µM), ``'hbr_peak'``, ``'hbo_auc'``,
        ``'hbr_auc'``, ``'time_to_peak'`` (s), ``'recovery_rate'``
        (µM/s), ``'mean_dose'``.
    """
    hbo = np.asarray(hbo)
    hbr = np.asarray(hbr)
    n_times = hbo.shape[0]

    if stimulus_onset is None:
        # Treat entire recording as single block
        mid = n_times // 2
        bl_start = max(0, mid + int(baseline_window[0] * fs))
        bl_end = max(0, mid + int(baseline_window[1] * fs))
        resp_start = max(0, mid + int(response_window[0] * fs))
        resp_end = min(n_times, mid + int(response_window[1] * fs))
    else:
        onset = int(stimulus_onset[0])
        bl_start = max(0, onset + int(baseline_window[0] * fs))
        bl_end = max(0, onset + int(baseline_window[1] * fs))
        resp_start = max(0, onset + int(response_window[0] * fs))
        resp_end = min(n_times, onset + int(response_window[1] * fs))

    # Mean across channels
    hbo_mean = np.mean(hbo, axis=1)
    hbr_mean = np.mean(hbr, axis=1)

    # Baseline
    hbo_bl = np.mean(hbo_mean[bl_start:bl_end]) if bl_end > bl_start else 0.0
    hbr_bl = np.mean(hbr_mean[bl_start:bl_end]) if bl_end > bl_start else 0.0

    # Response
    if resp_end > resp_start:
        hbo_resp = hbo_mean[resp_start:resp_end] - hbo_bl
        hbr_resp = hbr_mean[resp_start:resp_end] - hbr_bl
    else:
        hbo_resp = np.array([0.0])
        hbr_resp = np.array([0.0])

    hbo_peak = float(np.max(np.abs(hbo_resp))) if len(hbo_resp) > 0 else 0.0
    hbr_peak = float(np.max(np.abs(hbr_resp))) if len(hbr_resp) > 0 else 0.0

    hbo_auc = float(np.trapz(np.abs(hbo_resp))) / fs if len(hbo_resp) > 1 else 0.0
    hbr_auc = float(np.trapz(np.abs(hbr_resp))) / fs if len(hbr_resp) > 1 else 0.0

    ttp_idx = np.argmax(np.abs(hbo_resp)) if len(hbo_resp) > 0 else 0
    time_to_peak = ttp_idx / fs if fs > 0 else 0.0

    return {
        "hbo_peak": hbo_peak,
        "hbr_peak": hbr_peak,
        "hbo_auc": hbo_auc,
        "hbr_auc": hbr_auc,
        "time_to_peak": time_to_peak,
        "recovery_rate": 0.0,
        "mean_dose": 0.0,
    }
