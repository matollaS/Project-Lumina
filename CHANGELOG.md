# Changelog

All notable changes to `nlcore` are documented in this file.

## [0.1.0] — 2026-07-16

### Added
- **SNIRF I/O** — `SnirfFile` class, `load_snirf()`, `save_snirf()` with full
  HDF5 read/write, probe geometry, stim markers, metadata.  NumPy 2.x compatible.
- **Chromophore conversion** — `optical_density()`, `modified_beer_lambert()`,
  `compute_hbo_hbr()`, `extinction_matrix()` (with wavelength interpolation),
  `estimate_dpf()` (Scholkmann-Wolf 2013 model).
- **Preprocessing** — `bandpass_filter()` (zero-phase Butterworth),
  `notch_filter()` (zero-phase IIR notch), `detect_motion_artifacts()`,
  `correct_motion_spline()`, `correct_motion_pca()`, `correct_motion_wavelet()`.
- **PBM metrics** — `compute_pbm_dose()`, `compute_pbm_fluence()`,
  `pbm_metrics()` (haemodynamic response extraction).
- **MNE compatibility** — `SourceDetectorMap`, `raw_to_mne()`, `mne_to_raw()`.
- **Tooling** — `pyproject.toml`, `setup.py`, GitHub Actions CI, pytest suite
  (33 tests), Sphinx docs, example pipeline script, Apache 2.0 license.

[0.1.0]: https://github.com/matollaS/Project-Lumina/releases/tag/v0.1.0
