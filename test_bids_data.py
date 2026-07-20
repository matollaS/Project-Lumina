import sys
import numpy as np
import nlcore

def test_bids_snirf():
    fname = "sub-01_task-tapping_nirs.snirf"
    print(f"Loading {fname}...")
    try:
        ts, time, meta = nlcore.load_snirf(fname)
        print("Successfully loaded.")
        print(f"Data shape: {ts.shape}")
        print(f"Wavelengths: {meta.get('wavelengths')}")
        
        # Test chromophore conversion
        wls = meta.get("wavelengths")
        if wls is not None:
            print("Testing chromophore conversion...")
            # For simplicity, assume 3.0 cm for all distances if not present
            d = meta.get("distances", np.full(ts.shape[1], 3.0))
            hbo, hbr = nlcore.compute_hbo_hbr(ts, wls, d)
            print("Successfully computed HbO and HbR.")
            print(f"HbO shape: {hbo.shape}")
            print(f"HbO range: {hbo.min():.4f} to {hbo.max():.4f}")
            print(f"HbR range: {hbr.min():.4f} to {hbr.max():.4f}")
        else:
            print("No wavelengths found in metadata.")
    except Exception as e:
        print(f"Error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    test_bids_snirf()
