#!/usr/bin/env python3
"""
example_basic_pipeline.py — Full nlcore pipeline with synthetic data.

Usage:  python example_basic_pipeline.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

import nlcore


def main() -> None:
    # ── 1. Generate synthetic data ──────────────────────────────────
    print("[1/5] Generating synthetic fNIRS data …")
    n_times, fs = 6000, 10.0
    n_sd, n_wl = 8, 2
    wavelengths = np.array([760.0, 850.0])
    distances = np.full(n_sd, 3.0)  # 3 cm
    t = np.arange(n_times) / fs

    rng = np.random.default_rng(42)
    ts = np.zeros((n_times, n_wl, n_sd))
    for wl in range(n_wl):
        for ch in range(n_sd):
            ts[:, wl, ch] = 0.3 * np.sin(
                2 * np.pi * 0.08 * t + rng.uniform(0, 2 * np.pi)
            ) + 0.02 * np.cumsum(rng.normal(0, 0.01, n_times))

    # Insert a motion spike
    spike = slice(int(300 * fs), int(300.5 * fs))
    ts[spike] += rng.normal(2.0, 0.5, ts[spike].shape)

    meta = {
        "SubjectID": "demo-001",
        "wavelengths": wavelengths,
        "sourceLabels": [f"S{i + 1}" for i in range(n_sd)],
        "detectorLabels": [f"D{i + 1}" for i in range(n_sd)],
        "distances": distances,
    }
    print(f"   Shape: {ts.shape}  |  fs = {fs} Hz  |  λ = {wavelengths.tolist()}")

    # ── 2. Save to SNIRF and reload ─────────────────────────────────
    print("[2/5] Writing and round-tripping via SNIRF …")
    ts_flat = ts.reshape(n_times, n_wl * n_sd)
    t_1d = np.arange(n_times) / fs

    with tempfile.NamedTemporaryFile(suffix=".snirf", delete=False) as tmp:
        fname = tmp.name
    try:
        nlcore.save_snirf(fname, ts_flat, t_1d, meta)
        ts_loaded, time_loaded, meta_loaded = nlcore.load_snirf(fname)
        # Reshape back to 3-D
        ts_3d = ts_loaded.reshape(n_times, n_wl, n_sd)
        assert np.allclose(ts_flat, ts_loaded, atol=1e-6)
        print("   Round-trip OK ✓")
    finally:
        Path(fname).unlink()

    # ── 3. Chromophore conversion ───────────────────────────────────
    print("[3/5] Converting intensity → HbO/HbR …")
    hbo, hbr = nlcore.compute_hbo_hbr(ts_3d, wavelengths, distances)
    print(f"   HbO range: [{hbo.min():+.3f}, {hbo.max():+.3f}] µM")
    print(f"   HbR range: [{hbr.min():+.3f}, {hbr.max():+.3f}] µM")

    # ── 4. Extinction matrix & DPF ──────────────────────────────────
    print("[4/5] Extinction matrix & DPF estimation …")
    from nlcore.physiology.chromophore import estimate_dpf, extinction_matrix

    E = extinction_matrix(wavelengths)
    print(f"   E (ε_HbO, ε_HbR):\n{E}")

    for wl in wavelengths:
        print(f"   DPF({wl:.0f} nm, age=25) = {estimate_dpf(float(wl)):.2f}")

    # ── 5. Simulated PBM metrics ────────────────────────────────────
    print("[5/5] PBM metrics (simulated) …")
    dose = nlcore.compute_pbm_dose(power_mw=100, area_cm2=1.0, duration_s=60)
    fluence = nlcore.compute_pbm_fluence(power_mw=100, area_cm2=1.0)
    print(f"   Dose: {dose} J/cm²")
    print(f"   Fluence: {fluence} mW/cm²")

    print("\n✓ Pipeline complete!")


if __name__ == "__main__":
    main()
