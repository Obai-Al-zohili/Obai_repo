# fix_blocks.py
import torch
from typing import Dict


# =====================================================
# 🧠 Prompt Builder
# =====================================================
def build_error_prompt(error_info: Dict, code: str) -> str:
    """
    Build a prompt that matches the training format.
    Since the model was trained on direct buggy_code -> fixed_code,
    we should just return the buggy code without complex instructions.
    """
    # The model was trained to directly translate buggy code to fixed code
    # So we just return the buggy code as input
    return code.strip()


# =====================================================
# 🔧 Model Call
# =====================================================
def fix_code_with_model(model, tokenizer, prompt: str) -> str:
    """
    Send prompt to LLM and return fixed code.
    Updated to match the training format (direct code-to-code translation).
    """
    print(f"🔍 Input code length: {len(prompt)} characters")
    print(f"🔍 Input code preview: {prompt[:200]}...")

    # Use the same parameters as training: max_input_len=256
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=256,  # Match training MAX_INPUT_LEN
        padding=True
    )

    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=128,  # Match training MAX_TARGET_LEN
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # Decode only the generated part (skip input tokens)
    input_length = inputs['input_ids'].shape[1]
    generated_ids = output_ids[0][input_length:]
    
    decoded = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True
    )

    print(f"🔍 Raw model output length: {len(decoded)} characters")
    print(f"🔍 Raw model output: {decoded}")

    # The model should directly output the fixed code
    fixed_code = decoded.strip()

    print(f"🔍 Final fixed code: {fixed_code}")
    return fixed_code
