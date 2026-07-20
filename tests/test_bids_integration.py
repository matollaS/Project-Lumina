import os
import numpy as np
import pytest
import nlcore

def test_bids_snirf_integration():
    """Test loading and processing a real BIDS SNIRF file."""
    fname = "sub-01_task-tapping_nirs.snirf"
    
    if not os.path.exists(fname):
        pytest.skip(f"Test file {fname} not found. Skipping integration test.")
        
    ts, time, meta = nlcore.load_snirf(fname)
    
    assert ts.shape[0] > 0
    assert ts.shape[1] > 0
    assert len(time) == ts.shape[0]
    assert "wavelengths" in meta
    
    wls = meta["wavelengths"]
    assert len(wls) == 2  # BIDS tapping usually has 2 wavelengths
    
    # Calculate S-D pairs. Total channels = 56. 2 wavelengths. So 28 pairs.
    n_total_channels = ts.shape[1]
    n_wl = len(wls)
    n_sd_pairs = n_total_channels // n_wl
    
    # Mocking standard 3.0 cm distances for all pairs since the snirf might lack it
    d = meta.get("distances", np.full(n_sd_pairs, 3.0))
    
    assert len(d) == n_sd_pairs
    
    hbo, hbr = nlcore.compute_hbo_hbr(ts, wls, d)
    
    # Output shapes should be (n_times, n_sd_pairs)
    assert hbo.shape == (ts.shape[0], n_sd_pairs)
    assert hbr.shape == (ts.shape[0], n_sd_pairs)
    
    # Ensure no NaNs are produced
    assert not np.isnan(hbo).any()
    assert not np.isnan(hbr).any()
    
    # Ensure results are within plausible physiological bounds for concentration (µM)
    assert np.all(hbo > -1000) and np.all(hbo < 1000)
    assert np.all(hbr > -1000) and np.all(hbr < 1000)
