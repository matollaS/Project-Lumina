Scientific scope and validation ladder
======================================

Project Lumina is being developed as a research platform for optical brain
measurement and, in the longer term, closed-loop neurophotonics. The project
separates what is measured from what is inferred and from what is eventually
intervened upon.

The three-layer model
---------------------

1. Measurement
~~~~~~~~~~~~~~

Question: *What did the instruments reliably observe?*

The public ``nlcore`` package currently lives primarily at this layer. It
supports SNIRF I/O, fNIRS preprocessing, HbO/HbR estimation, motion-artifact
handling, PBM dose/fluence calculations, haemodynamic response extraction, and
MNE-compatible data interchange.

Current public capabilities should not be interpreted as direct measurement of
a disease state, a cognitive state, mitochondrial function, or treatment
response unless the relevant observable and validation study support that
interpretation.

2. Inference
~~~~~~~~~~~~

Question: *What latent physiological or cognitive state is supported by the
measurements?*

Examples include cognitive-load classification, state-transition modelling, or
individualised response estimation. These are model outputs rather than direct
sensor observables and require prospective validation, calibration, uncertainty
estimation, and out-of-distribution testing.

3. Intervention
~~~~~~~~~~~~~~~

Question: *Can a controlled input causally and safely alter the target state?*

Closed-loop PBM is a research objective, not a present clinical capability of
``nlcore``. A defensible closed loop requires, at minimum:

* a validated observable;
* a validated state estimator;
* explicit dose and safety constraints;
* an intervention policy tested prospectively against sham/control conditions;
* independent verification of the response; and
* appropriate ethics and regulatory oversight for human studies.

A useful conceptual loop is::

    sense -> estimate -> decide -> stimulate -> verify -> repeat

The frequency of sensing or computation must not be confused with the biological
response time of the full closed loop.

What nlcore does not currently claim
------------------------------------

The public repository does **not** currently claim to:

* diagnose neurological disease;
* prescribe or optimise PBM treatment for an individual;
* provide a clinically validated closed-loop stimulator;
* measure oxidised cytochrome-c-oxidase (oxCCO) from the existing standard
  HbO/HbR path; or
* establish that a physiological correlation is a causal treatment mechanism.

oxCCO as a separate validation programme
-----------------------------------------

Oxidised cytochrome-c-oxidase is scientifically interesting because its NIR
signal may provide information related to cellular oxidative metabolism.
However, its concentration change is weaker than the haemoglobin signal and
spectrally overlaps with haemoglobin. Modern reviews therefore treat robust
oxCCO monitoring as a broadband/hyperspectral NIRS instrumentation and inverse
problem, not as a trivial extension of two-wavelength fNIRS.

For Project Lumina, oxCCO should therefore be developed as a separate hardware,
algorithm, phantom-validation, and human-validation workstream before it is used
as a closed-loop biomarker.

Research programmes
-------------------

Clinical translation
~~~~~~~~~~~~~~~~~~~~

The near-term clinical research wedge is measurement-first: quantify response,
standardise dosimetry, and learn individual dose-response relationships before
claiming therapeutic optimisation. See :doc:`pbm_evidence` for the current
condition-specific evidence tiers.

Human-state science
~~~~~~~~~~~~~~~~~~~

The same measurement/inference separation can support non-clinical research on
state transitions such as task load, sleep, meditation, absorption, or other
controlled paradigms. These should be treated as experimental conditions with
prospective protocols, multimodal sensing where appropriate, and explicit
phenomenology/behavioural measures. They are not medical indications.

Recommended evidence ladder
----------------------------

A claim should only move upward when the preceding level is reproducible:

#. bench/phantom validation;
#. healthy-volunteer measurement validation;
#. observational physiological association;
#. prospective state-inference validation;
#. sham-controlled intervention study;
#. replicated clinical efficacy and safety;
#. regulated clinical deployment, where applicable.

This ladder is deliberately conservative. It protects the long-term closed-loop
vision by making each intermediate claim testable.

Selected technical references
-----------------------------

* Ward R, Diop M, Tachtsidis I, Orihuela-Espina F. *Recent near-infrared
  approaches to cytochrome-c-oxidase monitoring: a systematic review of
  instruments and algorithms.* Phys Med Biol. 2026. PMID 42013903.
  https://pubmed.ncbi.nlm.nih.gov/42013903/
* Bale G, Elwell CE, Tachtsidis I. *Review of measurements and imaging of
  cytochrome-c-oxidase in humans using near-infrared spectroscopy: an update.*
  Biomed Opt Express. 2024. PMID 38223181.
  https://pubmed.ncbi.nlm.nih.gov/38223181/
* Pham T et al. *Quantification of oxidized and reduced cytochrome-c-oxidase by
  combining discrete-wavelength time-resolved and broadband continuous-wave
  near-infrared spectroscopy.* 2025. PMID 41368101.
  https://pubmed.ncbi.nlm.nih.gov/41368101/
