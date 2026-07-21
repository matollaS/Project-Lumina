"""Tests for SNIRF file I/O."""

import tempfile
from pathlib import Path

import numpy as np
import pytest


class TestLoadSnirf:
    def test_import(self) -> None:
        from nlcore import load_snirf

        assert callable(load_snirf)

    def test_snirf_file_class_exists(self) -> None:
        from nlcore.io.snirf import SnirfFile

        assert SnirfFile is not None

    def test_roundtrip(self) -> None:
        """Create a minimal SNIRF file and read it back."""
        from nlcore import load_snirf, save_snirf

        n_times, n_chans = 100, 8
        rng = np.random.default_rng(42)
        ts_orig = rng.normal(0, 0.1, (n_times, n_chans))
        time_orig = np.arange(n_times, dtype=np.float64) / 10.0
        meta = {
            "SubjectID": "test-001",
            "wavelengths": np.array([760.0, 850.0]),
            "sourceLabels": ["S1", "S2"],
            "detectorLabels": ["D1", "D2"],
        }

        with tempfile.NamedTemporaryFile(suffix=".snirf", delete=False) as tmp:
            fname = tmp.name
        try:
            save_snirf(fname, ts_orig, time_orig, meta)
            ts, t, m = load_snirf(fname)
            assert ts.shape == (n_times, n_chans)
            assert np.allclose(ts_orig, ts, atol=1e-6)
            assert np.allclose(time_orig, t, atol=1e-6)
            assert m["SubjectID"] == "test-001"
            assert np.allclose(m["wavelengths"], [760.0, 850.0])
            assert m["sourceLabels"] == ["S1", "S2"]
            assert "fs" in m
            assert m["fs"] == pytest.approx(10.0)
        finally:
            Path(fname).unlink(missing_ok=True)

    def test_roundtrip_with_stim_and_aux(self) -> None:
        from nlcore import load_snirf, save_snirf

        n_times = 30
        ts = np.zeros((n_times, 2))
        time = np.arange(n_times) / 10.0
        meta = {
            "SubjectID": "stim-test",
            "wavelengths": np.array([760.0]),
            "sourceLabels": ["S1"],
            "detectorLabels": ["D1"],
        }
        stim = np.array(
            [(5.0, 2.0, 1, 1.0)],
            dtype=[("onset", "f8"), ("duration", "f8"), ("value", "i4"), ("amplitude", "f8")],
        )
        aux = np.random.default_rng(7).normal(0, 1, (n_times, 1))

        with tempfile.NamedTemporaryFile(suffix=".snirf", delete=False) as tmp:
            fname = tmp.name
        try:
            save_snirf(fname, ts, time, meta, stim=stim, aux=aux)
            ts2, t2, m2 = load_snirf(fname)
            assert ts2.shape == ts.shape
        finally:
            Path(fname).unlink(missing_ok=True)


class TestSaveSnirf:
    def test_import(self) -> None:
        from nlcore import save_snirf

        assert callable(save_snirf)

    def test_defaults(self) -> None:
        """Minimal metadata should still work."""
        from nlcore import load_snirf, save_snirf

        ts = np.ones((5, 1))
        time = np.arange(5.0)
        meta = {"wavelengths": np.array([760.0]), "sourceLabels": ["S1"], "detectorLabels": ["D1"]}

        with tempfile.NamedTemporaryFile(suffix=".snirf", delete=False) as tmp:
            fname = tmp.name
        try:
            save_snirf(fname, ts, time, meta)
            ts2, t2, m2 = load_snirf(fname)
            assert m2["SubjectID"] == "unknown"
            assert np.allclose(ts2, ts)
        finally:
            Path(fname).unlink(missing_ok=True)
