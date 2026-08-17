Individualized response modelling
=================================

``nlcore`` now contains a small, explicit inference-layer model for repeated PBM
research observations. The purpose is to connect reproducible measurement and
dosimetry outputs to a testable individual-response hypothesis without turning
that hypothesis into a treatment recommendation.

Model structure
---------------

:class:`nlcore.IndividualDoseResponseModel` uses two stages:

#. a global polynomial ridge model of response versus PBM radiant exposure and
   optional numeric covariates; and
#. a regularized subject-specific residual intercept and slope when enough
   repeated observations exist for that subject.

An unseen subject receives the global prediction only. Every prediction reports
whether a subject-specific adjustment was actually used.

The returned interval is an approximate predictive interval based on the fitted
residual variance and ridge leverage. It is useful for model diagnostics and
prospective protocol design, but it is not a calibrated clinical confidence
interval.

Measurement-to-inference handoff
--------------------------------

A typical workflow is::

    from nlcore import (
        IndividualDoseResponseModel,
        extract_dose_response,
        pbm_metrics,
    )

    observations = []
    for run in experiment_runs:
        metrics = pbm_metrics(
            run.hbo,
            run.hbr,
            run.fs,
            power_mw=run.power_mw,
            area_cm2=run.area_cm2,
            dose_duration_s=run.duration_s,
        )
        observations.append(extract_dose_response(metrics, response_key="hbo_auc"))

    dose = [item[0] for item in observations]
    response = [item[1] for item in observations]

    model = IndividualDoseResponseModel(degree=2)
    model.fit(dose, response, subject_ids=subject_ids, covariates=covariates)
    prediction = model.predict(
        candidate_doses,
        subject_ids=candidate_subject_ids,
        covariates=candidate_covariates,
    )

This bridge is intentionally explicit: ``pbm_metrics`` produces measured or
derived experimental quantities, while ``IndividualDoseResponseModel`` produces
an inference from a fitted dataset.

What the model does not establish
---------------------------------

A fitted dose-response curve does not by itself establish:

* that PBM caused the observed response;
* that the fitted response is clinically beneficial;
* that a higher or lower predicted response is desirable;
* that the model is valid outside the fitted dose, population, device, or
  protocol range; or
* that any dose should be selected for treatment.

For those reasons the public API intentionally contains no ``optimize_dose`` or
``recommend_dose`` method. Interventional use belongs later in the validation
ladder, after prospective inference validation and appropriate controlled safety
studies.

Prospective validation target
-----------------------------

The next defensible experiment is not retrospective curve fitting alone. It is a
held-out or prospective test in which the response endpoint, dose range,
covariates, subject-calibration procedure, and acceptance criteria are fixed in
advance. Useful evaluation quantities include prediction error, interval
coverage, calibration drift, subject-specific improvement over the global model,
and performance on unseen subjects.
