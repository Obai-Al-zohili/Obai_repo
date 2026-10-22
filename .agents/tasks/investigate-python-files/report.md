# Python & Notebook File Investigation Report
**Project:** Offhand / Beemo — AI-powered git commit message generator  
**Workspace:** `c:\Users\ASUSD\Desktop\Programing\seniorProject\OffHand`

---

## Summary

This project is an **AI commit message generator** with two user-facing products: an **Offhand VS Code extension** and a **Beemo CLI tool**. Both run a fine-tuned 4-bit LLM (Qwen2.5-Coder-1.5B) locally to suggest [Conventional Commits](https://www.conventionalcommits.org)-style messages from staged diffs.

The Python code covers four distinct layers:
1. **Core library** (`src/commit_model/`) — the inference engine, diff processing, and message cleanup used by both the CLI and as a reference implementation for the VS Code extension.
2. **Training pipeline** (`notebooks/`) — Kaggle-hosted Jupyter notebooks that filter training data, fine-tune the model, merge the adapter, quantize to GGUF, and measure quality.
3. **Evaluation scripts** (`scripts/`) — standalone Python scripts for measuring quality against held-out test data, targeting either the fine-tuned adapter (GPU) or a deployed Ollama instance.
4. **CommitSuite evaluation** (`CommitSuite/`) — separate benchmark evaluation scripts that score a commit-message-generation model against a custom dataset using both traditional NLP metrics and an LLM-as-judge approach.

All files share the same core ideas: the **Conventional Commits prefix** taxonomy (`feat`, `fix`, `refactor`, etc.), the same **diff truncation policy** (`MAX_DIFF_CHARS=4000`, `MAX_FILES_PER_DIFF=6`, lockfile exclusions), the same **prompt template** (`"Write a Conventional Commits message for this diff.\n\n{diff}\n\nCommit message:"`), and the same **sequence length** (`SEQ_LEN=768`).

---

## Component Breakdown

### 1. Core Library — `src/commit_model/`

| File | Purpose |
|---|---|
| `__init__.py` | Empty package marker |
| `diff_utils.py` | Diff filtering, truncation, and prompt formatting (shared by training & inference) |
| `postprocess.py` | Cleans model output — strips placeholder tokens (`<I>`, `<URL>`, `<EMAIL>`, `<HASH>`), normalizes casing |
| `engine.py` | Downloads + manages `llama-server` (llama.cpp) and runs inference via its HTTP API |
| `cli.py` | CLI entry point (`beemo` command) — reads `git diff --staged`, calls engine, prints or writes to a prepare-commit-msg hook file |

#### How they connect

```
cli.py
  ├── diff_utils.build_diff()      ← filter & truncate the staged diff
  └── engine.Engine.generate()
        ├── engine.fit_prompt()    ← via diff_utils.fit_prompt()
        └── postprocess.clean_message()   ← clean the model output
```

**`diff_utils.py`** is the most cross-cutting file. Its constants (`GENERATED_FILE_PATTERNS`, `LOW_CONTENT_STOPLIST`, `MAX_DIFF_CHARS`, `SEQ_LEN`, `PROMPT_TEMPLATE`) are duplicated verbatim in several notebooks because those notebooks are designed to run standalone on Kaggle without importing the local package.

**`engine.py`** handles the full lifecycle of `llama-server`:
- Detects platform (Windows/Linux/macOS) and architecture (x64/arm64)
- Downloads the appropriate llama.cpp binary release (`LLAMA_TAG = "b11476"`)
- Downloads the GGUF model from Hugging Face (`hf:Jess2005/commit-model-CLI/commit-model-Q4_K_M.gguf` by default)
- Starts the server on a free port, waits for it to be healthy, and tears it down on exit
- Exposes a `ServerTokenizer` that wraps the server's `/tokenize` and `/detokenize` endpoints so `diff_utils.fit_prompt` can use it

**`postprocess.py`** mirrors `vscode-extension/src/postprocess.ts`. The shared test cases live in `vscode-extension/test/clean-cases.json`, ensuring Python and TypeScript stay in sync.

---

### 2. Tests — `tests/test_postprocess.py`

Loads the shared `clean-cases.json` from the VS Code extension's test folder and runs every case through Python's `clean_message()`. This is a cross-language parity test: if the TypeScript and Python implementations diverge, this test catches it.

Run with: `python -m unittest tests.test_postprocess`

---

### 3. Training Pipeline — `notebooks/`

These notebooks are designed to run sequentially on **Kaggle** with GPU T4 accelerators. They are self-contained (they re-implement `diff_utils` logic inline) so they can run without the local `commit_model` package being installed.

| Notebook | Step | What it does |
|---|---|---|
| `CommitBench_filter.ipynb` | 1 — Data prep | Downloads `Maxscha/commitbench` from Hugging Face, filters to Conventional Commits messages, drops low-quality/lockfile entries, writes `train.jsonl` / `validation.jsonl` / `test.jsonl` |
| `fine-tuning_Kaggle.ipynb` | 2 — Training | LoRA fine-tunes `Qwen2.5-Coder-1.5B-Instruct` on the filtered dataset using `SFTTrainer` (TRL). Trains on commit messages only (`completion_only_loss=True`). Saves and zips the adapter (~70MB) |
| `evaluate_Kaggle.ipynb` | 3 — FP32 eval | Runs base model and base+adapter in parallel (one per T4), scores valid format %, type accuracy, BLEU, ROUGE-L |
| `merge_adapter_Kaggle.ipynb` | 4 — Merge | Folds the LoRA adapter into the base weights (`merge_and_unload()`), saves as bf16 HF model (~3.1GB) |
| `quantize_gguf_Kaggle.ipynb` | 5 — Quantize | Builds llama.cpp, converts merged model to bf16 GGUF, quantizes to `Q4_K_M` (~1GB), writes `Modelfile` for Ollama, runs a quality check |
| `evaluate_quantized_Kaggle.ipynb` | 6 — Q4 eval | Runs the GGUF model via llama-server on Kaggle GPUs, compares 4-bit vs fp32 scores with McNemar significance test |

**Data flow:**  
`CommitBench_filter` → `*.jsonl` files → `fine-tuning` → `adapter` → `evaluate_Kaggle` (scores) + `merge_adapter` → merged model → `quantize_gguf` → `.gguf` + `Modelfile` → `evaluate_quantized` (final scores)

---

### 4. Evaluation Scripts — `scripts/`

These are local Python scripts (not Kaggle notebooks) for evaluating after the training pipeline completes.

**`scripts/evaluate.py`**
- Loads the fine-tuned adapter on top of the base model in 4-bit (BitsAndBytes `nf4`)
- Runs inference on `data/processed/test.jsonl` (default: first 200 examples)
- Reports: type-prefix accuracy, BLEU (sacrebleu), ROUGE-L
- Uses `diff_utils.fit_prompt` from the local package
- Supports `--no-adapter` to baseline against the raw base model

**`scripts/evaluate_ollama.py`**
- Evaluates a model served by **Ollama** (`http://localhost:11434`) via its HTTP API
- Supports parallelism (`--workers 4`) with `ThreadPoolExecutor`
- Reports the same metrics as `evaluate.py` plus valid-format %
- Optionally compares against fp32 predictions from `evaluate_Kaggle.ipynb` example-by-example using a McNemar significance test
- Saves predictions to `preds_ollama.jsonl` for later analysis
- Uses `diff_utils.fit_prompt` with an `AutoTokenizer` (Hugging Face, no GPU needed)

Both scripts share `commit_model.diff_utils.fit_prompt` for consistent prompt construction.

---

### 5. CommitSuite Evaluation — `CommitSuite/`

A separate, independent evaluation benchmark for commit message generation. Reads a pre-generated `CMG_result.json` (a list of entries with `description`, `CMG_result`, and `modified_files`) and scores the generated messages.

**`CMG_eval_traditional_metrics.py`**
- Computes BLEU (NLTK), ROUGE-L, and METEOR between generated messages and reference descriptions
- Uses multiprocessing (`mp.Pool`, 10 workers by default)
- Writes averages to `CMG_reports/CMG_eval_traditional_metrics.csv`

**`CMG_eval_binary_metrics.py`**
- Uses **DeepSeek** (OpenAI-compatible API) as an LLM judge to score generated commit messages on 5 binary dimensions: Rationality, Comprehensiveness, Non-redundancy, Authenticity, Logicality
- Runs up to 15 concurrent API calls (`ThreadPoolExecutor`, `MAX_WORKERS=15`)
- Outputs per-entry scores as JSON and aggregate averages as CSV to `CMG_reports/`
- **Note:** Contains a bug — `os.open.path.join(...)` on line saving the JSON file should be `os.path.join(...)`. The CSV save is correct.
- The API key is hardcoded as `"sk-xxx"` (a placeholder) — this needs a real key to run.

**`Ten-category_eval.py`**
- Evaluates a 10-class commit type classifier (docs, perf, style, refactor, feat, fix, test, ci, build, chore)
- Reads `Ten-category_result.json` with fields `message_type` and `Ten-category_result`
- Computes accuracy, per-class precision/recall/F1, and macro averages using scikit-learn
- Generates a confusion matrix heatmap (seaborn) saved to `Ten-category_reports/confusion_matrix.png`
- Saves the metrics report to `Ten-category_reports/classification_metrics.csv`

---

## Cross-File Connections & Shared Constants

The following values are duplicated across multiple files (kept in sync manually):

| Constant | Value | Where |
|---|---|---|
| `SEQ_LEN` | 768 | `diff_utils.py`, `fine-tuning_Kaggle.ipynb`, `evaluate_Kaggle.ipynb`, `evaluate_quantized_Kaggle.ipynb`, `quantize_gguf_Kaggle.ipynb` |
| `PROMPT_TEMPLATE` | `"Write a Conventional Commits message..."` | Same set of files |
| `MAX_DIFF_CHARS` | 4000 | `diff_utils.py`, `CommitBench_filter.ipynb` |
| `MAX_FILES_PER_DIFF` | 6 | Same |
| `GENERATED_FILE_PATTERNS` | lockfile/build/minified patterns | Same |
| `LLAMA_TAG` | `"b11476"` | `engine.py`, `evaluate_quantized_Kaggle.ipynb` |
| `MAX_NEW_TOKENS` | 40 | `engine.py`, all evaluation notebooks/scripts |

The notebooks intentionally copy these constants inline to avoid a dependency on the local package when running on Kaggle.

---

## Overall Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  USER-FACING PRODUCTS                    │
│  VS Code Extension (TypeScript)  │  Beemo CLI (Python)  │
│       vscode-extension/          │  src/commit_model/   │
└────────────────────┬─────────────┴──────────┬───────────┘
                     │                        │
              postprocess.ts            postprocess.py  ← shared test cases
              engine.ts                 engine.py       ← same llama.cpp binary
              diff_utils.ts             diff_utils.py   ← shared constants
                     │                        │
                     └──────────┬─────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   GGUF Model (~1GB)    │
                    │  commit-model-Q4_K_M   │
                    │  served by llama-server│
                    └───────────┬────────────┘
                                │ produced by
                ┌───────────────▼──────────────────────┐
                │         TRAINING PIPELINE            │
                │  CommitBench_filter.ipynb             │
                │     → fine-tuning_Kaggle.ipynb        │
                │       → merge_adapter_Kaggle.ipynb    │
                │         → quantize_gguf_Kaggle.ipynb  │
                └──────────────────────────────────────┘
                                │ measured by
                ┌───────────────▼──────────────────────┐
                │         EVALUATION                   │
                │  scripts/evaluate.py  (adapter+GPU)  │
                │  scripts/evaluate_ollama.py (Ollama) │
                │  evaluate_Kaggle.ipynb  (fp32, T4)   │
                │  evaluate_quantized_Kaggle.ipynb      │
                └──────────────────────────────────────┘
                                │ separate benchmark
                ┌───────────────▼──────────────────────┐
                │         CommitSuite/                 │
                │  CMG_eval_traditional_metrics.py     │
                │  CMG_eval_binary_metrics.py          │
                │  Ten-category_eval.py                │
                └──────────────────────────────────────┘
```

---

## Issues & Recommendations

1. **Bug in `CommitSuite/CMG_eval_binary_metrics.py`** (line ~84): `os.open.path.join(...)` should be `os.path.join(...)`. The JSON output save will crash at runtime. The CSV save two lines later is correct.

2. **Hardcoded API key placeholder** in `CMG_eval_binary_metrics.py`: `api_key="sk-xxx"` will fail unless replaced with a real DeepSeek API key. Consider reading from an environment variable (`os.environ.get("DEEPSEEK_API_KEY")`).

3. **Duplicated constants** across notebooks and `diff_utils.py` are intentional (Kaggle standalone requirement) but could drift. Consider adding a comment in each notebook pointing to `diff_utils.py` as the source of truth.

4. **`CommitBench_filter.ipynb`** duplicates the full filtering logic from `diff_utils.py`. If filtering rules change, both must be updated. A note in the notebook already explains why (standalone Kaggle requirement).

5. **`scripts/evaluate.py`** uses BitsAndBytes 4-bit loading, which requires a CUDA GPU. `evaluate_ollama.py` is the CPU-friendly alternative for local use.
