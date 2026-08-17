# 🧠 NeuroLumina Core (`nlcore`)

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/matollaS/Project-Lumina/actions"><img src="https://github.com/matollaS/Project-Lumina/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
</p>

<p align="center">
  <strong>Open optical-brain signal processing for HD-fNIRS and PBM-response research.</strong>
</p>

---

**`nlcore`** is the open-core foundation of Project Lumina / NeuroLumina: a Python
library for turning raw fNIRS and photobiomodulation (PBM) experiment data into
reproducible physiological features.

The public core is deliberately **measurement-first**. It is SNIRF v1.0 compliant,
MNE-Python compatible, and currently focuses on optical data ingestion,
preprocessing, HbO/HbR estimation, PBM dosimetry utilities, and haemodynamic
response analysis.

> **Research status** — `nlcore` is research software, not a medical device. It
> does not diagnose disease, recommend PBM treatment, or provide a clinically
> validated closed-loop stimulator.

---

## Scientific architecture

Project Lumina separates three layers that must be validated independently:

1. **Measurement** — what did the instruments reliably observe?
2. **Inference** — what latent physiological/cognitive state is supported by the measurements?
3. **Intervention** — can a controlled input causally and safely alter the target state?

The public `nlcore` repository currently lives primarily at **Layer 1**.
State inference and closed-loop intervention remain research-roadmap capabilities
that require prospective validation, explicit uncertainty, dose constraints,
sham/control conditions, and appropriate ethics/regulatory oversight.

A future closed loop is conceptually:

```text
sense -> estimate -> decide -> stimulate -> verify -> repeat
```

The frequency of sensing or computation must not be confused with the biological
response time of the full closed loop.

See:

- [`docs/research_scope.rst`](docs/research_scope.rst) — validation ladder and claim boundaries
- [`docs/pbm_evidence.rst`](docs/pbm_evidence.rst) — condition-specific PBM evidence map (Aug 2026)

---

## Current capabilities

| Capability | What you get |
|---|---|
| **SNIRF-native I/O** | Read/write `.snirf` files (HDF5), including probe geometry, stim markers and metadata. |
| **Chromophore conversion** | Modified Beer-Lambert HbO/HbR estimation with wavelength interpolation and DPF estimation. |
| **MNE-ready** | NumPy outputs with conversion helpers for `mne.io.Raw`. |
| **Preprocessing** | Bandpass/notch filtering plus motion-artifact detection and spline/PCA/wavelet correction. |
| **PBM experiment metrics** | Dose (J/cm²), fluence rate (mW/cm²), and evoked haemodynamic-response utilities. |
| **Apache 2.0** | Open-source core for reproducible research workflows. |

### Important boundary: oxCCO

The current standard chromophore path estimates **HbO/HbR**. It does **not**
currently claim validated measurement of oxidised cytochrome-c-oxidase (oxCCO).
Robust oxCCO reconstruction is a separate broadband/hyperspectral NIRS hardware
and inverse-problem programme because the CCO signal is weaker than haemoglobin
and spectrally overlaps with it.

That distinction is central to the Lumina roadmap: metabolic sensing should be
validated as its own instrumentation stack before being used as a closed-loop
biomarker.

---

## Installation

```bash
git clone https://github.com/matollaS/Project-Lumina.git
cd Project-Lumina
pip install -e ".[dev]"
```

**Requirements:** Python ≥ 3.10, numpy, scipy, h5py. MNE ≥ 1.5 is optional.

---

## Quick start

### Load a SNIRF file and convert to HbO/HbR

```python
import nlcore

# Load data from a SNIRF file
ts, time, meta = nlcore.load_snirf("recording.snirf")
print(f"Shape: {ts.shape}, fs = {meta['fs']:.1f} Hz")
print(f"Wavelengths: {meta['wavelengths']}")

# Convert raw intensity -> HbO/HbR (µM)
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
    ts=hbo,
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
    optical_density,
    modified_beer_lambert,
    extinction_matrix,
    estimate_dpf,
)

od = optical_density(ts)
wavelengths = meta["wavelengths"]
dpf = [estimate_dpf(wl) for wl in wavelengths]
hbo, hbr = modified_beer_lambert(od, wavelengths, dpf=dpf)

E = extinction_matrix(wavelengths)
print(E)
```

---

## PBM evidence: current translational position

The repository uses an explicit evidence ladder rather than treating all PBM
findings as clinically interchangeable.

| Context | Current evidence interpretation |
|---|---|
| **Peripheral PBM in pediatric cerebral palsy** | Early clinical / preliminary; a 2025 pilot RCT found no significant between-group differences. |
| **Transcranial PBM in pediatric cerebral palsy** | Pre-preliminary; experimental only. |
| **tPBM for epilepsy** | Promising animal evidence; first open-label human pilot is recruiting, with no posted results as of Aug 2026. |
| **tPBM for TBI** | Early human evidence with small heterogeneous studies; promising but not established standard care. |
| **Chronic post-meningitis brain injury** | Direct PBM efficacy not established; TBI/stroke literature should generate hypotheses, not be treated as a clinical proxy. |

The engineering implication is more useful than the marketing shortcut:

```text
measure response -> standardise dosimetry -> model individual response
-> prospectively validate -> evaluate safety-gated closed-loop intervention
```

Full sources and evidence notes are in [`docs/pbm_evidence.rst`](docs/pbm_evidence.rst).

---

## Package structure

```text
Project-Lumina/
├── nlcore/
│   ├── __init__.py
│   ├── io/
│   │   └── snirf.py
│   ├── preprocessing/
│   │   ├── filtering.py
│   │   └── motion.py
│   ├── physiology/
│   │   ├── chromophore.py
│   │   └── pbm.py
│   └── utils/
│       └── mne_compat.py
├── tests/
├── docs/
│   ├── research_scope.rst
│   └── pbm_evidence.rst
├── examples/
├── pyproject.toml
└── README.md
```

---

## API reference

| Function | Module | Description |
|---|---|---|
| `load_snirf(fname)` | `nlcore.io` | Read SNIRF → `(ts, time, meta)` |
| `save_snirf(fname, ts, t, meta)` | `nlcore.io` | Write SNIRF v1.0 |
| `optical_density(intensity)` | `nlcore.physiology` | Intensity → ΔOD |
| `modified_beer_lambert(od, wl, d)` | `nlcore.physiology` | ΔOD → HbO/HbR (µM) |
| `compute_hbo_hbr(intensity, wl, d)` | `nlcore.physiology` | End-to-end HbO/HbR pipeline |
| `extinction_matrix(wavelengths)` | `nlcore.physiology` | Build extinction matrix |
| `estimate_dpf(wavelength, age)` | `nlcore.physiology` | DPF estimate |
| `compute_pbm_dose(power, area, dur)` | `nlcore.physiology` | Dose (J/cm²) |
| `compute_pbm_fluence(power, area)` | `nlcore.physiology` | Fluence rate (mW/cm²) |
| `pbm_metrics(hbo, hbr, fs)` | `nlcore.physiology` | Haemodynamic response metrics |
| `bandpass_filter(data, fs)` | `nlcore.preprocessing` | Zero-phase bandpass |
| `notch_filter(data, fs, freq)` | `nlcore.preprocessing` | Mains-noise notch |
| `detect_motion_artifacts(data, fs)` | `nlcore.preprocessing` | Flag artifacts |
| `correct_motion_spline(data, mask)` | `nlcore.preprocessing` | Spline repair |
| `correct_motion_pca(data, mask)` | `nlcore.preprocessing` | PCA repair |
| `correct_motion_wavelet(data, mask)` | `nlcore.preprocessing` | Wavelet repair |
| `raw_to_mne(...)` | `nlcore.utils` | NumPy → MNE Raw |
| `mne_to_raw(raw)` | `nlcore.utils` | MNE Raw → NumPy |

---

## Research roadmap

The long-term Project Lumina platform can build upward from the open core while
keeping each claim independently testable:

- **Multimodal measurement** — fNIRS + motion/IMU + cardiac/respiratory signals;
  EEG/EOG where the paradigm requires electrophysiology.
- **Metabolic sensing** — dedicated broadband/hyperspectral NIRS programme for
  oxCCO with phantom and human validation.
- **State modelling** — prospective latent-state and cognitive-load models with
  calibration, uncertainty and out-of-distribution testing.
- **PBM response modelling** — complete dosimetry capture and individual
  dose-response estimation.
- **Closed-loop research** — intervention only after validated sensing,
  prospective state estimation, explicit safety constraints and sham-controlled
  studies.

Non-clinical human-state research (for example sleep, task load, meditation or
absorption paradigms) can use the same measurement/inference separation without
being presented as a medical indication.

---

## Contributing

```bash
git clone https://github.com/matollaS/Project-Lumina.git
cd Project-Lumina
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Selected references

### Optical methods

- Delpy DT, et al. *Phys Med Biol.* 1988;33(12):1433.
- Scholkmann F, et al. *Physiol Meas.* 2010;31(5):649.
- Scholkmann F, Wolf M. *J Biomed Opt.* 2013;18(10):105004.
- Ward R, et al. *Recent near-infrared approaches to cytochrome-c-oxidase monitoring.* *Phys Med Biol.* 2026. PMID 42013903.
- Bale G, et al. *Review of measurements and imaging of cytochrome-c-oxidase in humans using NIRS: an update.* 2024. PMID 38223181.

### PBM translation

- Fernandes F, et al. *Devices used for photobiomodulation of the brain-a comprehensive and systematic review.* *J Neuroeng Rehabil.* 2024;21:53. PMID 38600582.
- Zeng J, et al. *Can transcranial photobiomodulation improve cognitive function in TBI patients?* *Front Psychol.* 2024;15:1378570. PMID 38952831.
- You J, et al. *Preventive effects of transcranial photobiomodulation on epileptogenesis in a kainic acid-induced rat epilepsy model.* *Exp Neurol.* 2025;383:115005. PMID 39419434.

---

## Acknowledgements

The sample fNIRS dataset (`sub-01_task-tapping_nirs.snirf`) included for testing
is sourced from the public `rob-luke/BIDS-NIRS-Tapping` repository, a community
reference dataset.

## License

Apache 2.0 © 2026 NeuroLumina Contributors.
