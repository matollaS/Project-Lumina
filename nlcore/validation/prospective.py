"""Prospective/held-out validation utilities for inference-layer models.

The functions in this module evaluate predictive performance on observations
that were not used to fit the model. They are intended for research validation,
not for treatment selection or clinical decision support.

The primary design implemented here is *unseen-subject holdout*: all
observations from specified subjects are excluded from fitting and used only for
evaluation. This prevents repeated observations from the same person leaking
across train and test sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from nlcore.inference.response import IndividualDoseResponseModel


@dataclass(frozen=True)
class ValidationReport:
    """Summary of held-out predictive performance.

    Attributes
    ----------
    n_train, n_test : int
        Number of observations used for fitting and evaluation.
    n_train_subjects, n_test_subjects : int
        Number of unique subjects in each partition.
    rmse, mae, bias : float
        Root-mean-square error, mean absolute error, and mean signed error on
        held-out observations.
    interval_coverage : float
        Fraction of held-out responses inside the model's prediction interval.
    mean_interval_width : float
        Mean width of the prediction interval on held-out observations.
    predictions, lower, upper : np.ndarray
        Held-out predictions and interval bounds in original test-set order.
    train_mask, test_mask : np.ndarray
        Boolean masks that define the exact split used for evaluation.
    """

    n_train: int
    n_test: int
    n_train_subjects: int
    n_test_subjects: int
    rmse: float
    mae: float
    bias: float
    interval_coverage: float
    mean_interval_width: float
    predictions: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    train_mask: np.ndarray
    test_mask: np.ndarray


def _as_1d(name: str, values: Any, *, dtype: Any = np.float64) -> np.ndarray:
    arr = np.asarray(values, dtype=dtype)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-D, got shape {arr.shape}")
    return arr


def evaluate_unseen_subjects(
    dose_j_cm2: np.ndarray,
    response: np.ndarray,
    subject_ids: np.ndarray,
    holdout_subjects: np.ndarray,
    *,
    covariates: np.ndarray | None = None,
    model_kwargs: dict[str, Any] | None = None,
) -> ValidationReport:
    """Fit on non-holdout subjects and evaluate on entirely unseen subjects.

    Parameters
    ----------
    dose_j_cm2 : array-like, shape (n_observations,)
        PBM radiant exposure in J/cm².
    response : array-like, shape (n_observations,)
        Pre-specified physiological response endpoint.
    subject_ids : array-like, shape (n_observations,)
        Subject identifier for every observation.
    holdout_subjects : array-like
        Subject identifiers reserved completely for evaluation.
    covariates : array-like, optional
        Numeric covariates with one row per observation. The training subset is
        used to estimate standardization parameters; test rows are transformed
        using those training parameters by the fitted model.
    model_kwargs : dict, optional
        Keyword arguments forwarded to :class:`IndividualDoseResponseModel`.

    Returns
    -------
    ValidationReport
        Held-out error and interval metrics plus the exact split masks.

    Notes
    -----
    Test subjects are passed to ``predict`` but cannot receive a fitted
    subject-specific adjustment because they were never seen during training.
    This explicitly measures global-model generalization to new people.
    """
    dose = _as_1d("dose_j_cm2", dose_j_cm2)
    y = _as_1d("response", response)
    subjects = _as_1d("subject_ids", subject_ids, dtype=object).astype(str)
    held_out = _as_1d("holdout_subjects", holdout_subjects, dtype=object).astype(str)

    n = len(dose)
    if len(y) != n or len(subjects) != n:
        raise ValueError("dose_j_cm2, response, and subject_ids must have equal length")
    if n == 0:
        raise ValueError("at least one observation is required")
    if len(held_out) == 0:
        raise ValueError("holdout_subjects must contain at least one subject")
    if not np.all(np.isfinite(dose)) or not np.all(np.isfinite(y)):
        raise ValueError("dose_j_cm2 and response must contain only finite values")
    if np.any(dose < 0):
        raise ValueError("dose_j_cm2 must be non-negative")

    test_mask = np.isin(subjects, held_out)
    train_mask = ~test_mask
    if not np.any(test_mask):
        raise ValueError("none of holdout_subjects occur in subject_ids")
    if not np.any(train_mask):
        raise ValueError("holdout split leaves no training observations")

    train_subjects = np.unique(subjects[train_mask])
    test_subjects = np.unique(subjects[test_mask])
    overlap = np.intersect1d(train_subjects, test_subjects)
    if len(overlap):
        raise RuntimeError("subject leakage detected between train and test partitions")

    cov = None
    cov_train = None
    cov_test = None
    if covariates is not None:
        cov = np.asarray(covariates, dtype=np.float64)
        if cov.ndim == 1:
            cov = cov.reshape(-1, 1)
        if cov.ndim != 2 or cov.shape[0] != n:
            raise ValueError(
                "covariates must have shape (n_observations, n_covariates); "
                f"got {cov.shape} for {n} observations"
            )
        if not np.all(np.isfinite(cov)):
            raise ValueError("covariates contain non-finite values")
        cov_train = cov[train_mask]
        cov_test = cov[test_mask]

    kwargs = dict(model_kwargs or {})
    model = IndividualDoseResponseModel(**kwargs)
    model.fit(
        dose[train_mask],
        y[train_mask],
        subject_ids=subjects[train_mask],
        covariates=cov_train,
    )
    pred = model.predict(
        dose[test_mask],
        subject_ids=subjects[test_mask],
        covariates=cov_test,
    )

    # By construction, the held-out subjects are unseen and therefore must not
    # receive learned subject-specific residual adjustments.
    if np.any(pred.used_subject_adjustment):
        raise RuntimeError("held-out subjects unexpectedly received subject adjustments")

    errors = pred.mean - y[test_mask]
    rmse = float(np.sqrt(np.mean(errors**2)))
    mae = float(np.mean(np.abs(errors)))
    bias = float(np.mean(errors))
    covered = (y[test_mask] >= pred.lower) & (y[test_mask] <= pred.upper)
    interval_coverage = float(np.mean(covered))
    mean_interval_width = float(np.mean(pred.upper - pred.lower))

    return ValidationReport(
        n_train=int(np.sum(train_mask)),
        n_test=int(np.sum(test_mask)),
        n_train_subjects=len(train_subjects),
        n_test_subjects=len(test_subjects),
        rmse=rmse,
        mae=mae,
        bias=bias,
        interval_coverage=interval_coverage,
        mean_interval_width=mean_interval_width,
        predictions=pred.mean,
        lower=pred.lower,
        upper=pred.upper,
        train_mask=train_mask,
        test_mask=test_mask,
    )
