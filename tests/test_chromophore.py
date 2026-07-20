"""Tests for chromophore conversion (modified Beer-Lambert)."""

import numpy as np
import pytest


class TestOpticalDensity:
    def test_import(self) -> None:
        from nlcore import optical_density
        assert callable(optical_density)

    def test_identity_for_unity_ratio(self) -> None:
        from nlcore.physiology.chromophore import optical_density
        I = np.ones((100, 4))
        od = optical_density(I, baseline=np.ones(4))
        assert od.shape == I.shape
        assert np.allclose(od, 0.0, atol=1e-10)

    def test_halved_intensity(self) -> None:
        from nlcore.physiology.chromophore import optical_density
        I = np.full((10, 1), 0.5)
        od = optical_density(I, baseline=np.array([1.0]))
        assert np.allclose(od, -np.log10(0.5), atol=1e-6)

    def test_auto_baseline(self) -> None:
        from nlcore.physiology.chromophore import optical_density
        rng = np.random.default_rng(42)
        I = rng.normal(100, 5, (200, 3))
        od = optical_density(I)
        assert od.shape == I.shape
        assert np.allclose(np.mean(od, axis=0), 0.0, atol=0.1)


class TestModifiedBeerLambert:
    def test_import(self) -> None:
        from nlcore import modified_beer_lambert
        assert callable(modified_beer_lambert)

    def test_zero_od(self) -> None:
        from nlcore.physiology.chromophore import modified_beer_lambert
        od = np.zeros((10, 2, 2))
        hbo, hbr = modified_beer_lambert(od, np.array([760.0, 850.0]), np.array([3.0, 3.0]))
        assert np.allclose(hbo, 0.0) and np.allclose(hbr, 0.0)

    def test_2d_interleaved(self) -> None:
        from nlcore.physiology.chromophore import modified_beer_lambert
        od = np.zeros((5, 6))  # 2 wl × 3 sd
        hbo, hbr = modified_beer_lambert(od, np.array([760.0, 850.0]), np.array([3.0, 3.0, 3.0]))
        assert hbo.shape == (5, 3) and hbr.shape == (5, 3)

    def test_known_signal_recovery(self) -> None:
        """Inject known HbO/HbR and verify recovery via forward model."""
        from nlcore.physiology.chromophore import modified_beer_lambert, extinction_matrix, estimate_dpf

        wavelengths = np.array([760.0, 850.0])
        d = np.array([3.0])
        E = extinction_matrix(wavelengths)
        dpf = np.array([estimate_dpf(float(wl)) for wl in wavelengths])

        delta_c = np.array([1.0, -0.5])  # [HbO, HbR]
        delta_od = E @ delta_c * d[0] * dpf

        n_times = 10
        od = np.tile(delta_od, (n_times, 1)).reshape(n_times, 2, 1)
        hbo, hbr = modified_beer_lambert(od, wavelengths, d, dpf=dpf)
        assert np.allclose(hbo[:, 0], 1.0, atol=1e-6)
        assert np.allclose(hbr[:, 0], -0.5, atol=1e-6)

    def test_delpy_1988_mbll(self) -> None:
        """Verify Delpy 1988 MBLL calculation explicitly: ΔC = ΔA / (ε * d * DPF)."""
        from nlcore.physiology.chromophore import modified_beer_lambert, extinction_matrix
        wl = np.array([850.0]) # single wavelength test (mock, to verify scale factor)
        d = np.array([2.5])
        dpf = np.array([6.0])
        od = np.array([[[1.5]]]) # shape (1 time, 1 wl, 1 sd)
        
        # Manually compute single-wavelength pseudo-inverse for sanity check
        # E shape (1, 2). E_pinv shape (2, 1). 
        # C = E_pinv * (OD / (d * dpf))
        hbo, hbr = modified_beer_lambert(od, wl, d, dpf=dpf)
        
        from numpy.linalg import pinv
        E = extinction_matrix(wl)
        E_pinv = pinv(E)
        scaled_od = 1.5 / (2.5 * 6.0)
        expected_hbo = E_pinv[0, 0] * scaled_od
        expected_hbr = E_pinv[1, 0] * scaled_od
        
        assert np.allclose(hbo[0, 0], expected_hbo, atol=1e-6)
        assert np.allclose(hbr[0, 0], expected_hbr, atol=1e-6)


class TestComputeHbOHbR:
    def test_import(self) -> None:
        from nlcore import compute_hbo_hbr
        assert callable(compute_hbo_hbr)

    def test_end_to_end(self) -> None:
        from nlcore.physiology.chromophore import compute_hbo_hbr
        intensity = np.ones((20, 2, 2))
        hbo, hbr = compute_hbo_hbr(intensity, np.array([760.0, 850.0]), np.array([3.0, 3.0]))
        assert hbo.shape == (20, 2)
        assert np.allclose(hbo, 0.0, atol=1e-6)
        assert np.allclose(hbr, 0.0, atol=1e-6)


class TestExtinctionMatrix:
    def test_shape(self) -> None:
        from nlcore.physiology.chromophore import extinction_matrix
        E = extinction_matrix(np.array([760.0, 850.0]))
        assert E.shape == (2, 2)
        assert np.all(E > 0)

    def test_interpolation(self) -> None:
        from nlcore.physiology.chromophore import extinction_matrix
        E = extinction_matrix(np.array([780.0]))
        assert E.shape == (1, 2)
        # 780 nm should be between 760 and 830 values
        E760 = extinction_matrix(np.array([760.0]))
        E830 = extinction_matrix(np.array([830.0]))
        for j in (0, 1):
            assert E760[0, j] <= E[0, j] <= E830[0, j] or E830[0, j] <= E[0, j] <= E760[0, j]


class TestEstimateDPF:
    def test_plausible(self) -> None:
        from nlcore.physiology.chromophore import estimate_dpf
        dpf = estimate_dpf(760.0, age=25)
        assert 3.0 < dpf < 10.0

    def test_age_monotonic(self) -> None:
        from nlcore.physiology.chromophore import estimate_dpf
        assert estimate_dpf(760.0, age=70) > estimate_dpf(760.0, age=5)

    def test_scholkmann_wolf_exact(self) -> None:
        """Verify DPF exactly matches Scholkmann & Wolf 2013 equation."""
        from nlcore.physiology.chromophore import estimate_dpf
        wl = 760.0
        age = 30.0
        # Equation from Scholkmann & Wolf (2013)
        expected_dpf = (
            223.3 
            + 0.05624 * (age ** 0.8493) 
            - 5.723e-7 * (wl ** 3) 
            + 0.001245 * (wl ** 2) 
            - 0.9025 * wl
        )
        # Apply limits max(1.0, min(dpf, 15.0))
        expected_dpf = max(1.0, min(expected_dpf, 15.0))
        assert estimate_dpf(wl, age=age) == pytest.approx(expected_dpf)
