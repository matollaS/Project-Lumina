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
        self.sources = sources
        self.detectors = detectors
        self.pairs = pairs
        self.wavelengths = np.asarray(wavelengths)

    @property
    def n_channels(self) -> int:
        """Number of source–detector channels."""
        return len(self.pairs)

    @property
    def channel_names(self) -> list[str]:
        """MNE-style channel names: ``'S1-D1 760'``, etc."""
        return [
            f"{self.sources[src]}-{self.detectors[det]} {wl:.0f}"
            for (src, det), wl in zip(self.pairs, self.wavelengths)
        ]

    def mne_info(self, sfreq: float) -> dict:
        """Build an MNE ``Info``-compatible dictionary."""
        import mne
        ch_names = self.channel_names
        ch_types = ["fnirs_cw_amplitude"] * self.n_channels
        return mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)


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
    import mne
    # Ensure data is (n_channels, n_times)
    data = np.asarray(data)
    if data.shape[0] != sd_map.n_channels:
        # Try to transpose if (n_times, n_channels)
        if data.shape[1] == sd_map.n_channels:
            data = data.T
        else:
            raise ValueError("Data shape must match number of channels in sd_map")
            
    info = sd_map.mne_info(sfreq)
    raw = mne.io.RawArray(data, info)
    return raw


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
    data = raw.get_data()
    sfreq = raw.info["sfreq"]
    ch_names = raw.info["ch_names"]
    
    sources = []
    detectors = []
    pairs = []
    wavelengths = []
    
    for ch in ch_names:
        src, det, wl = ch_name_to_source_detector(ch)
        if src not in sources:
            sources.append(src)
        if det not in detectors:
            detectors.append(det)
        pairs.append((sources.index(src), detectors.index(det)))
        wavelengths.append(wl if wl is not None else 0.0)
        
    sd_map = SourceDetectorMap(sources, detectors, pairs, np.array(wavelengths))
    return data, sfreq, sd_map


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
    parts = ch_name.split(" ")
    sd = parts[0].split("-")
    if len(sd) != 2:
        return ("Unknown", "Unknown", None)
    src, det = sd[0], sd[1]
    wl = float(parts[1]) if len(parts) > 1 else None
    return (src, det, wl)


def build_sd_map(
    sources: List[str],
    detectors: List[str],
    pairs: List[Tuple[int, int]],
    wavelengths: np.ndarray,
) -> SourceDetectorMap:
    """Factory to create a SourceDetectorMap (alias for the constructor)."""
    return SourceDetectorMap(sources, detectors, pairs, wavelengths)
