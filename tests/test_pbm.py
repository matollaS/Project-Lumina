"""Tests for PBM (photobiomodulation) metrics."""

import numpy as np
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
