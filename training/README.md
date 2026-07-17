# NeuroLumina Training Pipeline

> **ML Scientist — Baseline Models for Brain-State Classification**

---

## Overview

This directory contains the neural network models and training pipeline for NeuroLumina's premium tier: pre-trained deep-learning models that classify brain states (cognitive load, attention, fatigue, recovery) from HD-fNIRS signals.

---

## Architecture: HybridCNNBiLSTM

### Model Design

```
Input: (batch, n_channels, n_timepoints)
  │
  ├── Conv1D (64 filters, kernel=5, padding='same')
  ├── BatchNorm1D + ReLU
  ├── MaxPool1D (stride=2)
  │
  ├── Conv1D (128 filters, kernel=3, padding='same')
  ├── BatchNorm1D + ReLU
  ├── MaxPool1D (stride=2)
  │
  ├── Permute: (B, C, T) → (B, T, C)
  │
  ├── BiLSTM (hidden=128, layers=2, bidirectional)
  ├── Last timestep → (B, 256)
  │
  ├── Dense (64) + ReLU
  ├── Dropout (0.4)
  └── Dense (n_classes) → logits
```

### Parameter Count

| Component | Parameters |
|-----------|-----------|
| Conv1D Block 1 | ~4,800 |
| Conv1D Block 2 | ~24,700 |
| BiLSTM (2 layers, bidirectional) | ~396,000 |
| Classifier head | ~16,500 |
| **Total** | **~442,000** |

### Design Rationale

- **Conv1D layers** learn local temporal patterns in the haemodynamic response (HRF shape typically 5–10 s). Two blocks with progressively more filters extract hierarchical temporal features.
- **BatchNorm** stabilises training and reduces internal covariate shift.
- **BiLSTM** captures long-range temporal dependencies bidirectionally — important for fNIRS where cognitive-state-related haemodynamic changes unfold over 15–30 s windows.
- **Dropout (0.4)** prevents overfitting, especially important given the typical small-sample neuroscience dataset sizes (N=15–30 subjects).
- **He initialisation** matches the ReLU activation function.

### Variants

| Model | Input Shape | When to Use |
|-------|------------|-------------|
| `HybridCNNBiLSTM` | (B, ch, T) | General-purpose classification |
| `SpatiotemporalCNN` | (B, 2, T, H, W) | When optode positions are known (2D montage) |
| `MultiTaskModel` | (B, ch, T) | When predicting multiple targets (load + fatigue + attention) |

---

## Training Configuration

### Default Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Optimizer | AdamW | Better weight decay handling than Adam |
| Learning rate | 1×10⁻³ | Standard starting point for CNN-LSTM |
| LR schedule | ReduceLROnPlateau (factor=0.5, patience=5) | Reduces LR when validation plateaus |
| Weight decay | 1×10⁻⁴ | Mild L2 regularisation |
| Batch size | 32 | Memory-efficient, stable gradients |
| Epochs | 30–100 | Early stopping (patience=15) |
| Dropout | 0.4 | Prevents overfitting |
| Loss | CrossEntropy | Standard for multi-class classification |
| Weight init | He normal (Kaiming) | Matches ReLU activation |

### Expected Baseline Metrics (Synthetic Data)

Since the mock data generator produces well-separated class distributions (amplitude scales with class label), the model should achieve high accuracy quickly:

| Metric | Expected (Mock) | Notes |
|--------|----------------|-------|
| Train accuracy | >95% | Model easily fits synthetic patterns |
| Val accuracy (holdout) | >85% | Generalises to held-out epochs |
| Val accuracy (LOSO) | >80% | Generalises to held-out subjects |
| Train loss | <0.20 | Cross-entropy converges quickly |
| Val loss | <0.40 | Slightly higher due to held-out data |

### Target Benchmarks (Real Data)

| Dataset | Metric | Target | Stretch |
|---------|--------|--------|---------|
| fNIRS2MW (3-class) | Accuracy | ≥80% | ≥86% |
| fNIRS2MW (3-class) | F1-macro | ≥0.78 | ≥0.85 |
| Mental Arithmetic (binary) | Accuracy | ≥85% | ≥90% |
| Fatigue (regression) | RMSE | ≤0.15 | ≤0.10 |

---

## File Structure

```
training/
├── datamodule.py      # fNIRS DataModule (dataset loading + CV)
├── model.py           # Model architectures (HybridCNNBiLSTM + variants)
├── train.py           # Training script with CLI
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── checkpoints/       # Saved model checkpoints (created by train.py)
    ├── best_model.pt
    ├── epoch_10.pt
    ├── history.json
    └── args.json
```

---

## Usage

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install nlcore (for real SNIRF data)
pip install -e /path/to/nlcore
```

### Train on Synthetic Data
```bash
cd /home/team/shared/training
python train.py --dataset mock --epochs 30 --batch_size 32
```

### Train on fNIRS2MW (with real data)
```bash
python train.py \
    --dataset fnirs2mw \
    --snirf_paths /path/to/fNIRS2MW/sub-*.snirf \
    --val_strategy loso \
    --epochs 100 \
    --lr 1e-3
```

### Train on Mental Arithmetic
```bash
python train.py \
    --dataset mental_arithmetic \
    --snirf_paths /path/to/mental_arithmetic/*.snirf \
    --val_strategy kfold \
    --n_folds 5 \
    --epochs 80
```

### Resume from Checkpoint
```bash
python train.py --resume checkpoints/epoch_20.pt
```

### Monitor Training
Training logs are printed to stdout. Checkpoints and metrics are saved to `checkpoints/`:
- `best_model.pt` — best model by validation accuracy
- `history.json` — per-epoch loss and accuracy
- `args.json` — training configuration

---

## Integration with nlcore

The DataModule integrates with the `nlcore` package for reading SNIRF files and applying preprocessing:

```python
from nlcore import load_snirf
from nlcore.physiology.chromophore import compute_hbo_hbr
from nlcore.preprocessing.filtering import bandpass_filter
```

When `nlcore` is unavailable, the DataModule falls back to its built-in `MockfNIRSGenerator`,
which produces realistic synthetic fNIRS data with pink noise and HRF-shaped responses.

---

## Next Steps (Post-Training)

1. **Export to ONNX** for inference: `torch.onnx.export(model, dummy_input, "model.onnx")`
2. **Quantise** to INT8 for <50 MB model size
3. **Benchmark inference speed** (<100 ms per 10 s window)
4. **Cross-dataset validation** (train on fNIRS2MW, test on OpenfNIRS)
5. **Deploy** via API (Full-Stack Developer)

---

## References

- Hinrichs et al. (2024) — Deep Learning for fNIRS-Based Cognitive Workload Classification
- Rjoub et al. (2023) — Hybrid CNN-BiLSTM for fNIRS-Based Brain-Computer Interface
- Bulgheroni et al. (2022) — fNIRS2MW Dataset (Scientific Data)
- See `/home/team/shared/ml-architecture-plan.md` for full architecture details
