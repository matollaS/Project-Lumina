# Changelog

All notable changes to `nlcore` are documented in this file.

## [Unreleased]

### Added
- Added `IndividualDoseResponseModel`, the first explicit inference-layer model
  in the public core. It fits a global polynomial ridge dose-response model with
  optional covariates and regularized subject-specific residual adjustments for
  repeated observations.
- Added `ResponsePrediction` with approximate predictive uncertainty and an
  explicit flag showing whether subject-specific calibration was used.
- Added `extract_dose_response()` to make the handoff from PBM measurement
  metrics to inference explicit.
- Added response-model API docs, usage guidance, and synthetic tests.

### Documentation
- Reframed the public core as a measurement-first research library and separated
  **measurement**, **inference**, and **intervention** claims.
- Added an explicit validation ladder for future state inference and closed-loop
  PBM research.
- Added `docs/pbm_evidence.rst` with August 2026 evidence tiers for pediatric
  cerebral palsy, epilepsy, traumatic brain injury, and post-meningitis research.
- Clarified that the current HbO/HbR pipeline does not constitute validated
  oxidised cytochrome-c-oxidase (oxCCO) measurement; oxCCO is treated as a
  separate broadband/hyperspectral NIRS validation programme.
- Added a research-use statement: `nlcore` is not a medical device and does not
  diagnose disease or recommend PBM treatment.
- Documented the response model as an associative research tool rather than a
  causal estimator or dose-prescribing system.

## [0.1.0] — 2026-07-16

### Added
- **SNIRF I/O** — `SnirfFile` class, `load_snirf()`, `save_snirf()` with full
  HDF5 read/write, probe geometry, stim markers, metadata. NumPy 2.x compatible.
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
