# AI Commit Message Generator

**Automatic commit messages that never leave your machine.** Stage your changes and a small fine-tuned model suggests a [Conventional Commits](https://www.conventionalcommits.org) message right in VS Code's terminal. Type **Y** and it's committed.

```
$ git add .
Suggests:  feat: add subtract function
Commit with this message? [Y/N] y
✓ Committed 3f2a1bc  feat: add subtract function
```

Free, no account, no API key, no cloud — the model runs on your own GPU or CPU.

## What's in this repo

| | What | Where |
|---|---|---|
| **VS Code extension** | Suggestion after `git add`, Y/N, commit | [`vscode-extension/`](vscode-extension/) |
| **CLI tool (Beemo)** | Same model as a command-line tool for any terminal | [`src/commit_model/`](src/commit_model/) |
| **The model** | Qwen2.5-Coder-1.5B fine-tuned with LoRA, 4-bit GGUF (986 MB) | [`commit-model-lora/`](commit-model-lora/) |

## Get started

### VS Code extension

1. Open `vscode-extension/` and run `npm install && npm run compile`.
2. Press **F5** to launch the extension in a development VS Code window.
3. Click the toggle in the status bar to turn it on.
4. Open a **new** terminal, save your changes, and run `git add .`.

### Beemo (command line)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

git add .
beemo                                   # prints a suggested message
scripts/install_hook.sh . <model.gguf>  # or pre-fill git commit through a git hook
```

`--model-path` or `BEEMO_MODEL_PATH` points to a local `.gguf` file.

## How it works

```
CommitBench (real GitHub commits)
  → filter: Conventional Commits messages only, no lockfiles or generated files   ~45 000 examples
  → fine-tune Qwen2.5-Coder-1.5B-Instruct with LoRA (Kaggle, 2× T4, 2 epochs)
  → evaluate on 9 704 held-out commits against the base model and a majority baseline
  → merge the adapter, quantize to 4-bit GGUF with llama.cpp (no measurable quality loss)
  → VS Code extension / CLI: llama.cpp's llama-server runs it locally
```

## Results

On 9 704 held-out CommitBench commits:

| | Base Qwen | **Fine-tuned** | Always `fix:` baseline |
|---|---|---|---|
| Valid Conventional Commits format | 1.9% | **99.9%** | — |
| Right commit type | 0.9% | **67.3%** | 53.3% |
| BLEU | 0.5 | **19.4** | — |
| ROUGE-L | 0.022 | **0.328** | — |

Strong on `fix`, `docs` and `test`. The model leans toward `fix` (over half of the training data) and rarely picks `build`, `ci`, `perf` or `style`. Full results and per-type accuracy: [`results.md`](results.md).

## Evaluation

All evaluation scripts share the same prompt template and diff-filtering logic as training (`src/commit_model/diff_utils.py`).

**CommitBench test split** (9 704 held-out examples):

```bash
# With the 4-bit GGUF via Ollama (no GPU required):
python scripts/evaluate_ollama.py --limit 200

# With the LoRA adapter via BitsAndBytes (GPU required):
python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 200
```

Both scripts report: valid-format rate, type accuracy, BLEU, ROUGE-L, METEOR, per-type precision/recall/F1, confusion-matrix PNG, and a McNemar significance test.

**CommitSuite CMG benchmark** (1 000 curated examples across 7 languages):

```bash
# Requires Ollama running with the model loaded
python scripts/evaluate_commitsuite.py --limit 10   # smoke test
python scripts/evaluate_commitsuite.py              # full benchmark
```

## Repository layout

| Path | |
|---|---|
| [`notebooks/`](notebooks/) | Pipeline: `CommitBench_filter` → `fine-tuning_Kaggle` → `evaluate_Kaggle` → `merge_adapter_Kaggle` → `quantize_gguf_Kaggle` → `evaluate_quantized_Kaggle` |
| [`vscode-extension/`](vscode-extension/) | VS Code extension (TypeScript) and its unit and integration tests |
| [`src/commit_model/`](src/commit_model/) | CLI, engine, prompt building, and cleanup (Python) |
| [`scripts/`](scripts/) | `evaluate.py`, `evaluate_ollama.py`, `evaluate_commitsuite.py`, `install_hook.sh` |
| [`commit-model-lora/`](commit-model-lora/) | LoRA adapter weights and model card |
| [`hf_model_card/`](hf_model_card/) | Model card for the quantized GGUF |
| [`results.md`](results.md), [`plan.md`](plan.md) | Evaluation results and project roadmap |

## Development

```bash
# Extension
cd vscode-extension && npm install && npm run compile
npm run test:unit          # cleanup unit tests
npm run test:integration   # full workflow in a real VS Code window

# Python
python -m unittest tests.test_postprocess
```

## Licenses

- Extension code: MIT ([`vscode-extension/LICENSE`](vscode-extension/LICENSE))
- The model weights: **CC BY-NC 4.0** (non-commercial), inherited from training data **CommitBench** (Maximilian Schall et al., CC BY-NC 4.0)
- Base model **Qwen2.5-Coder-1.5B-Instruct**: Apache 2.0 (Alibaba Cloud)
- Inference engine **llama.cpp**: MIT
