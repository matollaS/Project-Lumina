"""Tests for preprocessing filters and motion correction."""

import numpy as np


class TestBandpassFilter:
    """Tests for bandpass_filter()."""

    def test_import(self) -> None:
        from nlcore import bandpass_filter

        assert callable(bandpass_filter)

    def test_1d_signal_shape_preserved(self) -> None:
        """Bandpass should return same shape as input."""
        from nlcore.preprocessing.filtering import bandpass_filter

        x = np.sin(2 * np.pi * 0.1 * np.arange(1000) / 10.0)
        y = bandpass_filter(x, fs=10.0, lowcut=0.01, highcut=0.5)
        assert y.shape == x.shape


class TestNotchFilter:
    """Tests for notch_filter()."""

    def test_import(self) -> None:
        from nlcore import notch_filter

        assert callable(notch_filter)


class TestMotionDetection:
    """Tests for motion artifact detection."""

    def test_import(self) -> None:
        from nlcore import detect_motion_artifacts

        assert callable(detect_motion_artifacts)

    def test_clean_signal_no_artifacts(self) -> None:
        """A clean sinusoid should yield zero artifacts."""
        from nlcore.preprocessing.motion import detect_motion_artifacts

        x = np.sin(2 * np.pi * 0.1 * np.arange(1000) / 10.0)
        mask = detect_motion_artifacts(x, fs=10.0, amp_thresh=5.0)
        assert not np.any(mask)


class TestMotionCorrection:
    """Tests for motion correction methods."""

    def test_spline_import(self) -> None:
        from nlcore import correct_motion_spline

        assert callable(correct_motion_spline)

    def test_pca_import(self) -> None:
        from nlcore import correct_motion_pca

        assert callable(correct_motion_pca)

    def test_wavelet_import(self) -> None:
        from nlcore import correct_motion_wavelet

        assert callable(correct_motion_wavelet)

    def test_stubs_no_error(self) -> None:
        """Test functional implementation of motion correction on simple mock arrays."""
        from nlcore import correct_motion_pca, correct_motion_spline, correct_motion_wavelet

        # Create a mock 2D data array with an obvious artifact spike
        data = np.zeros((100, 2))
        data[40:60, :] = 100.0  # huge artifact

        mask = np.zeros((100, 2), dtype=bool)
        mask[40:60, :] = True

        # Spline test
        spline_corrected = correct_motion_spline(data, mask)
        assert spline_corrected.shape == data.shape
        # The artifact should be flattened out to near zero by spline
        assert np.max(np.abs(spline_corrected[40:60, :])) < 5.0

        # PCA test (need more channels for PCA to work well, but it should not crash)
        data_pca = np.zeros((100, 6))
        data_pca[40:60, :] = 100.0
        mask_pca = np.zeros((100, 6), dtype=bool)
        mask_pca[40:60, :] = True
        pca_corrected = correct_motion_pca(data_pca, mask_pca, n_components=1)
        assert pca_corrected.shape == data_pca.shape

        # Wavelet test
        wave_corrected = correct_motion_wavelet(data, mask, wavelet="db4", level=2)
        assert wave_corrected.shape == data.shape
