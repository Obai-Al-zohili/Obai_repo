#!/usr/bin/env python3
"""
Test the trained model directly with simple Python code
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def test_model_directly():
    """Test the model with a simple Python bug"""
    
    print("🧪 Testing trained model directly...")
    
    # Load model and tokenizer
    try:
        BASE_MODEL = "Salesforce/codet5-base"
        FINETUNED_WEIGHTS = "best_model.pt"
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        
        # Load base model
        model = AutoModelForSeq2SeqLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32
        )
        
        # Load fine-tuned weights
        state_dict = torch.load(FINETUNED_WEIGHTS, map_location="cpu")
        model.load_state_dict(state_dict, strict=False)
        
        model.to(device)
        model.eval()
        
        print("✅ Model loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Test with simple Python bugs
    test_cases = [
        # Simple division by zero
        "def divide(a, b):\n    return a / b",
        
        # Simple index error
        "def first(lst):\n    return lst[0]",
        
        # Simple type conversion
        "def to_int(s):\n    return int(s)"
    ]
    
    print(f"\n🔍 Testing {len(test_cases)} simple cases...")
    
    for i, buggy_code in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {buggy_code}")
        
        try:
            # Tokenize input (using training parameters)
            inputs = tokenizer(
                buggy_code,
                return_tensors="pt",
                truncation=True,
                max_length=384,  # Match training
                padding=True
            )
            
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate output
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=128,  # Match training
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )
            
            # Decode only the generated part
            input_length = inputs['input_ids'].shape[1]
            generated_ids = output_ids[0][input_length:]
            
            decoded = tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            print(f"Output: {decoded}")
            
            # Check if output looks like Python
            if any(keyword in decoded.lower() for keyword in ['def ', 'if ', 'return', 'raise', 'except']):
                print("✅ Output looks like Python code")
            else:
                print("❌ Output doesn't look like Python code")
                
        except Exception as e:
            print(f"❌ Error during generation: {e}")
    
    # Test model info
    print(f"\n📊 Model Info:")
    print(f"   Device: {device}")
    print(f"   Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"   Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

if __name__ == "__main__":
    test_model_directly()