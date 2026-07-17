"""Tests for preprocessing filters and motion correction."""

import numpy as np
import pytest


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
