"""Tests for PBM (photobiomodulation) metrics."""

import pytest


class TestPBMDose:
    """Tests for compute_pbm_dose()."""

    def test_import(self) -> None:
        from nlcore import compute_pbm_dose

        assert callable(compute_pbm_dose)

    def test_cw_dose_calculation_hamblin_2016(self) -> None:
        """Dose = (power/1000) * duration / area. (Hamblin 2016 Verification)"""
        from nlcore.physiology.pbm import compute_pbm_dose

        dose = compute_pbm_dose(power_mw=100, area_cm2=1.0, duration_s=60)
        # 100 mW = 0.1 W, 0.1 W * 60 s / 1 cm² = 6 J/cm²
        assert dose == pytest.approx(6.0)


class TestPBMFluence:
    """Tests for compute_pbm_fluence()."""

    def test_import(self) -> None:
        from nlcore import compute_pbm_fluence

        assert callable(compute_pbm_fluence)

    def test_fluence_calculation(self) -> None:
        from nlcore.physiology.pbm import compute_pbm_fluence

        fluence = compute_pbm_fluence(power_mw=200, area_cm2=2.0)
        assert fluence == pytest.approx(100.0)  # 200/2 = 100 mW/cm²


class TestPBMMetrics:
    """Tests for pbm_metrics()."""

    def test_import(self) -> None:
        from nlcore import pbm_metrics

        assert callable(pbm_metrics)

    def test_pbm_metrics_dose_calculation(self) -> None:
        """Verify dose is correctly wired into pbm_metrics when power/area are provided."""
        import numpy as np
        from nlcore.physiology.pbm import pbm_metrics

        # Dummy data
        fs = 10.0
        n_times = 2000
        hbo = np.zeros((n_times, 2))
        hbr = np.zeros((n_times, 2))
        
        # Test 1: No power/area given
        metrics1 = pbm_metrics(hbo, hbr, fs, response_window=(0.0, 10.0))
        assert metrics1["mean_dose"] == 0.0

        # Test 2: Power and area given, duration inferred from response window
        metrics2 = pbm_metrics(
            hbo, hbr, fs, 
            response_window=(0.0, 60.0),
            power_mw=100.0, 
            area_cm2=1.0
        )
        # Dose = (100 mW / 1000) * 60 s / 1.0 cm2 = 6.0 J/cm2
        assert metrics2["mean_dose"] == pytest.approx(6.0)

        # Test 3: Explicit dose duration
        metrics3 = pbm_metrics(
            hbo, hbr, fs, 
            response_window=(0.0, 60.0),
            power_mw=100.0, 
            area_cm2=1.0,
            dose_duration_s=120.0
        )
        # Dose = (100 mW / 1000) * 120 s / 1.0 cm2 = 12.0 J/cm2
        assert metrics3["mean_dose"] == pytest.approx(12.0)

    def test_pbm_metrics_recovery_rate(self) -> None:
        """Verify post-peak recovery rate is fitted correctly."""
        import numpy as np
        from nlcore.physiology.pbm import pbm_metrics

        fs = 10.0
        n_times = 100
        
        # Create a synthetic signal with a known decay rate
        # Let's say baseline is 0 for the first 20 samples, 
        # then it jumps to peak at t=20, and decays linearly.
        hbo = np.zeros((n_times, 1))
        
        # Baseline (t=0 to 2s, idx 0 to 20) is 0.0
        # Peak at idx 20 is 10.0
        # Recovery (decay) from idx 20 to 100: decay rate of 0.5 µM/s.
        # So value drops by 0.5 for every 1 second (10 samples).
        hbo[20] = 10.0
        for i in range(21, n_times):
            dt = (i - 20) / fs
            hbo[i] = 10.0 - (0.5 * dt)
            
        hbr = np.zeros((n_times, 1))
        
        # Use full window to ensure no clipping
        metrics = pbm_metrics(
            hbo, hbr, fs,
            stimulus_onset=np.array([0]),
            baseline_window=(0.0, 1.0),
            response_window=(0.0, 10.0)
        )
        
        assert metrics["recovery_rate"] == pytest.approx(0.5, abs=1e-5)
