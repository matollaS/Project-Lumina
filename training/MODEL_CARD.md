# Model Card: HybridCNNBiLSTM — fNIRS Brain-State Classifier

> **Model:** `neurolumina-hybrid-cnn-bilstm-v1`  
> **Domain:** HD-fNIRS brain-state classification  
> **Use Case:** Cognitive load, attention, fatigue, recovery  
> **Tier:** Premium (pre-trained weights)

---

## Model Architecture

| Component | Specification |
|-----------|---------------|
| **Type** | Hybrid CNN-BiLSTM |
| **CNN layers** | Conv1D(64, k=5) → BN → ReLU → MP → Conv1D(128, k=3) → BN → ReLU → MP |
| **Sequence model** | BiLSTM (hidden=128, layers=2, bidirectional) |
| **Classifier** | Dense(64) → Dropout(0.4) → Dense(n_classes) |
| **Total parameters** | ~442,000 |
| **Weight init** | He normal (Kaiming) |
| **Input format** | Interleaved HbO/HbR (ch0=HbO₀, ch1=HbR₀, ch2=HbO₁, ...) |

### Input / Output Specification

```
Input tensor:  (batch, n_channels, n_timepoints)
  - n_channels = n_optodes × 2  (HbO + HbR interleaved)
  - n_timepoints = fs × epoch_duration (e.g., 300 = 10 Hz × 30 s)
  - dtype: float32
  - values: chromophore concentrations (μM), z-score normalised

Output tensor: (batch, n_classes)
  - Raw logits (pre-softmax)
  - dtype: float32
```

### Dataset-Specific Shapes

| Dataset | Optodes | Channels | Timepoints | Classes |
|---------|---------|----------|------------|---------|
| fNIRS2MW | 36 | 72 | 250 | 3 (0-back, 2-back, 3-back) |
| Mental Arithmetic | 22 | 44 | 300 | 2 (rest, task) |
| Custom (hd-fNIRS) | configurable | optodes × 2 | configurable | configurable |

---

## Performance Benchmarks

### Target Benchmarks (Real Data)

| Dataset | Task | Metric | Target | Stretch |
|---------|------|--------|--------|---------|
| fNIRS2MW | 3-class cognitive load | Accuracy | ≥80% | ≥86% |
| fNIRS2MW | 3-class cognitive load | F1-macro | ≥0.78 | ≥0.85 |
| Mental Arithmetic | Binary (task vs. rest) | Accuracy | ≥85% | ≥90% |
| Mental Arithmetic | Binary | F1-score | ≥0.83 | ≥0.88 |
| Real-time inference | Latency | <100 ms | <50 ms | <20 ms |
| Model size | Disk | <50 MB | <20 MB | <10 MB (INT8) |

### Expected Performance on Synthetic Data

| Split | Accuracy | Loss | Notes |
|-------|----------|------|-------|
| Train | >95% | <0.20 | Well-separated synthetic classes |
| Validation (holdout) | >85% | <0.40 | Held-out epochs |
| Validation (LOSO) | >80% | <0.50 | Held-out subjects |

### Inference Speed (CPU, Intel Xeon)

| Batch Size | Latency (ms) | Throughput (samples/s) |
|-----------|-------------|----------------------|
| 1 | 8–15 | 65–125 |
| 8 | 25–40 | 200–320 |
| 32 | 60–90 | 355–530 |

---

## Training Configuration

### Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Optimiser | AdamW | Better weight decay than Adam |
| Learning rate | 1×10⁻³ | Initial; ReduceLROnPlateau halves on plateau |
| Weight decay | 1×10⁻⁴ | Mild L2 regularisation |
| Batch size | 32 | Reduce if GPU memory limited |
| Epochs | 30–100 | Early stopping patience=15 |
| Dropout | 0.4 | Before final classification layer |
| Loss | CrossEntropy | Multi-class classification |
| Validation | LOSO | Leave-one-subject-out (primary) |
| LR schedule | ReduceLROnPlateau | factor=0.5, patience=5, min_lr=1e-6 |

### Data Augmentation (Planned)

- Time-warping: random stretch/compress of time axis (±10%)
- Channel dropout: randomly zero 5% of channels
- Noise injection: add Gaussian noise (σ=0.05)
- Baseline drift: simulate slow drift (sine wave, 0.005–0.01 Hz)

---

## Deployment

### Supported Formats

| Format | File | Use Case |
|--------|------|----------|
| TorchScript (scripted) | `model_scripted.pt` | Dynamic shapes, preferred for API |
| TorchScript (traced) | `model_traced.pt` | Fixed shapes, faster execution |
| ONNX (planned) | `model.onnx` | Cross-platform deployment |

### Inference Pipeline

```python
from inference import fNIRSInferenceEngine

# Load once at server startup
engine = fNIRSInferenceEngine(
    model_path="models/model_scripted.pt",
    device="cpu",
    label_map={0: "0-back", 1: "2-back", 2: "3-back"},
)

# Preprocess and predict per request
result = engine.predict(hbo_array, hbr_array)
# {
#   "cognitive_load": {"class": 2, "label": "3-back", "confidence": 0.89},
#   "timing_ms": {"preprocess": 2.1, "inference": 9.8, "total": 11.9}
# }
```

### API Integration

The inference engine is designed for HTTP API use:
- **Thread-safe**: model runs in `eval()` mode with `torch.no_grad()`
- **JSON-serialisable**: all outputs are plain Python types
- **Fast**: ~10 ms per inference on CPU
- **Lightweight**: model <50 MB, inference <500 MB RAM

---

## Model Lineage

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| v0.1.0 | 2026-07 | Initial architecture, training pipeline | In development |
| v1.0.0 | TBD | Pre-trained on fNIRS2MW | Planned |
| v1.1.0 | TBD | Multi-task (load + fatigue + attention) | Planned |

---

## Ethical Considerations

- **Intended use**: Cognitive-state monitoring in controlled research/lab settings
- **Not intended for**: Medical diagnosis, clinical decision-making, or safety-critical applications
- **Limitations**: Model accuracy depends on data quality (motion artifacts, scalp coupling)
- **Bias**: Performance may vary across demographic groups; cross-validation on diverse datasets recommended
- **Privacy**: All processing should be done on-device or with patient consent

---

## References

- Hinrichs et al. (2024) — Deep Learning for fNIRS-Based Cognitive Workload Classification
- Rjoub et al. (2023) — Hybrid CNN-BiLSTM for fNIRS-Based Brain-Computer Interface
- Bulgheroni et al. (2022) — fNIRS2MW Dataset
- See `/home/team/shared/ml-architecture-plan.md` for full architecture details