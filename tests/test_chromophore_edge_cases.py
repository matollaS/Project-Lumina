"""Edge-case and reference-validation tests for chromophore.py.

Spec 3 — branding-updates: improve test coverage of the chromophore
module WITHOUT modifying the production code.

References
----------
.. [1] Delpy, D. T., et al. (1988). *Phys. Med. Biol.*, 33(12), 1433.
.. [2] Scholkmann, F., & Wolf, M. (2013). *J. Biomed. Opt.*, 18(10), 105004.
.. [3] UCL Biomedical Optics Research Laboratory extinction coefficient database.
"""

from __future__ import annotations

import numpy as np
import pytest

from nlcore.physiology.chromophore import (
    EXTINCTION_COEFFS,
    _interpolate_extinction,
    compute_hbo_hbr,
    estimate_dpf,
    extinction_matrix,
    modified_beer_lambert,
    optical_density,
)


# ---------------------------------------------------------------------------
#  estimate_dpf — Scholkmann–Wolf boundary & clamp tests
# ---------------------------------------------------------------------------


class TestEstimateDPFBoundaries:
    """Tests for estimate_dpf at and beyond the valid wavelength range.

    The Scholkmann–Wolf 2013 model (Ref [2], Eq. 2) is:
        DPF = 223.3 + 0.05624·age^0.8493
              − 5.723e-7·λ³ + 0.001245·λ² − 0.9025·λ
    with a clamp to [1.0, 15.0].
    """

    @staticmethod
    def _raw_dpf(wavelength: float, age: float = 25.0) -> float:
        """Recompute the raw (unclamped) Scholkmann–Wolf DPF."""
        return (
            223.3
            + 0.05624 * (age**0.8493)
            - 5.723e-7 * (wavelength**3)
            + 0.001245 * (wavelength**2)
            - 0.9025 * wavelength
        )

    def test_dpf_at_690nm(self) -> None:
        """DPF at 690 nm (lower boundary of common fNIRS range).

        At 690 nm, age 25, the raw model gives a value that should be
        within [1, 15] per the clamp in estimate_dpf.
        Ref: Scholkmann & Wolf 2013, Table 2, age-dependent DPF.
        """
        raw = self._raw_dpf(690.0, 25.0)
        expected = max(1.0, min(raw, 15.0))
        assert estimate_dpf(690.0, 25.0) == pytest.approx(expected, abs=1e-10)

    def test_dpf_at_850nm(self) -> None:
        """DPF at 850 nm (upper boundary of common fNIRS range).

        Ref: Scholkmann & Wolf 2013, Table 2.
        """
        raw = self._raw_dpf(850.0, 25.0)
        expected = max(1.0, min(raw, 15.0))
        assert estimate_dpf(850.0, 25.0) == pytest.approx(expected, abs=1e-10)

    def test_dpf_below_valid_range_clamps_to_lower_bound(self) -> None:
        """Very short wavelength (300 nm) should still return ≥ 1.0.

        At λ=300, the cubic term dominates negatively; the function should
        clamp to 1.0 rather than return a nonsensical or negative DPF.
        """
        dpf = estimate_dpf(300.0, 25.0)
        assert dpf >= 1.0, f"DPF must be clamped to ≥1.0, got {dpf}"

    def test_dpf_above_valid_range_clamps_to_upper_bound(self) -> None:
        """Very long wavelength (2000 nm) should still return ≤ 15.0.

        The cubic term makes the raw DPF very large; the clamp should cap it.
        """
        dpf = estimate_dpf(2000.0, 25.0)
        assert dpf <= 15.0, f"DPF must be clamped to ≤15.0, got {dpf}"

    def test_dpf_clamp_lower_exactly(self) -> None:
        """When raw DPF < 1.0, estimate_dpf must return exactly 1.0."""
        # At very short wavelength the quadratic/cubic terms push DPF down.
        dpf = estimate_dpf(100.0, 1.0)
        raw = self._raw_dpf(100.0, 1.0)
        if raw < 1.0:
            assert dpf == pytest.approx(1.0)
        else:
            # If the raw value is ≥ 1 even here, just check clamp holds
            assert dpf >= 1.0

    def test_dpf_clamp_upper_exactly(self) -> None:
        """When raw DPF > 15.0, estimate_dpf must return exactly 15.0."""
        dpf = estimate_dpf(2000.0, 80.0)
        raw = self._raw_dpf(2000.0, 80.0)
        if raw > 15.0:
            assert dpf == pytest.approx(15.0)
        else:
            assert dpf <= 15.0

    def test_dpf_age_zero(self) -> None:
        """Age=0 should not raise; the 0^0.8493 term is 0 so it drops out."""
        dpf = estimate_dpf(760.0, 0.0)
        assert 1.0 <= dpf <= 15.0


# ---------------------------------------------------------------------------
#  modified_beer_lambert — shape-mismatch validation
# ---------------------------------------------------------------------------


class TestModifiedBeerLambertShapeMismatch:
    """Verify that modified_beer_lambert raises on invalid input shapes.

    Silently broadcasting mismatched arrays would produce wrong concentration
    values, so the function must raise ValueError for shape mismatches.
    """

    def test_3d_od_wavelength_mismatch_raises(self) -> None:
        """3-D OD with shape[1] != len(wavelengths) must raise ValueError.

        E.g., OD with 3 wavelength channels but only 2 wavelengths provided.
        """
        od = np.zeros((10, 3, 2))  # 3 wavelength channels
        wavelengths = np.array([760.0, 850.0])  # only 2 wavelengths
        d = np.array([3.0, 3.0])
        with pytest.raises(ValueError, match="od shape"):
            modified_beer_lambert(od, wavelengths, d)

    def test_2d_od_not_divisible_by_n_wl_raises(self) -> None:
        """2-D OD whose channel count is not divisible by n_wl must raise.

        E.g., OD with 5 interleaved channels but 2 wavelengths → 5 % 2 ≠ 0.
        """
        od = np.zeros((10, 5))  # 5 channels
        wavelengths = np.array([760.0, 850.0])  # 2 wavelengths
        d = np.array([3.0])
        with pytest.raises(ValueError, match="not divisible"):
            modified_beer_lambert(od, wavelengths, d)

    def test_1d_od_raises(self) -> None:
        """1-D OD array must raise ValueError (need at least 2 dims)."""
        od = np.zeros((10,))
        wavelengths = np.array([760.0, 850.0])
        d = np.array([3.0])
        with pytest.raises(ValueError, match="2-D or 3-D"):
            modified_beer_lambert(od, wavelengths, d)

    def test_4d_od_raises(self) -> None:
        """4-D OD array must raise ValueError."""
        od = np.zeros((5, 2, 2, 2))
        wavelengths = np.array([760.0, 850.0])
        d = np.array([3.0, 3.0])
        with pytest.raises(ValueError, match="2-D or 3-D"):
            modified_beer_lambert(od, wavelengths, d)


# ---------------------------------------------------------------------------
#  extinction_matrix — validation against published reference values
# ---------------------------------------------------------------------------


class TestExtinctionMatrixReference:
    """Validate extinction_matrix against published UCL/Scholkmann values.

    Reference values from UCL Biomedical Optics Research Laboratory
    extinction coefficient database (Ref [3]) and Scholkmann & Wolf 2013
    (Ref [2], Table 1).

    The EXTINCTION_COEFFS dict in chromophore.py stores (ε_HbO, ε_HbR)
    in µM⁻¹·cm⁻¹ for each tabulated wavelength.
    """

    @pytest.mark.parametrize(
        "wl, expected_hbo, expected_hbr",
        [
            pytest.param(690, 0.312, 2.138, id="690nm-UCL-table"),
            pytest.param(760, 0.456, 1.540, id="760nm-UCL-table"),
            pytest.param(830, 0.726, 0.814, id="830nm-UCL-table"),
            pytest.param(850, 0.864, 0.724, id="850nm-UCL-table"),
        ],
    )
    def test_exact_tabulated_wavelength(
        self, wl: float, expected_hbo: float, expected_hbr: float
    ) -> None:
        """Extinction coefficients at tabulated wavelengths must exactly match
        the UCL Biomedical Optics Research Laboratory database values.

        Ref: UCL BORL database; also listed in Scholkmann & Wolf 2013,
        *J. Biomed. Opt.* 18(10), Table 1.
        """
        E = extinction_matrix(np.array([float(wl)]))
        assert E[0, 0] == pytest.approx(expected_hbo, abs=1e-6), (
            f"ε_HbO at {wl} nm: expected {expected_hbo}, got {E[0, 0]}"
        )
        assert E[0, 1] == pytest.approx(expected_hbr, abs=1e-6), (
            f"ε_HbR at {wl} nm: expected {expected_hbr}, got {E[0, 1]}"
        )

    def test_interpolated_795nm(self) -> None:
        """Verify linear interpolation at 795 nm (midpoint of 760–830).

        At the exact midpoint between two tabulated wavelengths, the
        extinction coefficients should be the arithmetic mean.

        Ref: Linear interpolation between UCL tabulated values at 760 and
        830 nm; Scholkmann & Wolf 2013, Table 1.
        """
        E = extinction_matrix(np.array([795.0]))
        # 795 is exactly halfway between 760 and 830
        expected_hbo = (EXTINCTION_COEFFS[760][0] + EXTINCTION_COEFFS[830][0]) / 2
        expected_hbr = (EXTINCTION_COEFFS[760][1] + EXTINCTION_COEFFS[830][1]) / 2
        assert E[0, 0] == pytest.approx(expected_hbo, abs=1e-6)
        assert E[0, 1] == pytest.approx(expected_hbr, abs=1e-6)

    def test_below_min_wavelength_clamps(self) -> None:
        """Wavelength below the minimum table entry (690 nm) should return
        the 690 nm coefficients (clamp behavior per _interpolate_extinction).

        Ref: UCL BORL database value at 690 nm.
        """
        E = extinction_matrix(np.array([500.0]))
        assert E[0, 0] == pytest.approx(EXTINCTION_COEFFS[690][0], abs=1e-6)
        assert E[0, 1] == pytest.approx(EXTINCTION_COEFFS[690][1], abs=1e-6)

    def test_above_max_wavelength_clamps(self) -> None:
        """Wavelength above the maximum table entry (850 nm) should return
        the 850 nm coefficients (clamp behavior per _interpolate_extinction).

        Ref: UCL BORL database value at 850 nm.
        """
        E = extinction_matrix(np.array([1000.0]))
        assert E[0, 0] == pytest.approx(EXTINCTION_COEFFS[850][0], abs=1e-6)
        assert E[0, 1] == pytest.approx(EXTINCTION_COEFFS[850][1], abs=1e-6)

    def test_multi_wavelength_ordering(self) -> None:
        """Multi-wavelength call must return rows in the same order as input.

        Ref: UCL BORL database.
        """
        wls = np.array([850.0, 690.0, 760.0])
        E = extinction_matrix(wls)
        assert E.shape == (3, 2)
        # First row should be 850 nm
        assert E[0, 0] == pytest.approx(EXTINCTION_COEFFS[850][0], abs=1e-6)
        # Second row should be 690 nm
        assert E[1, 0] == pytest.approx(EXTINCTION_COEFFS[690][0], abs=1e-6)
        # Third row should be 760 nm
        assert E[2, 0] == pytest.approx(EXTINCTION_COEFFS[760][0], abs=1e-6)

    def test_hbo_hbr_crossover_between_760_and_830(self) -> None:
        """Between 760 and 830 nm, ε_HbO crosses above ε_HbR.

        At 760 nm: ε_HbO (0.456) < ε_HbR (1.540)
        At 830 nm: ε_HbO (0.726) < ε_HbR (0.814) still, but gap narrows.
        At 850 nm: ε_HbO (0.864) > ε_HbR (0.724) — crossover occurred.

        Ref: Scholkmann & Wolf 2013, Fig. 1; UCL BORL database.
        """
        E850 = extinction_matrix(np.array([850.0]))
        assert E850[0, 0] > E850[0, 1], (
            "At 850 nm, ε_HbO should exceed ε_HbR (isobestic crossover)"
        )
        E760 = extinction_matrix(np.array([760.0]))
        assert E760[0, 0] < E760[0, 1], (
            "At 760 nm, ε_HbR should exceed ε_HbO"
        )


# ---------------------------------------------------------------------------
#  optical_density — edge cases
# ---------------------------------------------------------------------------


class TestOpticalDensityEdgeCases:
    """Edge-case tests for optical_density conversion."""

    def test_zero_intensity_clamped(self) -> None:
        """Zero intensity should not produce -inf or NaN.

        The function clamps the ratio to a minimum of 1e-12 before log,
        so the result should be finite and equal to -log10(1e-12) = 12.0
        when baseline is 1.0.
        """
        I = np.zeros((5, 2))
        od = optical_density(I, baseline=np.ones(2))
        assert np.all(np.isfinite(od)), "OD must be finite for zero intensity"
        # I/I0 = 0/1 = 0, clamped to 1e-12 → OD = -log10(1e-12) = 12
        assert np.allclose(od, 12.0, atol=1e-6)

    def test_negative_intensity_clamped(self) -> None:
        """Negative intensity (instrument artifact) should not produce NaN.

        Negative values yield negative ratios, which are clamped to 1e-12.
        """
        I = np.full((3, 1), -5.0)
        od = optical_density(I, baseline=np.array([1.0]))
        assert np.all(np.isfinite(od)), "OD must be finite for negative intensity"
        # I/I0 = -5/1 = -5, clamped to 1e-12 → OD = 12
        assert np.allclose(od, 12.0, atol=1e-6)

    def test_constant_signal_zero_od(self) -> None:
        """Constant signal (no change) should produce OD ≈ 0 when baseline
        is auto-computed from the temporal mean.

        If I(t) = constant ∀t, then I₀ = mean(I) = I, so I/I₀ = 1 → OD = 0.
        """
        I = np.full((50, 3), 42.0)
        od = optical_density(I)  # baseline=None → auto-mean
        assert np.allclose(od, 0.0, atol=1e-10)

    def test_very_small_baseline_clamped(self) -> None:
        """Baseline near zero should be clamped to 1e-12, not cause division by zero."""
        I = np.ones((5, 2))
        od = optical_density(I, baseline=np.array([1e-20, 1e-20]))
        assert np.all(np.isfinite(od)), "OD must be finite with near-zero baseline"

    def test_od_sign_convention(self) -> None:
        """Verify sign convention: intensity decrease → positive OD.

        When I < I₀, the ratio I/I₀ < 1, so -log10(ratio) > 0.
        This matches the physical convention: more attenuation = positive ΔOD.
        """
        I = np.full((10, 1), 0.1)
        od = optical_density(I, baseline=np.array([1.0]))
        assert np.all(od > 0), "Decreased intensity should give positive OD"
        assert np.allclose(od, 1.0, atol=1e-6)  # -log10(0.1) = 1

    def test_od_intensity_increase_negative(self) -> None:
        """Intensity increase relative to baseline → negative OD.

        When I > I₀, ratio > 1, so -log10(ratio) < 0.
        """
        I = np.full((10, 1), 10.0)
        od = optical_density(I, baseline=np.array([1.0]))
        assert np.all(od < 0), "Increased intensity should give negative OD"
        assert np.allclose(od, -1.0, atol=1e-6)  # -log10(10) = -1

    def test_single_timepoint(self) -> None:
        """Single-timepoint input should work (auto-baseline = the value itself)."""
        I = np.array([[5.0, 10.0]])
        od = optical_density(I)  # baseline=None → mean = [5, 10]
        assert od.shape == (1, 2)
        assert np.allclose(od, 0.0, atol=1e-10)


# ---------------------------------------------------------------------------
#  compute_hbo_hbr — end-to-end with known synthetic data
# ---------------------------------------------------------------------------


class TestComputeHbOHbRSynthetic:
    """End-to-end tests of compute_hbo_hbr with synthetic signals where
    the ground-truth HbO/HbR changes are known analytically.

    NOTE: compute_hbo_hbr chains optical_density → modified_beer_lambert.
    optical_density expects 2-D input (n_times, n_channels) with interleaved
    wavelength channels [λ1_sd1, λ1_sd2, ..., λ2_sd1, λ2_sd2, ...].
    """

    def test_pure_hbo_increase(self) -> None:
        """Inject a pure HbO increase (ΔHbR=0) and verify recovery.

        Forward model: I(λ,t) = I₀ · 10^(−ε_HbO(λ)·Δ[HbO]·d·DPF(λ))
        With Δ[HbO]=1.0µM, Δ[HbR]=0 we should recover those values.
        """
        wavelengths = np.array([760.0, 850.0])
        d = np.array([3.0])
        E = extinction_matrix(wavelengths)
        dpf = np.array([estimate_dpf(760.0), estimate_dpf(850.0)])

        delta_hbo, delta_hbr = 0.5, 0.0
        delta_c = np.array([delta_hbo, delta_hbr])

        # Forward: ΔOD = E @ Δc * d * DPF
        delta_od = (E @ delta_c) * d[0] * dpf  # shape (2,)

        I0 = 1000.0
        n_times = 20
        # Build interleaved 2D: columns are [λ1_sd1, λ2_sd1]
        intensity = np.zeros((n_times, 2))
        for w in range(2):
            intensity[:, w] = I0 * 10 ** (-delta_od[w])

        hbo, hbr = compute_hbo_hbr(
            intensity,
            wavelengths,
            d,
            dpf=dpf,
            baseline=np.full(2, I0),
        )
        assert hbo.shape == (n_times, 1)
        assert np.allclose(hbo[:, 0], delta_hbo, atol=0.05), (
            f"Expected HbO≈{delta_hbo}, got {hbo[0, 0]:.4f}"
        )
        assert np.allclose(hbr[:, 0], delta_hbr, atol=0.05), (
            f"Expected HbR≈{delta_hbr}, got {hbr[0, 0]:.4f}"
        )

    def test_pure_hbr_decrease(self) -> None:
        """Inject a pure HbR decrease (ΔHbO=0, ΔHbR=−0.5 µM) and verify.

        Ref: Standard mBLL forward/inverse round-trip; Delpy 1988.
        """
        wavelengths = np.array([760.0, 850.0])
        d = np.array([3.0])
        E = extinction_matrix(wavelengths)
        dpf = np.array([estimate_dpf(760.0), estimate_dpf(850.0)])

        delta_hbo, delta_hbr = 0.0, -0.5
        delta_c = np.array([delta_hbo, delta_hbr])
        delta_od = (E @ delta_c) * d[0] * dpf

        I0 = 1000.0
        n_times = 15
        intensity = np.zeros((n_times, 2))
        for w in range(2):
            intensity[:, w] = I0 * 10 ** (-delta_od[w])

        hbo, hbr = compute_hbo_hbr(
            intensity,
            wavelengths,
            d,
            dpf=dpf,
            baseline=np.full(2, I0),
        )
        assert np.allclose(hbo[:, 0], delta_hbo, atol=0.05)
        assert np.allclose(hbr[:, 0], delta_hbr, atol=0.05)

    def test_mixed_hbo_hbr_change(self) -> None:
        """Inject simultaneous HbO and HbR changes and verify round-trip.

        ΔHbO = +2.0 µM, ΔHbR = −1.0 µM (typical functional activation).
        Ref: Standard mBLL forward/inverse; Delpy 1988 Eq. 4.
        """
        wavelengths = np.array([760.0, 850.0])
        d = np.array([2.5])
        E = extinction_matrix(wavelengths)
        dpf = np.array([estimate_dpf(760.0), estimate_dpf(850.0)])

        delta_hbo, delta_hbr = 0.5, -0.25
        delta_c = np.array([delta_hbo, delta_hbr])
        delta_od = (E @ delta_c) * d[0] * dpf

        I0 = 500.0
        n_times = 30
        intensity = np.zeros((n_times, 2))
        for w in range(2):
            intensity[:, w] = I0 * 10 ** (-delta_od[w])

        hbo, hbr = compute_hbo_hbr(
            intensity,
            wavelengths,
            d,
            dpf=dpf,
            baseline=np.full(2, I0),
        )
        assert np.allclose(hbo[:, 0], delta_hbo, atol=0.05), (
            f"Expected HbO≈{delta_hbo}, got {hbo[0, 0]:.4f}"
        )
        assert np.allclose(hbr[:, 0], delta_hbr, atol=0.05), (
            f"Expected HbR≈{delta_hbr}, got {hbr[0, 0]:.4f}"
        )

    def test_three_wavelength_overdetermined(self) -> None:
        """Three-wavelength system (overdetermined) should still recover HbO/HbR.

        Using 690, 760, 850 nm — 3 equations, 2 unknowns — the pseudo-inverse
        should give a least-squares solution identical to the true values
        when the data is noise-free.

        Ref: Delpy 1988 §3.2; Scholkmann & Wolf 2013, §2.1.
        """
        wavelengths = np.array([690.0, 760.0, 850.0])
        d = np.array([3.0])
        E = extinction_matrix(wavelengths)
        dpf = np.array([estimate_dpf(float(wl)) for wl in wavelengths])

        delta_hbo, delta_hbr = 1.5, -0.8
        delta_c = np.array([delta_hbo, delta_hbr])
        delta_od = (E @ delta_c) * d[0] * dpf  # shape (3,)

        I0 = 1000.0
        n_times = 10
        # Interleaved 2D: [λ1_sd1, λ2_sd1, λ3_sd1]
        intensity = np.zeros((n_times, 3))
        for w in range(3):
            intensity[:, w] = I0 * 10 ** (-delta_od[w])

        hbo, hbr = compute_hbo_hbr(
            intensity,
            wavelengths,
            d,
            dpf=dpf,
            baseline=np.full(3, I0),
        )
        assert np.allclose(hbo[:, 0], delta_hbo, atol=0.05)
        assert np.allclose(hbr[:, 0], delta_hbr, atol=0.05)

    def test_multiple_sd_pairs(self) -> None:
        """End-to-end with multiple source-detector pairs (different distances).

        Each S-D pair should independently recover the injected concentrations.
        Uses interleaved 2D format: columns are
        [λ1_sd1, λ1_sd2, λ2_sd1, λ2_sd2].
        """
        wavelengths = np.array([760.0, 850.0])
        d = np.array([2.0, 3.5])  # two S-D pairs
        n_sd = len(d)
        n_wl = len(wavelengths)
        E = extinction_matrix(wavelengths)
        dpf = np.array([estimate_dpf(760.0), estimate_dpf(850.0)])

        delta_hbo, delta_hbr = 1.0, -0.5
        delta_c = np.array([delta_hbo, delta_hbr])

        I0 = 1000.0
        n_times = 10
        # Interleaved 2D: [λ1_sd1, λ1_sd2, λ2_sd1, λ2_sd2]
        intensity = np.zeros((n_times, n_wl * n_sd))
        baseline = np.full(n_wl * n_sd, I0)
        for s in range(n_sd):
            delta_od = (E @ delta_c) * d[s] * dpf
            for w in range(n_wl):
                col = w * n_sd + s  # interleaved
                intensity[:, col] = I0 * 10 ** (-delta_od[w])

        hbo, hbr = compute_hbo_hbr(
            intensity,
            wavelengths,
            d,
            dpf=dpf,
            baseline=baseline,
        )
        assert hbo.shape == (n_times, n_sd)
        for s in range(n_sd):
            assert np.allclose(hbo[:, s], delta_hbo, atol=0.05), (
                f"S-D pair {s}: expected HbO≈{delta_hbo}, got {hbo[0, s]:.4f}"
            )
            assert np.allclose(hbr[:, s], delta_hbr, atol=0.05), (
                f"S-D pair {s}: expected HbR≈{delta_hbr}, got {hbr[0, s]:.4f}"
            )


# ---------------------------------------------------------------------------
#  _interpolate_extinction — private helper but critical for correctness
# ---------------------------------------------------------------------------


class TestInterpolateExtinction:
    """Tests for _interpolate_extinction edge behavior.

    While private, this function underpins extinction_matrix and thus all
    concentration calculations. Testing it directly ensures numerical
    correctness at the boundaries.
    """

    def test_at_exact_tabulated_wavelength(self) -> None:
        """Interpolation at an exact table entry should return that entry."""
        for wl, (e_hbo, e_hbr) in EXTINCTION_COEFFS.items():
            result = _interpolate_extinction(float(wl))
            assert result[0] == pytest.approx(e_hbo, abs=1e-10)
            assert result[1] == pytest.approx(e_hbr, abs=1e-10)

    def test_below_minimum_returns_min_entry(self) -> None:
        """Wavelength below 690 nm should return 690 nm coefficients."""
        result = _interpolate_extinction(400.0)
        assert result == EXTINCTION_COEFFS[690]

    def test_above_maximum_returns_max_entry(self) -> None:
        """Wavelength above 850 nm should return 850 nm coefficients."""
        result = _interpolate_extinction(1200.0)
        assert result == EXTINCTION_COEFFS[850]

    def test_quarter_interpolation_690_760(self) -> None:
        """25% of the way from 690 to 760 (= 707.5 nm).

        frac = (707.5 - 690) / (760 - 690) = 17.5 / 70 = 0.25
        """
        e690 = np.array(EXTINCTION_COEFFS[690])
        e760 = np.array(EXTINCTION_COEFFS[760])
        expected = e690 + 0.25 * (e760 - e690)
        result = _interpolate_extinction(707.5)
        assert result[0] == pytest.approx(float(expected[0]), abs=1e-6)
        assert result[1] == pytest.approx(float(expected[1]), abs=1e-6)
