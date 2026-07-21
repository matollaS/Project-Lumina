"""Chromophore concentration computation via the modified Beer-Lambert law.

Continuous-wave fNIRS measures changes in light attenuation at two or
more wavelengths.  This module converts raw intensity (or optical
density) signals into oxy-haemoglobin (HbO) and deoxy-haemoglobin (HbR)
concentration changes using the modified Beer-Lambert law (mBLL).

Theory
------
ΔOD(λ) = (ε_HbO(λ) · Δ[HbO] + ε_HbR(λ) · Δ[HbR]) · d · DPF(λ)

The system is solved per channel–time point via the pseudo-inverse of
the extinction matrix.

References
----------
.. [1] Delpy, D. T., et al. (1988). *Phys. Med. Biol.*, 33(12), 1433.
.. [2] Scholkmann, F., & Wolf, M. (2013). *J. Biomed. Opt.*, 18(10), 105004.
"""

from __future__ import annotations

import numpy as np

# Extinction coefficients (µM⁻¹·cm⁻¹) for common fNIRS wavelengths
# Source: UCL Biomedical Optics Research Laboratory database
EXTINCTION_COEFFS: dict[float, tuple[float, float]] = {
    690: (0.312, 2.138),
    760: (0.456, 1.540),
    830: (0.726, 0.814),
    850: (0.864, 0.724),
}


def _interpolate_extinction(wavelength: float) -> tuple[float, float]:
    """Linearly interpolate extinction coefficients for an arbitrary wavelength."""
    wls = sorted(EXTINCTION_COEFFS.keys())
    if wavelength <= wls[0]:
        return EXTINCTION_COEFFS[wls[0]]
    if wavelength >= wls[-1]:
        return EXTINCTION_COEFFS[wls[-1]]
    for i in range(len(wls) - 1):
        if wls[i] <= wavelength <= wls[i + 1]:
            frac = (wavelength - wls[i]) / (wls[i + 1] - wls[i])
            e0 = np.array(EXTINCTION_COEFFS[wls[i]])
            e1 = np.array(EXTINCTION_COEFFS[wls[i + 1]])
            e = e0 + frac * (e1 - e0)
            return (float(e[0]), float(e[1]))
    raise ValueError(f"Cannot interpolate extinction for {wavelength} nm")


def extinction_matrix(wavelengths: np.ndarray) -> np.ndarray:
    """Build the molar extinction coefficient matrix E (n_wl × 2).

    Parameters
    ----------
    wavelengths : np.ndarray
        Wavelengths in nm.

    Returns
    -------
    E : np.ndarray
        Shape ``(n_wl, 2)``, columns ``(ε_HbO, ε_HbR)``.
    """
    n_wl = len(wavelengths)
    E = np.zeros((n_wl, 2))
    for i, wl in enumerate(wavelengths):
        e_hbo, e_hbr = _interpolate_extinction(float(wl))
        E[i, 0] = e_hbo
        E[i, 1] = e_hbr
    return E


def estimate_dpf(wavelength: float, age: float = 25.0) -> float:
    """Estimate DPF via the Scholkmann–Wolf model [2]_.

    Parameters
    ----------
    wavelength : float
        Wavelength in nm.
    age : float
        Subject age in years.

    Returns
    -------
    dpf : float
        Estimated differential pathlength factor.
    """
    a, b, c = 223.3, 0.05624, 0.8493
    d, e, f = -5.723e-7, 0.001245, -0.9025
    dpf = a + b * (age**c) + d * (wavelength**3) + e * (wavelength**2) + f * wavelength
    return max(1.0, min(dpf, 15.0))


def optical_density(
    intensity: np.ndarray,
    baseline: np.ndarray | None = None,
) -> np.ndarray:
    """Convert raw intensity to optical density (attenuation).

    ΔOD = -log₁₀(I / I₀) where I₀ is the baseline.

    Parameters
    ----------
    intensity : np.ndarray
        Raw intensity, shape ``(n_times, n_channels)``.
    baseline : np.ndarray or None
        Baseline per channel, shape ``(n_channels,)``.  Uses temporal mean if None.

    Returns
    -------
    od : np.ndarray
        Optical density changes, same shape as intensity.
    """
    intensity = np.asarray(intensity, dtype=np.float64)
    if baseline is None:
        I0 = np.mean(intensity, axis=0, keepdims=True)
    else:
        I0 = np.asarray(baseline, dtype=np.float64).reshape(1, -1)
    I0 = np.maximum(I0, 1e-12)
    ratio = np.maximum(intensity / I0, 1e-12)
    return -np.log10(ratio)


def modified_beer_lambert(
    od: np.ndarray,
    wavelengths: np.ndarray,
    d: np.ndarray | None = None,
    dpf: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert multi-wavelength optical density to HbO/HbR concentrations.

    Parameters
    ----------
    od : np.ndarray
        OD, shape ``(n_times, n_wl, n_sd_pairs)`` or ``(n_times, n_total)``
        for interleaved channels.
    wavelengths : np.ndarray
        Wavelengths in nm, shape ``(n_wl,)``.
    d : np.ndarray or None
        Source–detector distances in cm, shape ``(n_sd_pairs,)``. If None,
        defaults to 3.0 cm for all pairs.
    dpf : np.ndarray or None
        DPF per wavelength. Estimated via Scholkmann-Wolf if None.

    Returns
    -------
    hbo : np.ndarray  —  Δ[HbO] in µM, shape ``(n_times, n_sd_pairs)``
    hbr : np.ndarray  —  Δ[HbR] in µM, shape ``(n_times, n_sd_pairs)``
    """
    od = np.asarray(od, dtype=np.float64)
    wavelengths = np.asarray(wavelengths, dtype=np.float64)
    n_wl = len(wavelengths)

    # Normalise shape to (n_times, n_wl, n_sd)
    if od.ndim == 3:
        n_times, n_wl_in, n_sd = od.shape
        if n_wl_in != n_wl:
            raise ValueError(f"od shape[1]={n_wl_in} != n_wavelengths={n_wl}")
    elif od.ndim == 2:
        n_times, n_total = od.shape
        if n_total % n_wl != 0:
            raise ValueError(f"od channels {n_total} not divisible by n_wl {n_wl}")
        n_sd = n_total // n_wl
        od = od.reshape(n_times, n_wl, n_sd)
    else:
        raise ValueError(f"od must be 2-D or 3-D, got {od.shape}")

    if d is None:
        d = np.full(n_sd, 3.0, dtype=np.float64)
    else:
        d = np.asarray(d, dtype=np.float64)
        if d.shape != (n_sd,):
            raise ValueError(f"d must have shape ({n_sd},), got {d.shape}")

    # Extinction matrix + DPF
    E = extinction_matrix(wavelengths)
    if dpf is None:
        dpf = np.array([estimate_dpf(float(wl)) for wl in wavelengths])
    else:
        dpf = np.asarray(dpf, dtype=np.float64)

    # Scale: ΔOD_scaled = ΔOD / (d * DPF)
    d_exp = d.reshape(1, 1, n_sd)
    dpf_exp = dpf.reshape(1, n_wl, 1)
    scale = np.maximum(d_exp * dpf_exp, 1e-12)
    od_scaled = od / scale

    # Batch solve: pinv(E) @ od_scaled
    E_pinv = np.linalg.pinv(E)
    od_flat = od_scaled.transpose(1, 0, 2).reshape(n_wl, -1)
    conc_flat = E_pinv @ od_flat
    conc = conc_flat.reshape(2, n_times, n_sd).transpose(1, 2, 0)

    return conc[:, :, 0], conc[:, :, 1]


def compute_hbo_hbr(
    intensity: np.ndarray,
    wavelengths: np.ndarray,
    d: np.ndarray | None = None,
    *,
    dpf: np.ndarray | None = None,
    baseline: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """End-to-end pipeline: intensity → HbO/HbR concentration changes.

    Chains :func:`optical_density` → :func:`modified_beer_lambert`.

    Parameters
    ----------
    intensity : np.ndarray
        Raw intensity, shape ``(n_times, n_wl, n_sd)`` or interleaved ``(n_times, n_total)``.
    wavelengths : np.ndarray — shape ``(n_wl,)``.
    d : np.ndarray or None — S-D distances, shape ``(n_sd,)``. Defaults to 3.0 cm.
    dpf : np.ndarray or None
    baseline : np.ndarray or None

    Returns
    -------
    hbo, hbr : np.ndarray — each shape ``(n_times, n_sd)`` in µM.
    """
    od = optical_density(intensity, baseline=baseline)
    return modified_beer_lambert(od, wavelengths, d, dpf=dpf)
