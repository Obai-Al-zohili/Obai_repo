# config.py
import torch
from pathlib import Path

# ============================================================
# 🧠 Model configuration
# ============================================================

# Directory where this config.py lives
BASE_DIR = Path(__file__).resolve().parent

# HuggingFace base model (used when loading state_dict)
BASE_MODEL = "Salesforce/codet5-base"

# ✅ Fine-tuned weights (saved via torch.save(model.state_dict()))
# File location: bug2_qlura/best_model.pt
FINETUNED_WEIGHTS = BASE_DIR.parent / "best_model.pt"

# Maximum repair iterations
MAX_ITER = 3

# ============================================================
# 💻 Device configuration
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================================
# 🩹 Patch markers (used by repair agent)
# ============================================================

PATCH_MARKER_START = "PATCH-START"
PATCH_MARKER_END = "PATCH-END"

# ============================================================
# 📐 Tokenization (⚠ MUST match training)
# ============================================================

MAX_INPUT_LEN = 192
MAX_TARGET_LEN = 192

# ============================================================
# 💾 Model loading strategy
# ============================================================

# You trained and saved using:
# torch.save(model.state_dict(), "best_model.pt")
# → This means ONLY weights were saved (not full model)
FULL_MODEL_SAVED = False
