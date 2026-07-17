Getting Started
===============

Installation
------------

.. code-block:: bash

    pip install nlcore

Or for development:

.. code-block:: bash

    git clone https://github.com/neurolumina/nlcore.git
    cd nlcore
    pip install -e ".[dev]"

Basic Usage
-----------

.. code-block:: python

    import nlcore

    # Load a SNIRF file
    ts, time, meta = nlcore.load_snirf("recording.snirf")

    # Preprocess
    filtered = nlcore.bandpass_filter(ts, fs=10.0)
    mask = nlcore.detect_motion_artifacts(filtered, fs=10.0)
    clean = nlcore.correct_motion_spline(filtered, mask)

    # Convert to chromophores
    hbo, hbr = nlcore.compute_hbo_hbr(
        clean, wavelengths=meta["wavelengths"], d=meta["distances"]
    )

Next Steps
----------

- :doc:`api/io` — SNIRF file format I/O
- :doc:`api/preprocessing` — filtering and motion correction
- :doc:`api/physiology` — chromophore conversion and PBM metrics
- :doc:`api/utils` — MNE-Python integration
