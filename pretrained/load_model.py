# load_model.py
import torch
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ================================
# 🔧 CONFIG
# ================================
BASE_MODEL = "Salesforce/codet5-base"
FINETUNED_WEIGHTS = "best_model.pt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Check if fine-tuned weights exist
if not os.path.exists(FINETUNED_WEIGHTS):
    print(f"❌ Fine-tuned weights not found: {FINETUNED_WEIGHTS}")
    print("Please run the training notebook first to create the model weights.")
    exit(1)

# ================================
# 🧠 Load tokenizer (BASE MODEL)
# ================================
try:
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
except:
    print("❌ Model not found locally. Please ensure the model is downloaded first.")
    print("You can download it by running the CodeT5_Base.ipynb notebook.")
    exit(1)

# ================================
# 🧠 Load base model
# ================================
try:
    model = AutoModelForSeq2SeqLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        local_files_only=True
    )
except:
    print("❌ Model not found locally. Please ensure the model is downloaded first.")
    print("You can download it by running the CodeT5_Base.ipynb notebook.")
    exit(1)

# ================================
# 🔁 Load fine-tuned weights
# ================================
try:
    state_dict = torch.load(FINETUNED_WEIGHTS, map_location="cpu")
    model.load_state_dict(state_dict, strict=False)
    
    model.to(device)
    model.eval()
    
    print("✅ CodeT5-base loaded + fine-tuned weights applied")
    print(f"🧠 Device: {device}")
except Exception as e:
    print(f"❌ Error loading fine-tuned weights: {e}")
    exit(1)