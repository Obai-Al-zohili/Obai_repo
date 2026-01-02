# 🤖 Pretrained Model System

This folder contains all the files needed to run the trained CodeT5 bug-fixing model.

## 📁 Files Overview

### **Core System Files**
- `auto_fix.py` - Main script to run automatic bug fixing
- `load_model.py` - Loads the trained CodeT5 model and tokenizer
- `fix_blocks.py` - Contains the model inference logic
- `tester.py` - Runs pytest and parses test failures
- `simple_tester.py` - Simple test runner (fallback if pytest not available)

### **Model Files**
- `best_model.pt` - Your trained CodeT5 model weights

### **Test Files**
- `buggy_code.py` - Contains buggy Python functions to be fixed
- `test_buggy_code.py` - Pytest tests for the buggy functions
- `test_with_bugs.py` - Alternative test runner
- `test_model_directly.py` - Direct model testing script

## 🚀 How to Use

### **1. Run Automatic Bug Fixing**
```bash
cd pretrained
python auto_fix.py
```

This will:
- Load your trained model
- Run tests on `buggy_code.py`
- Attempt to fix any bugs found
- Show results

### **2. Test Model Directly**
```bash
python test_model_directly.py
```

This tests the model with simple Python code examples.

### **3. Run Tests Only**
```bash
python simple_tester.py
```

This runs the tests without attempting fixes.

## 🔧 System Requirements

- Python 3.8+
- PyTorch
- Transformers library
- pandas, openpyxl (for Excel files)
- pytest (optional, has fallback)

## 📊 Model Details

- **Base Model**: Salesforce/codet5-base
- **Training Data**: 49,704 Python bug-fix examples
- **Task**: Automatic Python bug fixing
- **Input**: Buggy Python code
- **Output**: Fixed Python code

## 🐛 Current Known Issues

The model may generate:
- Repetitive output
- Non-Python code in some cases
- Empty responses

**Recommendation**: Retrain with more conservative parameters if issues persist.

## 🔄 Retraining

If you need to retrain the model:
1. Go back to the parent directory
2. Run `CodeT5_Base.ipynb` with updated parameters
3. Copy the new `best_model.pt` to this folder

## 📝 Example Usage

```python
# Example of what the system does:

# Input (buggy_code.py):
def divide(a, b):
    if b == 0:
        return 0  # BUG: Should raise exception
    return a / b

# Expected Output (after auto_fix.py):
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
```

## 🎯 Success Criteria

The system works correctly when:
- Tests initially fail on `buggy_code.py`
- Model generates proper Python fixes
- Tests pass after applying fixes
- No syntax errors in generated code