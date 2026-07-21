# 🧠 NeuroLumina Core (`nlcore`)

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/matollaS/Project-Lumina/actions"><img src="https://github.com/matollaS/Project-Lumina/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
</p>

<p align="center">
  <strong>The open-source engine powering the next generation of optical brain monitoring.</strong>
</p>

---

**`nlcore`** is the open-core foundation of [NeuroLumina](https://neurolumina.ai) — a
production-grade Python library that turns raw HD-fNIRS and PBM signals into
actionable brain-state intelligence.

Designed from the ground up to be **SNIRF v1.0 compliant** and **MNE-Python
compatible**, `nlcore` slots directly into existing neuroimaging workflows while
also serving as the data-ingestion layer for NeuroLumina's premium deep-learning
models and dashboards.

---

## Why nlcore?

| Capability | What you get |
|---|---|
| **SNIRF-native I/O** | Read/write `.snirf` files (HDF5). Full probe geometry, stim markers, metadata. |
| **Chromophore conversion** | Modified Beer-Lambert law with built-in extinction coefficients (690–850 nm), DPF estimation via Scholkmann-Wolf, and batch pseudo-inverse solving. |
| **MNE-ready** | All outputs are numpy arrays. Convert to `mne.io.Raw` in one call. |
| **Preprocessing** | Motion artifact detection + correction (spline, PCA, wavelet). Zero-phase bandpass & notch filtering. |
| **PBM metrics** | Dose (J/cm²), fluence rate (mW/cm²), evoked haemodynamic response. |
| **Apache 2.0** | Free forever. Premium features (DL models, dashboards, API) live on the NeuroLumina cloud. |

---

## Installation

```bash
git clone https://github.com/matollaS/Project-Lumina.git
cd Project-Lumina
pip install -e ".[dev]"
```

**Requirements:** Python ≥ 3.10, numpy, scipy, h5py. MNE ≥ 1.5 is optional.

---

## Quick Start

### Load a SNIRF file and convert to HbO/HbR

```python
import nlcore

# Load data from a SNIRF file
ts, time, meta = nlcore.load_snirf("recording.snirf")
print(f"Shape: {ts.shape}, fs = {meta['fs']:.1f} Hz")
print(f"Wavelengths: {meta['wavelengths']}")

# Convert raw intensity → HbO/HbR (µM)
hbo, hbr = nlcore.compute_hbo_hbr(
    ts,
    wavelengths=meta["wavelengths"],
    d=meta.get("distances"),
)
print(f"HbO range: [{hbo.min():+.3f}, {hbo.max():+.3f}] µM")
print(f"HbR range: [{hbr.min():+.3f}, {hbr.max():+.3f}] µM")
```

### Write processed data back to SNIRF

```python
nlcore.save_snirf(
    "processed.snirf",
    ts=hbo,            # (n_times, n_channels)
    time=time,
    meta={
        "SubjectID": "sub-01",
        "wavelengths": meta["wavelengths"],
        "sourceLabels": meta["sourceLabels"],
        "detectorLabels": meta["detectorLabels"],
    },
)
```

### Chromophore conversion step-by-step

```python
from nlcore.physiology.chromophore import (
    optical_density, modified_beer_lambert,
    extinction_matrix, estimate_dpf,
)

# Step 1: Intensity → optical density
od = optical_density(ts)  # auto-baseline = temporal mean

# Step 2: OD → HbO/HbR via modified Beer-Lambert
wavelengths = meta["wavelengths"]
dpf = [estimate_dpf(wl) for wl in wavelengths]
hbo, hbr = modified_beer_lambert(od, wavelengths, dpf=dpf)

# Inspect the extinction matrix
E = extinction_matrix(wavelengths)
print(E)  # [[ε_HbO(λ1), ε_HbR(λ1)], [ε_HbO(λ2), ε_HbR(λ2)]]
```

---

## Package Structure

```
Project-Lumina/
├── nlcore/
│   ├── __init__.py              # Top-level API (16 public functions)
│   ├── io/
│   │   └── snirf.py             # SnirfFile, load_snirf, save_snirf
│   ├── preprocessing/
│   │   ├── filtering.py         # bandpass_filter, notch_filter
│   │   └── motion.py            # detect + correct (spline, PCA, wavelet)
│   ├── physiology/
│   │   ├── chromophore.py       # optical_density, mBLL, compute_hbo_hbr
│   │   └── pbm.py               # compute_pbm_dose, fluence, pbm_metrics
│   └── utils/
│       └── mne_compat.py        # SourceDetectorMap, raw_to_mne, mne_to_raw
├── tests/                       # pytest (33 tests)\r
│   └── data/                    # test fixtures (.snirf, etc.)
├── docs/                        # Sphinx docs
├── examples/
├── pyproject.toml
└── README.md
```

---

## API Reference

| Function | Module | Description |
|---|---|---|
| `load_snirf(fname)` | `nlcore.io` | Read SNIRF → `(ts, time, meta)` |
| `save_snirf(fname, ts, t, meta)` | `nlcore.io` | Write SNIRF v1.0 |
| `optical_density(intensity)` | `nlcore.physiology` | Intensity → ΔOD |
| `modified_beer_lambert(od, wl, d)` | `nlcore.physiology` | ΔOD → HbO/HbR (µM) |
| `compute_hbo_hbr(intensity, wl, d)` | `nlcore.physiology` | End-to-end pipeline |
| `extinction_matrix(wavelengths)` | `nlcore.physiology` | Build ε matrix |
| `estimate_dpf(wavelength, age)` | `nlcore.physiology` | Scholkmann-Wolf DPF |
| `compute_pbm_dose(power, area, dur)` | `nlcore.physiology` | Dose (J/cm²) |
| `compute_pbm_fluence(power, area)` | `nlcore.physiology` | Fluence (mW/cm²) |
| `pbm_metrics(hbo, hbr, fs)` | `nlcore.physiology` | Haemodynamic response |
| `bandpass_filter(data, fs)` | `nlcore.preprocessing` | Zero-phase bandpass |
| `notch_filter(data, fs, freq)` | `nlcore.preprocessing` | Mains-noise notch |
| `detect_motion_artifacts(data, fs)` | `nlcore.preprocessing` | Flag artifacts |
| `correct_motion_spline(data, mask)` | `nlcore.preprocessing` | Spline repair |
| `correct_motion_pca(data, mask)` | `nlcore.preprocessing` | PCA repair |
| `correct_motion_wavelet(data, mask)` | `nlcore.preprocessing` | Wavelet repair |
| `raw_to_mne(...)` | `nlcore.utils` | numpy → MNE Raw |
| `mne_to_raw(raw)` | `nlcore.utils` | MNE Raw → numpy |

---

## Open Core → Premium

`nlcore` is free forever. The [NeuroLumina Platform](https://neurolumina.ai) adds:

- **Pre-trained deep-learning models** (CNN / Bi-LSTM) for cognitive-load classification
- **Real-time inference API** (<100 ms latency)
- **Turnkey dashboards** for labs, clinics, and enterprise
- **On-premise deployment** — air-gapped, HIPAA-ready, white-label

---

## Contributing

```bash
git clone https://github.com/matollaS/Project-Lumina.git
cd Project-Lumina
pip install -e ".[dev]"
pytest   # 70+ tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## References

- Scholkmann, F., et al. (2010). *Physiol. Meas.*, 31(5), 649.
- Brigadoi, S., et al. (2014). *NeuroImage*, 85, 181–191.
- Delpy, D. T., et al. (1988). *Phys. Med. Biol.*, 33(12), 1433.
- Scholkmann, F., & Wolf, M. (2013). *J. Biomed. Opt.*, 18(10), 105004.
- Hamblin, M. R. (2016). *BBA Clin.*, 6, 113–124.

## Acknowledgements

- The sample fNIRS dataset (`sub-01_task-tapping_nirs.snirf`) included for testing is sourced from the public [rob-luke/BIDS-NIRS-Tapping](https://github.com/rob-luke/BIDS-NIRS-Tapping) repository, a standard community reference dataset.

## License

Apache 2.0 © 2026 NeuroLumina Contributors.
