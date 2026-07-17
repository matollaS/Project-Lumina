"""SNIRF (Shared Near-Infrared Spectroscopy Format) file I/O.

The SNIRF specification defines an HDF5-based file format for storing
functional near-infrared spectroscopy (fNIRS) data.  This module provides
a pure-Python reader/writer that maps SNIRF groups and datasets onto
numpy arrays and MNE-compatible structures.

SNIRF v1.0 specification reference:
    https://github.com/fNIRS/snirf

Data model
----------
*nirs / metaDataTags*
    Subject ID, measurement date, instrument model, etc.
*nirs / data<n>*  (one group per acquisition run)
    *dataTimeSeries*  —  ``(time, channel)`` float32
    *time*            —  ``(time,)`` float32
    *stim*            —  stimulus onset/type table
    *probe*           —  source/detector positions and optode matrix
    *aux*             —  auxiliary signals (accelerometers, etc.)
*nirs / probe*
    Default probe geometry (wavelengths, source/detector labels).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import numpy as np
import h5py


def _decode_bytes(val):
    """Decode bytes/ndarray of bytes to str or list of str."""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if isinstance(val, np.ndarray) and val.dtype.kind == "S":
        return val.astype(str).tolist()
    if isinstance(val, np.ndarray) and val.dtype.kind == "U":
        return val.tolist()
    if isinstance(val, (list, tuple)):
        return [_decode_bytes(v) for v in val]
    return val


def _read_compound_labels(h5group, dataset_name: str) -> list[str]:
    """Read labels from a compound dataset that has a 'label' field."""
    ds = h5group[dataset_name]
    labels = []
    if hasattr(ds, "dtype") and ds.dtype.names is not None:
        if "label" in ds.dtype.names:
            for row in ds[:]:
                label = row["label"]
                if isinstance(label, bytes):
                    label = label.decode("utf-8", errors="replace")
                labels.append(str(label))
    else:
        labels = _decode_bytes(ds[:])
    return labels


class SnirfFile:
    """Handle for a SNIRF file, providing read and write access.

    Parameters
    ----------
    fname : path-like
        Path to the ``.snirf`` file on disk.
    mode : str
        Open mode (``'r'``, ``'r+'``, ``'w'``).  Default ``'r'``.
    """

    def __init__(self, fname: Union[str, Path], mode: str = "r") -> None:
        self._fname = Path(fname)
        self._mode = mode
        self._h5: Optional[h5py.File] = None

    @property
    def h5(self) -> h5py.File:
        if self._h5 is None:
            self._h5 = h5py.File(self._fname, self._mode)
        return self._h5

    @property
    def n_runs(self) -> int:
        nirs = self.h5.get("/nirs")
        if nirs is None:
            return 0
        count = 0
        i = 1
        while f"data{i}" in nirs:
            count += 1
            i += 1
        return count

    @property
    def wavelengths(self) -> np.ndarray:
        wl_ds = self.h5.get("/nirs/probe/wavelengths")
        if wl_ds is None:
            return np.array([], dtype=np.float64)
        return np.asarray(wl_ds, dtype=np.float64).flatten()

    @property
    def source_labels(self) -> list[str]:
        probe = self.h5.get("/nirs/probe")
        if probe is None:
            return []
        return _read_compound_labels(probe, "sourceLabels")

    @property
    def detector_labels(self) -> list[str]:
        probe = self.h5.get("/nirs/probe")
        if probe is None:
            return []
        return _read_compound_labels(probe, "detectorLabels")

    def read_data(self, run_index: int = 0) -> dict[str, np.ndarray]:
        group_path = f"/nirs/data{run_index + 1}"
        grp = self.h5.get(group_path)
        if grp is None:
            raise KeyError(f"Run group '{group_path}' not found in {self._fname}")

        ts = np.asarray(grp["dataTimeSeries"], dtype=np.float64)
        time = np.asarray(grp["time"], dtype=np.float64).flatten()

        result: dict[str, np.ndarray] = {"ts": ts, "time": time}

        if "stim" in grp:
            stim_grp = grp["stim"]
            if "data" in stim_grp:
                result["stim"] = np.asarray(stim_grp["data"])

        if "probe" in grp:
            p = grp["probe"]
            coords: dict[str, np.ndarray] = {}
            for key in ("sourcePos2D", "sourcePos3D", "detectorPos2D", "detectorPos3D"):
                if key in p:
                    coords[key] = np.asarray(p[key], dtype=np.float64)
            if coords:
                result["probe_coords"] = coords

        if "aux" in grp:
            aux_grp = grp["aux"]
            if "dataTimeSeries" in aux_grp:
                result["aux"] = np.asarray(aux_grp["dataTimeSeries"], dtype=np.float64)

        return result

    def read_meta(self) -> dict[str, str]:
        meta: dict[str, str] = {}
        mdt = self.h5.get("/nirs/metaDataTags")
        if mdt is not None:
            for key in mdt:
                val = _decode_bytes(mdt[key][()])
                meta[key] = val
        return meta

    def close(self) -> None:
        if self._h5 is not None:
            self._h5.close()
            self._h5 = None

    def __enter__(self) -> "SnirfFile":
        return self

    def __exit__(self, *args) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Convenience top-level functions
# ---------------------------------------------------------------------------

def load_snirf(
    fname: Union[str, Path],
    run_index: int = 0,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load time-series data and metadata from a SNIRF file.

    Parameters
    ----------
    fname : path-like
        Path to ``.snirf`` file.
    run_index : int
        Run to load (default ``0``).

    Returns
    -------
    ts : np.ndarray
        Data array of shape ``(n_times, n_channels)``.
    time : np.ndarray
        Time vector of shape ``(n_times,)`` in seconds.
    meta : dict
        Metadata (subject ID, probe geometry, wavelengths, fs, etc.).
    """
    with SnirfFile(fname, "r") as sf:
        data = sf.read_data(run_index=run_index)
        ts = data["ts"]
        time = data["time"]

        meta = sf.read_meta()
        meta["_wavelengths"] = sf.wavelengths.tolist()
        meta["_source_labels"] = sf.source_labels
        meta["_detector_labels"] = sf.detector_labels
        meta["_n_runs"] = sf.n_runs

        if "probe_coords" in data:
            meta["_probe_coords"] = {
                k: v.tolist() for k, v in data["probe_coords"].items()
            }

        if "stim" in data:
            meta["_has_stim"] = True

        meta["fs"] = 1.0 / float(np.median(np.diff(time)))
        meta["wavelengths"] = np.array(meta["_wavelengths"])
        meta["sourceLabels"] = meta["_source_labels"]
        meta["detectorLabels"] = meta["_detector_labels"]

        return ts, time, meta


def save_snirf(
    fname: Union[str, Path],
    ts: np.ndarray,
    time: np.ndarray,
    meta: dict,
    *,
    stim: Optional[np.ndarray] = None,
    aux: Optional[np.ndarray] = None,
) -> None:
    """Write a time series to a SNIRF v1.0 file.

    Parameters
    ----------
    fname : path-like
        Output filename (``.snirf``).
    ts : np.ndarray
        Data, shape ``(n_times, n_channels)``.
    time : np.ndarray
        Time vector, shape ``(n_times,)``.
    meta : dict
        Metadata dict (must include ``'SubjectID'``, ``'wavelengths'``,
        ``'sourceLabels'``, ``'detectorLabels'``).
    stim : np.ndarray or None
        Stimulus table (structured array).
    aux : np.ndarray or None
        Auxiliary signals, shape ``(n_times, n_aux)``.
    """
    with h5py.File(fname, "w") as f:
        nirs = f.create_group("nirs")

        mdt = nirs.create_group("metaDataTags")
        for key, val in meta.items():
            if not key.startswith("_"):
                mdt.create_dataset(key, data=np.bytes_(str(val)))
        if "SubjectID" not in meta:
            mdt.create_dataset("SubjectID", data=np.bytes_("unknown"))

        probe = nirs.create_group("probe")
        wavelengths = np.asarray(meta.get("wavelengths", []), dtype=np.float64)
        probe.create_dataset("wavelengths", data=wavelengths)

        src_labels = meta.get("sourceLabels", meta.get("_source_labels", []))
        det_labels = meta.get("detectorLabels", meta.get("_detectorLabels", []))

        if src_labels:
            dt = np.dtype([("label", h5py.string_dtype())])
            probe.create_dataset("sourceLabels", data=np.array([(l,) for l in src_labels], dtype=dt))
        if det_labels:
            dt = np.dtype([("label", h5py.string_dtype())])
            probe.create_dataset("detectorLabels", data=np.array([(l,) for l in det_labels], dtype=dt))

        probe_coords = meta.get("_probe_coords", {})
        for coord_name, coord_data in probe_coords.items():
            arr = np.array(coord_data, dtype=np.float64) if isinstance(coord_data, list) else coord_data
            if isinstance(arr, np.ndarray):
                probe.create_dataset(coord_name, data=arr)

        data_grp = nirs.create_group("data1")
        data_grp.create_dataset("dataTimeSeries", data=np.asarray(ts, dtype=np.float64))
        data_grp.create_dataset("time", data=np.asarray(time, dtype=np.float64).flatten())

        if stim is not None:
            sgrp = data_grp.create_group("stim")
            sgrp.create_dataset("data", data=stim)

        if aux is not None:
            agrp = data_grp.create_group("aux")
            agrp.create_dataset("dataTimeSeries", data=np.asarray(aux, dtype=np.float64))
