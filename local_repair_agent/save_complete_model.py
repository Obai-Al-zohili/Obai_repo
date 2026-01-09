#!/usr/bin/env python3
# save_complete_model.py - Convert state_dict to complete model

import torch
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def save_complete_model():
    """
    Load the current best_model.pt (state_dict) and save as complete model
    This eliminates the need to download CodeT5-base every time
    """
    BASE_MODEL = "Salesforce/codet5-base"
    STATE_DICT_PATH = "../best_model.pt"
    COMPLETE_MODEL_PATH = "../best_model_complete.pt"
    
    print("🔄 Converting state_dict to complete model...")
    
    # Check if state_dict exists
    if not os.path.exists(STATE_DICT_PATH):
        print(f"❌ State dict not found: {STATE_DICT_PATH}")
        return False
    
    try:
        # Load tokenizer and base model (one-time download)
        print("📦 Loading base model and tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)
        
        # Load your trained weights
        print("🧠 Loading trained weights...")
        state_dict = torch.load(STATE_DICT_PATH, map_location="cpu")
        model.load_state_dict(state_dict, strict=False)
        
        # Save complete model (includes architecture + weights)
        print("💾 Saving complete model...")
        torch.save({
            'model': model,
            'tokenizer': tokenizer,
            'config': model.config
        }, COMPLETE_MODEL_PATH)
        
        # Check file sizes
        original_size = os.path.getsize(STATE_DICT_PATH) / (1024 * 1024)
        complete_size = os.path.getsize(COMPLETE_MODEL_PATH) / (1024 * 1024)
        
        print(f"✅ Complete model saved!")
        print(f"📊 Original size: {original_size:.1f} MB")
        print(f"📊 Complete size: {complete_size:.1f} MB")
        print(f"📁 Saved to: {COMPLETE_MODEL_PATH}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = save_complete_model()
    if success:
        print("\n💡 Now you can:")
        print("1. Update config.py: Set FULL_MODEL_SAVED = True")
        print("2. Update config.py: Set FINETUNED_WEIGHTS = '../best_model_complete.pt'")
        print("3. Run repair agent without needing CodeT5-base downloads!")
    else:
        print("\n❌ Failed to create complete model")