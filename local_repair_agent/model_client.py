# model_client.py

import os
import torch
import difflib
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import LoraConfig, get_peft_model
import config


class LocalModelClient:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.load_model()

    def load_model(self):
        if not os.path.exists(config.FINETUNED_WEIGHTS):
            raise RuntimeError(f"Fine-tuned weights not found: {config.FINETUNED_WEIGHTS}")

        print("📦 Loading CodeT5-base...")
        self.tokenizer = AutoTokenizer.from_pretrained(config.BASE_MODEL)

        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            config.BASE_MODEL,
            torch_dtype=torch.float16 if config.DEVICE.type == "cuda" else torch.float32,
        )

        # 🔗 MUST match training LoRA config
        lora_config = LoraConfig(
            r=128,
            lora_alpha=64,
            lora_dropout=0.05,
            bias="none",
            task_type="SEQ_2_SEQ_LM",
            target_modules=["q", "k", "v", "o", "wi", "wo"],
        )

        self.model = get_peft_model(base_model, lora_config)

        print("📥 Loading fine-tuned LoRA weights...")
        state_dict = torch.load(config.FINETUNED_WEIGHTS, map_location="cpu")

        # ✅ CORRECT: strict=False for LoRA
        missing, unexpected = self.model.load_state_dict(state_dict, strict=False)

        if unexpected:
            raise RuntimeError(f"Unexpected keys in state_dict: {unexpected}")

        self.model.to(config.DEVICE)
        self.model.eval()

        print("✅ CodeT5 + LoRA loaded")
        print(f"🧠 Device: {config.DEVICE}")

    def generate_fix(self, buggy_code: str) -> str:
        inputs = self.tokenizer(
            buggy_code,
            return_tensors="pt",
            truncation=True,
            max_length=config.MAX_INPUT_LEN,
            padding=True,
        )

        inputs = {k: v.to(config.DEVICE) for k, v in inputs.items()}

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=config.MAX_TARGET_LEN,
                num_beams=4,
                do_sample=False,
                early_stopping=True,
            )

        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

    def create_unified_diff(self, original: str, fixed: str, path: str) -> str:
        return "".join(
            difflib.unified_diff(
                original.splitlines(True),
                fixed.splitlines(True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm="",
            )
        )


_model_client = None


def get_model_client():
    global _model_client
    if _model_client is None:
        _model_client = LocalModelClient()
    return _model_client


def call_llm_propose_patch(file_path, file_contents, failing_test, trace):
    print("🤖 Local CodeT5 model generating patch...")
    client = get_model_client()

    fixed_code = client.generate_fix(file_contents)
    patch = client.create_unified_diff(file_contents, fixed_code, file_path)

    if not patch.strip():
        print("⚠️ No changes generated")
        return ""

    print("✅ Patch generated")
    return patch
