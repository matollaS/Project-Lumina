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

# np.trapz was removed in NumPy 2.0 (renamed np.trapezoid); pyproject.toml
# only requires numpy>=1.24 with no upper bound, so pick whichever the
# installed version provides.
_trapz = getattr(np, "trapezoid", None) or np.trapz


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


def _fit_recovery_rate(
    resp: np.ndarray,
    peak_idx: int,
    fs: float,
) -> float:
    """Estimate the post-peak recovery rate of a haemodynamic response.

    Fits a straight line (least-squares) to the segment running from the
    response peak to the end of the response window, and returns the
    magnitude of its slope in µM/s. A positive value means the signal is
    decaying back toward baseline after the peak; a value of ``0.0`` is
    returned if there are too few post-peak samples to fit a trend or if
    the segment is not decaying (e.g. still rising at the window edge).

    Parameters
    ----------
    resp : np.ndarray
        The (baseline-subtracted) response segment, 1-D.
    peak_idx : int
        Index of the peak within ``resp``.
    fs : float
        Sampling frequency in Hz.

    Returns
    -------
    rate : float
        Recovery rate in µM/s (non-negative).
    """
    tail = resp[peak_idx:]
    n = len(tail)
    if n < 3 or fs <= 0:
        return 0.0

    t = np.arange(n) / fs
    # Least-squares linear fit: tail(t) ~= intercept + slope * t
    slope, _intercept = np.polyfit(t, tail, 1)

    # A recovering response decays back toward baseline, i.e. the
    # magnitude of the (signed) response shrinks over time. Express
    # that as a non-negative rate; a rising/non-recovering tail yields 0.
    sign = np.sign(tail[0]) if tail[0] != 0 else 1.0
    rate = -sign * slope
    return float(max(rate, 0.0))


def pbm_metrics(
    hbo: np.ndarray,
    hbr: np.ndarray,
    fs: float,
    *,
    stimulus_onset: Optional[np.ndarray] = None,
    baseline_window: Tuple[float, float] = (-5.0, 0.0),
    response_window: Tuple[float, float] = (0.0, 30.0),
    power_mw: Optional[float] = None,
    area_cm2: Optional[float] = None,
    duty_cycle: float = 1.0,
    dose_duration_s: Optional[float] = None,
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
    power_mw : float or None
        Optical output power in mW for the PBM source used during this
        recording. If provided together with ``area_cm2``, the delivered
        dose is computed via :func:`compute_pbm_dose`. If omitted,
        ``'mean_dose'`` in the returned metrics is ``0.0``.
    area_cm2 : float or None
        Beam area at the tissue surface in cm², paired with ``power_mw``.
    duty_cycle : float
        Duty cycle of pulsed operation (0-1). Default 1.0 (CW).
    dose_duration_s : float or None
        Irradiation duration used for the dose calculation. Defaults to
        the length of the response window (in seconds) if not given.

    Returns
    -------
    metrics : dict
        Keys include: ``'hbo_peak'`` (µM), ``'hbr_peak'``, ``'hbo_auc'``,
        ``'hbr_auc'``, ``'time_to_peak'`` (s), ``'recovery_rate'``
        (µM/s, non-negative — rate of decay back toward baseline after
        the HbO peak), ``'mean_dose'`` (J/cm², 0.0 if ``power_mw``/
        ``area_cm2`` are not supplied).
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

    hbo_auc = float(_trapz(np.abs(hbo_resp))) / fs if len(hbo_resp) > 1 else 0.0
    hbr_auc = float(_trapz(np.abs(hbr_resp))) / fs if len(hbr_resp) > 1 else 0.0

    ttp_idx = int(np.argmax(np.abs(hbo_resp))) if len(hbo_resp) > 0 else 0
    time_to_peak = ttp_idx / fs if fs > 0 else 0.0

    recovery_rate = _fit_recovery_rate(hbo_resp, ttp_idx, fs) if len(hbo_resp) > 0 else 0.0

    mean_dose = 0.0
    if power_mw is not None and area_cm2 is not None:
        if dose_duration_s is not None:
            duration_s = dose_duration_s
        elif resp_end > resp_start and fs > 0:
            duration_s = (resp_end - resp_start) / fs
        else:
            duration_s = response_window[1] - response_window[0]
        mean_dose = compute_pbm_dose(
            power_mw=power_mw,
            area_cm2=area_cm2,
            duration_s=duration_s,
            duty_cycle=duty_cycle,
        )

    return {
        "hbo_peak": hbo_peak,
        "hbr_peak": hbr_peak,
        "hbo_auc": hbo_auc,
        "hbr_auc": hbr_auc,
        "time_to_peak": time_to_peak,
        "recovery_rate": recovery_rate,
        "mean_dose": mean_dose,
    }
