"""MNE-Python compatibility utilities.

MNE-Python is the de-facto standard for MEG/EEG analysis and
increasingly used for fNIRS.  This module provides conversion helpers
that make ``nlcore`` data interoperable with MNE's `Epochs`, `Evoked`,
and `Raw` objects.

Key conventions
---------------
* MNE channel types for fNIRS: ``'hbo'``, ``'hbr'``, ``'fnirs_cw_amplitude'``
* Channel names follow the ``S<n>-D<m> [wl]`` convention where *wl* is
  the wavelength in nm.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class SourceDetectorMap:
    """Mapping between source–detector pairs and channel indices.

    Parameters
    ----------
    sources : list of str
        Source labels, e.g. ``['S1', 'S2', ...]``.
    detectors : list of str
        Detector labels, e.g. ``['D1', 'D2', ...]``.
    pairs : list of tuple
        ``(src_idx, det_idx)`` for each channel.
    wavelengths : np.ndarray
        Wavelength per channel, shape ``(n_channels,)``.
    """

    def __init__(
        self,
        sources: List[str],
        detectors: List[str],
        pairs: List[Tuple[int, int]],
        wavelengths: np.ndarray,
    ) -> None:
        ...

    @property
    def n_channels(self) -> int:
        """Number of source–detector channels."""
        ...

    @property
    def channel_names(self) -> list[str]:
        """MNE-style channel names: ``'S1-D1 760'``, etc."""
        ...

    def mne_info(self, sfreq: float) -> dict:
        """Build an MNE ``Info``-compatible dictionary.

        Parameters
        ----------
        sfreq : float
            Sampling frequency.

        Returns
        -------
        info : dict
            Can be passed to ``mne.create_info()``.
        """
        ...


def raw_to_mne(
    data: np.ndarray,
    sfreq: float,
    sd_map: SourceDetectorMap,
    *,
    ch_types: str = "fnirs_cw_amplitude",
) -> Any:   # mne.io.Raw
    """Wrap a numpy array as an MNE `Raw` object.

    Parameters
    ----------
    data : np.ndarray
        Time series, shape ``(n_channels, n_times)`` (MNE convention).
    sfreq : float
        Sampling frequency in Hz.
    sd_map : SourceDetectorMap
        Channel layout.
    ch_types : str
        MNE channel type string.

    Returns
    -------
    raw : mne.io.RawArray
        MNE Raw object suitable for filtering, epoching, etc.

    Notes
    -----
    Requires ``mne`` to be installed.
    """
    ...


def mne_to_raw(
    raw: Any,   # mne.io.Raw
) -> Tuple[np.ndarray, float, SourceDetectorMap]:
    """Extract data array and metadata from an MNE `Raw` object.

    Parameters
    ----------
    raw : mne.io.Raw
        MNE Raw object containing fNIRS data.

    Returns
    -------
    data : np.ndarray
        Time series, shape ``(n_channels, n_times)``.
    sfreq : float
        Sampling frequency.
    sd_map : SourceDetectorMap
        Reconstructed source–detector map.
    """
    ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ch_name_to_source_detector(
    ch_name: str,
) -> Tuple[str, str, Optional[float]]:
    """Parse an MNE fNIRS channel name into source, detector, wavelength.

    >>> ch_name_to_source_detector("S1-D1 760")
    ('S1', 'D1', 760.0)
    """
    ...


def build_sd_map(
    sources: List[str],
    detectors: List[str],
    pairs: List[Tuple[int, int]],
    wavelengths: np.ndarray,
) -> SourceDetectorMap:
    """Factory to create a SourceDetectorMap (alias for the constructor)."""
    ...
