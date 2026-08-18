Prospective PBM response validation
===================================

The individualized response model is useful only if it predicts observations
that were not used to fit or tune it. Project Lumina therefore treats
prospective validation as a separate stage between inference development and
any future intervention research.

This document defines the software-facing validation design. It is not a
clinical protocol and does not select a PBM dose.

Primary question
----------------

The first validation question is deliberately narrow:

    Can a model fitted on previously observed subjects predict a pre-specified
    physiological PBM-response endpoint in entirely unseen subjects?

The primary split is therefore made by **subject**, not by row or session. All
observations from a held-out person remain outside fitting and calibration.
This prevents repeated measurements from the same person leaking information
into both sides of the evaluation.

Protocol file
-------------

The machine-readable draft is stored at
``protocols/pbm_response_validation_v1.json``. It pre-specifies the intended
endpoint, split unit, model class, primary metrics, and analysis-integrity
rules while leaving safety-, hardware-, sample-size-, and threshold-dependent
fields explicitly unresolved.

The protocol remains ``draft-not-locked`` until, at minimum:

* PBM stimulation parameters and allowed dose range are fixed by the approved
  experimental/safety framework;
* signal-quality and exclusion rules are fixed;
* covariates are frozen;
* model hyperparameters are frozen;
* sample-size or precision rationale is completed;
* numerical success thresholds are frozen; and
* the exact software commit or release tag is pinned.

A field marked ``TBD`` or ``null`` is not permission to decide it after looking
at prospective outcomes. It is a blocker to protocol lock.

Primary endpoint
----------------

Version 1 names ``hbo_auc`` from :func:`nlcore.pbm_metrics` as the primary
software endpoint. In the current implementation this is the integrated
magnitude of the baseline-subtracted mean-channel HbO response over the
pre-specified response window.

This is a physiological response feature, not a clinical outcome and not proof
of a therapeutic mechanism. Changing the primary endpoint after protocol lock
requires a new protocol version.

Primary evaluation
------------------

Use :func:`nlcore.validation.evaluate_unseen_subjects` to fit the existing
:class:`nlcore.IndividualDoseResponseModel` on non-holdout subjects and evaluate
it on subjects that were never seen during fitting.

The function reports:

* RMSE;
* MAE;
* mean signed error (bias);
* prediction-interval coverage;
* mean prediction-interval width; and
* the exact train/test masks used.

Example::

    from nlcore.validation import evaluate_unseen_subjects

    report = evaluate_unseen_subjects(
        dose_j_cm2=dose,
        response=hbo_auc,
        subject_ids=subject_ids,
        holdout_subjects=["sub-021", "sub-022"],
        covariates=covariates,
        model_kwargs={
            "degree": 2,
            "alpha": 1.0,
            "subject_alpha": 2.0,
            "min_subject_samples": 3,
            "interval_z": 1.96,
        },
    )

    print(report.rmse, report.interval_coverage)

The held-out subjects cannot receive learned subject-specific adjustments. The
primary analysis therefore tests **new-subject generalization** of the global
model.

What must be frozen before evaluation
-------------------------------------

The following choices materially affect the result and should be fixed before
prospective outcomes are inspected:

#. stimulation wavelength(s), power, area, duration, duty cycle/pulse settings,
   and allowed radiant-exposure range;
#. preprocessing and motion-quality rules;
#. baseline and response windows;
#. channel inclusion/exclusion and aggregation rules;
#. primary response endpoint;
#. allowed covariates and their encoding;
#. model hyperparameters;
#. subject holdout rule;
#. sample-size/precision rationale; and
#. quantitative success criteria.

This is intentionally stricter than ordinary exploratory analysis. The purpose
is to make failure informative rather than allowing the analysis to drift until
it succeeds.

Secondary calibration question
------------------------------

A later protocol may test whether a small, pre-specified number of calibration
sessions from a new subject improves prediction of that subject's subsequent
sessions. That is a distinct question from the primary unseen-subject test and
should use a temporal/calibration split that prevents future observations from
influencing earlier predictions.

No clinical leap
----------------

Passing this validation would support a claim that the model predicts the
locked physiological endpoint under the tested protocol. It would not establish
that PBM is clinically effective, that the endpoint is a surrogate for benefit,
or that the model can safely choose an intervention. Those require separate
prospective causal and safety studies.
