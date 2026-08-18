"""Tests for prospective/held-out validation utilities."""

import numpy as np
import pytest

from nlcore.validation import evaluate_unseen_subjects


def _synthetic_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    subjects = np.repeat(np.array(["A", "B", "C", "D"]), 5)
    dose = np.tile(np.linspace(0.0, 8.0, 5), 4)
    offsets = np.repeat(np.array([0.2, -0.2, 0.1, -0.1]), 5)
    response = 1.5 + 0.6 * dose + offsets
    return dose, response, subjects


def test_unseen_subject_split_has_no_leakage() -> None:
    dose, response, subjects = _synthetic_dataset()

    report = evaluate_unseen_subjects(
        dose,
        response,
        subjects,
        np.array(["D"]),
        model_kwargs={"degree": 1, "alpha": 0.0, "subject_alpha": 0.0},
    )

    assert report.n_train == 15
    assert report.n_test == 5
    assert report.n_train_subjects == 3
    assert report.n_test_subjects == 1
    assert set(subjects[report.train_mask]) == {"A", "B", "C"}
    assert set(subjects[report.test_mask]) == {"D"}
    assert report.rmse < 0.3
    assert report.mae < 0.3
    assert report.mean_interval_width > 0.0


def test_multiple_holdout_subjects_are_supported() -> None:
    dose, response, subjects = _synthetic_dataset()

    report = evaluate_unseen_subjects(
        dose,
        response,
        subjects,
        np.array(["C", "D"]),
        model_kwargs={"degree": 1, "alpha": 0.0},
    )

    assert report.n_test == 10
    assert report.n_test_subjects == 2
    assert 0.0 <= report.interval_coverage <= 1.0
    assert report.predictions.shape == (10,)
    assert report.lower.shape == (10,)
    assert report.upper.shape == (10,)


def test_covariates_are_fit_only_from_training_partition() -> None:
    dose, _, subjects = _synthetic_dataset()
    context = np.linspace(-1.0, 1.0, len(dose))
    response = 1.0 + 0.5 * dose + 2.0 * context

    report = evaluate_unseen_subjects(
        dose,
        response,
        subjects,
        np.array(["D"]),
        covariates=context,
        model_kwargs={"degree": 1, "alpha": 0.0},
    )

    assert report.rmse < 1e-8


def test_unknown_holdout_subject_is_rejected() -> None:
    dose, response, subjects = _synthetic_dataset()

    with pytest.raises(ValueError, match="none of holdout_subjects"):
        evaluate_unseen_subjects(dose, response, subjects, np.array(["Z"]))


def test_empty_holdout_is_rejected() -> None:
    dose, response, subjects = _synthetic_dataset()

    with pytest.raises(ValueError, match="at least one subject"):
        evaluate_unseen_subjects(dose, response, subjects, np.array([]))


def test_bad_covariate_shape_is_rejected() -> None:
    dose, response, subjects = _synthetic_dataset()

    with pytest.raises(ValueError, match="covariates must have shape"):
        evaluate_unseen_subjects(
            dose,
            response,
            subjects,
            np.array(["D"]),
            covariates=np.ones((3, 2)),
        )
