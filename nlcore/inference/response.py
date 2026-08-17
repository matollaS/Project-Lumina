"""Individualized dose-response modelling for PBM research datasets.

This module belongs to the *inference* layer of Project Lumina. It operates on
validated measurements or derived response features; it does not turn an
association into a causal treatment effect and it does not prescribe a dose.

The model deliberately stays small and inspectable:

1. fit a global polynomial ridge model of response versus PBM dose and optional
   covariates;
2. learn a regularized per-subject residual intercept/slope when enough repeated
   observations are available; and
3. return approximate predictive intervals based on residual variance and ridge
   leverage.

The subject-specific term is therefore a calibrated research adjustment, not a
clinical personalization claim.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ResponsePrediction:
    """Prediction returned by :class:`IndividualDoseResponseModel`.

    Attributes
    ----------
    mean : np.ndarray
        Predicted response for each requested observation.
    std : np.ndarray
        Approximate predictive standard deviation. This is model-based and is
        not a calibrated clinical confidence measure.
    lower, upper : np.ndarray
        Symmetric interval bounds using ``interval_z`` from the fitted model.
    used_subject_adjustment : np.ndarray
        Boolean flag showing whether a fitted subject-specific residual term was
        applied for each prediction.
    """

    mean: np.ndarray
    std: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    used_subject_adjustment: np.ndarray


def _as_1d_float(name: str, values: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-D, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _ridge_solution(x: np.ndarray, y: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    """Solve ridge regression while leaving the intercept unpenalized."""
    penalty = np.eye(x.shape[1], dtype=np.float64)
    penalty[0, 0] = 0.0
    gram = x.T @ x + alpha * penalty
    gram_inv = np.linalg.pinv(gram)
    beta = gram_inv @ x.T @ y
    return beta, gram_inv


class IndividualDoseResponseModel:
    """Transparent research model for repeated PBM dose-response observations.

    The global component is polynomial ridge regression in dose with optional
    standardized covariates. For subjects with repeated observations, a second
    regularized model is fitted to the global residuals using an intercept and
    linear dose term. New/unseen subjects receive the global estimate only.

    This class intentionally does **not** expose dose optimization or treatment
    recommendation methods. Predictions are associations learned from the fitted
    dataset and require prospective validation before any interventional use.
    """

    def __init__(
        self,
        *,
        degree: int = 2,
        alpha: float = 1.0,
        subject_alpha: float = 2.0,
        min_subject_samples: int = 3,
        interval_z: float = 1.96,
    ) -> None:
        if degree < 1 or degree > 3:
            raise ValueError("degree must be between 1 and 3")
        if alpha < 0 or subject_alpha < 0:
            raise ValueError("ridge penalties must be non-negative")
        if min_subject_samples < 2:
            raise ValueError("min_subject_samples must be at least 2")
        if interval_z <= 0:
            raise ValueError("interval_z must be positive")

        self.degree = int(degree)
        self.alpha = float(alpha)
        self.subject_alpha = float(subject_alpha)
        self.min_subject_samples = int(min_subject_samples)
        self.interval_z = float(interval_z)
        self._fitted = False

    def _prepare_covariates(
        self,
        covariates: np.ndarray | Sequence[Sequence[float]] | None,
        n_rows: int,
        *,
        fitting: bool,
    ) -> np.ndarray:
        if covariates is None:
            if fitting:
                self.n_covariates_ = 0
                self.covariate_mean_ = np.empty(0, dtype=np.float64)
                self.covariate_scale_ = np.empty(0, dtype=np.float64)
            elif self.n_covariates_ != 0:
                raise ValueError(
                    f"model expects {self.n_covariates_} covariate columns, got none"
                )
            return np.empty((n_rows, 0), dtype=np.float64)

        cov = np.asarray(covariates, dtype=np.float64)
        if cov.ndim == 1:
            cov = cov.reshape(-1, 1)
        if cov.ndim != 2 or cov.shape[0] != n_rows:
            raise ValueError(
                "covariates must have shape (n_observations, n_covariates); "
                f"got {cov.shape} for {n_rows} observations"
            )
        if not np.all(np.isfinite(cov)):
            raise ValueError("covariates contain non-finite values")

        if fitting:
            self.n_covariates_ = cov.shape[1]
            self.covariate_mean_ = np.mean(cov, axis=0)
            scale = np.std(cov, axis=0)
            self.covariate_scale_ = np.where(scale > 1e-12, scale, 1.0)
        elif cov.shape[1] != self.n_covariates_:
            raise ValueError(
                f"model expects {self.n_covariates_} covariate columns, got {cov.shape[1]}"
            )

        return (cov - self.covariate_mean_) / self.covariate_scale_

    def _global_design(self, dose: np.ndarray, covariates_scaled: np.ndarray) -> np.ndarray:
        dose_scaled = (dose - self.dose_mean_) / self.dose_scale_
        columns = [np.ones_like(dose_scaled)]
        columns.extend(dose_scaled**power for power in range(1, self.degree + 1))
        if covariates_scaled.shape[1]:
            columns.extend(covariates_scaled[:, i] for i in range(covariates_scaled.shape[1]))
        return np.column_stack(columns)

    def fit(
        self,
        dose_j_cm2: Sequence[float] | np.ndarray,
        response: Sequence[float] | np.ndarray,
        *,
        subject_ids: Sequence[str] | np.ndarray | None = None,
        covariates: np.ndarray | Sequence[Sequence[float]] | None = None,
    ) -> IndividualDoseResponseModel:
        """Fit the global and optional subject-specific response models.

        Parameters
        ----------
        dose_j_cm2 : array-like, shape (n_observations,)
            PBM radiant exposure in J/cm². Values must be non-negative.
        response : array-like, shape (n_observations,)
            A validated response feature such as ``hbo_auc`` or another
            pre-specified experimental endpoint.
        subject_ids : array-like of str, optional
            Repeated subject identifiers. Subject adjustments are fitted only
            when a subject has at least ``min_subject_samples`` observations.
        covariates : array-like, optional
            Numeric nuisance/context covariates such as baseline physiology or
            experimental condition encodings. They are standardized internally.
        """
        dose = _as_1d_float("dose_j_cm2", dose_j_cm2)
        y = _as_1d_float("response", response)
        if len(dose) != len(y):
            raise ValueError("dose_j_cm2 and response must have the same length")
        if len(dose) < max(3, self.degree + 1):
            raise ValueError("not enough observations for requested polynomial degree")
        if np.any(dose < 0):
            raise ValueError("dose_j_cm2 must be non-negative")

        self.dose_mean_ = float(np.mean(dose))
        dose_scale = float(np.std(dose))
        self.dose_scale_ = dose_scale if dose_scale > 1e-12 else 1.0

        cov_scaled = self._prepare_covariates(covariates, len(dose), fitting=True)
        x = self._global_design(dose, cov_scaled)
        self.coef_, self.global_gram_inv_ = _ridge_solution(x, y, self.alpha)
        global_pred = x @ self.coef_
        residual = y - global_pred

        if subject_ids is None:
            subjects = np.full(len(dose), "", dtype=object)
        else:
            subjects = np.asarray(subject_ids, dtype=object)
            if subjects.ndim != 1 or len(subjects) != len(dose):
                raise ValueError("subject_ids must be 1-D and match dose_j_cm2 length")
            subjects = subjects.astype(str)

        self.subject_effects_: dict[str, np.ndarray] = {}
        self.subject_gram_inv_: dict[str, np.ndarray] = {}
        adjusted_pred = global_pred.copy()
        dose_scaled = (dose - self.dose_mean_) / self.dose_scale_

        if subject_ids is not None:
            for subject in np.unique(subjects):
                mask = subjects == subject
                if int(np.sum(mask)) < self.min_subject_samples:
                    continue
                z = np.column_stack([np.ones(np.sum(mask)), dose_scaled[mask]])
                effect, gram_inv = _ridge_solution(z, residual[mask], self.subject_alpha)
                self.subject_effects_[subject] = effect
                self.subject_gram_inv_[subject] = gram_inv
                adjusted_pred[mask] += z @ effect

        final_residual = y - adjusted_pred
        dof = max(1, len(y) - x.shape[1] - 2 * len(self.subject_effects_))
        residual_var = float(np.sum(final_residual**2) / dof)
        self.residual_std_ = float(np.sqrt(max(residual_var, 1e-12)))
        self.n_observations_ = len(y)
        self._fitted = True
        return self

    def predict(
        self,
        dose_j_cm2: Sequence[float] | np.ndarray,
        *,
        subject_ids: Sequence[str] | np.ndarray | None = None,
        covariates: np.ndarray | Sequence[Sequence[float]] | None = None,
    ) -> ResponsePrediction:
        """Predict response and return an approximate predictive interval."""
        if not self._fitted:
            raise RuntimeError("model must be fitted before predict")

        dose = _as_1d_float("dose_j_cm2", dose_j_cm2)
        if np.any(dose < 0):
            raise ValueError("dose_j_cm2 must be non-negative")
        cov_scaled = self._prepare_covariates(covariates, len(dose), fitting=False)
        x = self._global_design(dose, cov_scaled)
        mean = x @ self.coef_

        # Ridge leverage provides a transparent approximation to model
        # uncertainty. The leading 1.0 includes irreducible residual variance.
        global_leverage = np.einsum("ij,jk,ik->i", x, self.global_gram_inv_, x)
        variance_factor = 1.0 + np.maximum(global_leverage, 0.0)
        used_subject = np.zeros(len(dose), dtype=bool)

        if subject_ids is not None:
            subjects = np.asarray(subject_ids, dtype=object)
            if subjects.ndim != 1 or len(subjects) != len(dose):
                raise ValueError("subject_ids must be 1-D and match dose_j_cm2 length")
            subjects = subjects.astype(str)
            dose_scaled = (dose - self.dose_mean_) / self.dose_scale_
            for subject in np.unique(subjects):
                if subject not in self.subject_effects_:
                    continue
                mask = subjects == subject
                z = np.column_stack([np.ones(np.sum(mask)), dose_scaled[mask]])
                mean[mask] += z @ self.subject_effects_[subject]
                subject_leverage = np.einsum(
                    "ij,jk,ik->i", z, self.subject_gram_inv_[subject], z
                )
                variance_factor[mask] += np.maximum(subject_leverage, 0.0)
                used_subject[mask] = True

        std = self.residual_std_ * np.sqrt(variance_factor)
        lower = mean - self.interval_z * std
        upper = mean + self.interval_z * std
        return ResponsePrediction(
            mean=np.asarray(mean, dtype=np.float64),
            std=np.asarray(std, dtype=np.float64),
            lower=np.asarray(lower, dtype=np.float64),
            upper=np.asarray(upper, dtype=np.float64),
            used_subject_adjustment=used_subject,
        )


def extract_dose_response(
    metrics: Mapping[str, float],
    *,
    response_key: str = "hbo_auc",
) -> tuple[float, float]:
    """Extract a ``(dose, response)`` pair from :func:`nlcore.pbm_metrics` output.

    The helper keeps the measurement-to-inference handoff explicit. It performs
    no causal interpretation and rejects non-finite values.
    """
    if "mean_dose" not in metrics:
        raise KeyError("metrics must contain 'mean_dose'")
    if response_key not in metrics:
        raise KeyError(f"metrics must contain response key {response_key!r}")

    dose = float(metrics["mean_dose"])
    response = float(metrics[response_key])
    if not np.isfinite(dose) or not np.isfinite(response):
        raise ValueError("dose and response metric must be finite")
    if dose < 0:
        raise ValueError("mean_dose must be non-negative")
    return dose, response
