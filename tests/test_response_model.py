"""Tests for the inference-layer individualized dose-response model."""

import numpy as np
import pytest

from nlcore import IndividualDoseResponseModel, extract_dose_response


def test_global_linear_response_is_recovered() -> None:
    dose = np.linspace(0.0, 12.0, 13)
    response = 2.0 + 0.5 * dose

    model = IndividualDoseResponseModel(degree=1, alpha=0.0)
    model.fit(dose, response)
    pred = model.predict(np.array([1.0, 5.0, 10.0]))

    assert pred.mean == pytest.approx(np.array([2.5, 4.5, 7.0]), abs=1e-9)
    assert np.all(pred.std > 0)
    assert np.all(pred.lower <= pred.mean)
    assert np.all(pred.upper >= pred.mean)
    assert not np.any(pred.used_subject_adjustment)


def test_repeated_subjects_receive_regularized_adjustments() -> None:
    dose_single = np.array([0.0, 2.0, 4.0, 6.0])
    dose = np.tile(dose_single, 2)
    subjects = np.array(["A"] * 4 + ["B"] * 4)
    baseline = 1.0 + 0.4 * dose
    response = baseline + np.array([1.5] * 4 + [-1.5] * 4)

    model = IndividualDoseResponseModel(
        degree=1,
        alpha=0.0,
        subject_alpha=0.0,
        min_subject_samples=3,
    )
    model.fit(dose, response, subject_ids=subjects)

    pred = model.predict(np.array([3.0, 3.0]), subject_ids=np.array(["A", "B"]))
    assert pred.used_subject_adjustment.tolist() == [True, True]
    assert pred.mean[0] - pred.mean[1] == pytest.approx(3.0, abs=1e-8)

    unseen = model.predict(np.array([3.0]), subject_ids=np.array(["new-subject"]))
    assert unseen.used_subject_adjustment.tolist() == [False]
    assert unseen.mean[0] == pytest.approx(2.2, abs=1e-8)


def test_covariates_are_standardized_and_used() -> None:
    dose = np.linspace(0.0, 5.0, 12)
    context = np.linspace(-2.0, 2.0, 12)
    response = 0.7 * dose + 2.5 * context

    model = IndividualDoseResponseModel(degree=1, alpha=0.0)
    model.fit(dose, response, covariates=context)
    pred = model.predict(
        np.array([2.0, 2.0]),
        covariates=np.array([[-1.0], [1.0]]),
    )

    assert pred.mean[1] - pred.mean[0] == pytest.approx(5.0, abs=1e-8)


def test_covariate_schema_mismatch_raises() -> None:
    dose = np.linspace(0.0, 5.0, 8)
    covariates = np.column_stack([dose, dose**2])
    response = dose.copy()

    model = IndividualDoseResponseModel(degree=1).fit(
        dose,
        response,
        covariates=covariates,
    )

    with pytest.raises(ValueError, match="expects 2 covariate columns"):
        model.predict(np.array([1.0]), covariates=np.array([[3.0]]))


def test_extract_dose_response_keeps_measurement_inference_handoff_explicit() -> None:
    metrics = {
        "mean_dose": 6.0,
        "hbo_auc": 12.5,
        "hbo_peak": 1.2,
    }

    assert extract_dose_response(metrics) == pytest.approx((6.0, 12.5))
    assert extract_dose_response(metrics, response_key="hbo_peak") == pytest.approx((6.0, 1.2))


def test_negative_dose_is_rejected() -> None:
    model = IndividualDoseResponseModel(degree=1)
    with pytest.raises(ValueError, match="non-negative"):
        model.fit(np.array([0.0, 1.0, -1.0]), np.array([0.0, 1.0, 2.0]))
