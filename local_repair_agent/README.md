# Local Model Repair Agent

This is a modified version of the original repair agent that uses a local fine-tuned CodeT5 model (`best_model.pt`) instead of Gemini AI for generating code fixes.

## Key Differences from Original

- **No API Keys Required**: Uses local model instead of Gemini AI
- **Offline Operation**: Works completely offline once model is loaded
- **Direct Code Translation**: Model directly translates buggy code to fixed code
- **Faster Inference**: No network calls to external APIs

## Prerequisites

1. **Trained Model**: Ensure `best_model.pt` exists in the parent directory
2. **Base Model**: CodeT5-base model (will be downloaded automatically if not cached)
3. **Python Dependencies**: 
   - torch
   - transformers
   - pytest (for running tests)
   - git (for applying patches)

## Installation

```bash
# Install required packages
pip install torch transformers pytest

# Ensure you're in a git repository
git init  # if not already a git repo
```

## Usage

```bash
cd local_repair_agent
python main.py
```

## How It Works

1. **Test Execution**: Runs pytest to identify failing tests
2. **Error Analysis**: Parses test output to extract failing file and error details
3. **Code Generation**: Uses the local CodeT5 model to generate fixed code
4. **Patch Creation**: Creates unified diff patches from original vs fixed code
5. **Patch Application**: Applies patches using `git apply` and commits changes
6. **Iteration**: Repeats until tests pass or max iterations reached

## Configuration

Edit `config.py` to modify:
- `BASE_MODEL`: Base CodeT5 model name
- `FINETUNED_WEIGHTS`: Path to your trained model
- `MAX_ITER`: Maximum repair iterations
- `MAX_INPUT_LEN`: Maximum input sequence length
- `MAX_TARGET_LEN`: Maximum output sequence length

## File Structure

- `config.py`: Configuration settings
- `model_client.py`: Local model loading and inference
- `main.py`: Main repair loop
- `patcher.py`: Patch application utilities
- `tester.py`: Test execution and failure parsing
- `README.md`: This documentation

## Troubleshooting

### Model Loading Issues
- Ensure `best_model.pt` exists and is accessible
- Check that you have sufficient GPU/CPU memory
- Verify transformers library version compatibility

### Patch Application Issues
- Ensure you're in a git repository
- Check that target files are not locked or read-only
- Verify git is installed and accessible

### Test Detection Issues
- Ensure pytest is installed
- Check that test files are in `tests/` directory
- Verify test files follow pytest naming conventions

## Performance Notes

- **GPU Recommended**: Model inference is faster on GPU
- **Memory Usage**: Model requires ~1-2GB RAM/VRAM
- **Inference Time**: Typically 1-5 seconds per fix generation

## Comparison with Original

| Feature | Original (Gemini) | Local Model |
|---------|------------------|-------------|
| API Key | Required | Not needed |
| Internet | Required | Not required |
| Cost | Per API call | One-time setup |
| Speed | Network dependent | Local inference |
| Customization | Limited | Full control |
| Privacy | Data sent to Google | Fully local |