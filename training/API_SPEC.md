# NeuroLumina Inference API — Integration Specification

> **For:** Full-Stack Developer (API team)  
> **From:** ML Scientist  
> **Purpose:** Document the input/output contract for serving the HybridCNNBiLSTM model

---

## Overview

The inference engine is loaded as a Python module at server startup. The API server calls `engine.predict(hbo, hbr)` for each inference request and returns serialised JSON results.

---

## 1. Model Loading (Server Startup)

```python
from inference import fNIRSInferenceEngine

# Load once when the server starts
engine = fNIRSInferenceEngine(
    model_path="models/model_scripted.pt",  # TorchScript model
    device="cpu",                            # or "cuda" if GPU available
    label_map={
        0: "0-back",
        1: "2-back",
        2: "3-back",
    },  # Optional: defaults to fNIRS2MW labels
)
```

**Initialisation cost:** ~1–2 seconds (model load + JIT compile)  
**Memory:** ~100–200 MB RAM for the model

---

## 2. Inference Request

### Input

```python
# hbo: numpy array of HbO concentrations
# Shape: (n_optodes,) or (n_optodes, n_timepoints)
# dtype: float32
# Unit: μM (micromolar)

# hbr: numpy array of HbR concentrations
# Same shape as hbo

result = engine.predict(hbo, hbr)
```

### Minimal input (single timepoint)
```python
hbo = np.array([1.2, 1.5, 1.1, ...], dtype=np.float32)      # (36,)
hbr = np.array([0.8, 0.9, 0.7, ...], dtype=np.float32)      # (36,)
```

### Full input (time series)
```python
hbo = np.random.randn(36, 300).astype(np.float32)            # (36, 300)
hbr = np.random.randn(36, 300).astype(np.float32)            # (36, 300)
```

---

## 3. Inference Response

### Standard response

```json
{
  "cognitive_load": {
    "class": 2,
    "label": "3-back",
    "confidence": 0.89
  },
  "timing_ms": {
    "preprocess": 2.1,
    "inference": 9.8,
    "total": 11.9
  }
}
```

### With logits (debug/analysis mode)

```json
{
  "cognitive_load": {
    "class": 2,
    "label": "3-back",
    "confidence": 0.89,
    "logits": [-1.23, 0.45, 2.67]
  },
  "timing_ms": {
    "preprocess": 2.1,
    "inference": 9.8,
    "total": 11.9
  }
}
```

---

## 4. REST API Design (Suggestion)

### POST /api/v1/predict

**Request:**
```json
{
  "hbo": [[1.2, 1.5, ...], [1.1, 1.3, ...], ...],
  "hbr": [[0.8, 0.9, ...], [0.7, 0.8, ...], ...],
  "return_logits": false,
  "label_map": "fnirs2mw"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "cognitive_load": {
      "class": 2,
      "label": "3-back",
      "confidence": 0.89
    },
    "timing_ms": {
      "preprocess": 2.1,
      "inference": 9.8,
      "total": 11.9
    }
  },
  "model": "hybrid_cnn_bilstm_v1",
  "version": "0.1.0"
}
```

### POST /api/v1/predict/batch

Handles multiple samples in one request.

**Request:**
```json
{
  "hbo": [[[1.2, ...], ...], [[1.3, ...], ...], ...],
  "hbr": [[[0.8, ...], ...], [[0.9, ...], ...], ...],
  "return_logits": false
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "sample_id": 0,
      "cognitive_load": {"class": 2, "label": "3-back", "confidence": 0.89},
      "timing_ms": {"preprocess": 2.1, "inference": 9.8, "total": 11.9}
    },
    ...
  ]
}
```

---

## 5. Error Handling

### Common Errors

| Scenario | HTTP Status | Error Code | Message |
|----------|------------|------------|---------|
| Invalid input shape | 400 | `INVALID_SHAPE` | "HbO shape (36, 300) expected, got (36, 250)" |
| Missing data | 400 | `MISSING_DATA` | "Both hbo and hbr are required" |
| Type mismatch | 400 | `TYPE_ERROR` | "Expected float32, got float64" |
| Model not loaded | 503 | `MODEL_UNAVAILABLE` | "Model not initialised" |
| NaN values | 400 | `NAN_DETECTED` | "Input contains NaN values" |

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SHAPE",
    "message": "HbO shape (36, 300) expected, got (36, 250)"
  }
}
```

---

## 6. Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| P50 latency | <15 ms | Single inference, CPU |
| P99 latency | <50 ms | Single inference, CPU |
| Throughput | >100 req/s | Single CPU core |
| Batch throughput | >500 samples/s | Batch of 32 |
| Model load time | <3 s | At server startup |
| Memory (model) | <200 MB | RAM |
| Memory (inference) | <500 MB | Peak |

---

## 7. Preprocessing (Server-Side)

The `Preprocessor` class handles input normalisation. It should be fitted once on training data stats:

```python
from inference import Preprocessor

# At training time, save normalisation stats:
preprocessor = Preprocessor()
preprocessor.fit(training_data)
preprocessor.save_normalisation("models/normalisation.npz")

# At inference time, load them:
preprocessor = Preprocessor()
preprocessor.load_normalisation("models/normalisation.npz")
```

The preprocessor is automatically called inside `engine.predict()`.

---

## 8. Thread Safety

The inference engine is **thread-safe**:
- `model.eval()` is called once at init
- `torch.no_grad()` is applied per predict call
- No mutable shared state during inference
- Multiple threads can call `predict()` concurrently

For high-throughput scenarios, use a model instance per worker thread
or wrap in a thread pool.

---

## 9. File Locations

```
/home/team/shared/training/
├── inference.py          # Inference engine class
├── export.py             # TorchScript export script
├── model.py              # Model architecture definitions
├── datamodule.py         # Data loading (for reference)
├── MODEL_CARD.md         # Full model card with benchmarks
└── requirements.txt      # Dependencies
```

---

## 10. Quick Start for API Integration

```python
# 1. Install dependencies
# pip install torch numpy

# 2. Export a trained model
# python export.py --checkpoint checkpoints/best_model.pt --output models/

# 3. Test inference
from inference import fNIRSInferenceEngine, Preprocessor
import numpy as np

engine = fNIRSInferenceEngine("models/model_scripted.pt")

# Load normalisation stats
preprocessor = Preprocessor()
preprocessor.load_normalisation("models/normalisation.npz")
engine.preprocessor = preprocessor

# Simulate a request
hbo = np.random.randn(36, 300).astype(np.float32)
hbr = np.random.randn(36, 300).astype(np.float32)
result = engine.predict(hbo, hbr)

print(result)
# {
#   "cognitive_load": {"class": 2, "label": "3-back", "confidence": 0.89},
#   "timing_ms": {"preprocess": 2.1, "inference": 9.8, "total": 11.9}
# }
```