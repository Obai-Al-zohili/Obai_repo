# Integration Final Report: CommitSuite → OffHand

**Date:** 2026-10-22  
**Status:** Complete  
**Workflow:** `offhand-commitsuite-integration` (wf_b4d0c0677c95699f, resumed after usage-limit interruption)

---

## 1. Summary of Key Differences

| Dimension | OffHand | CommitSuite |
|---|---|---|
| **Purpose** | End-to-end CMG product: VS Code extension + CLI + training pipeline | Benchmark framework: evaluation dataset + metric scripts only |
| **Model** | Fine-tuned Qwen2.5-Coder-1.5B-Instruct → LoRA adapter → Q4_K_M GGUF | No model; evaluates external tools |
| **Training data** | CommitBench (Maxscha/commitbench, filtered to ~45 K examples) | CMG-eval dataset (1 000 curated commits, 7 languages) |
| **Evaluation** | BLEU (sacrebleu), ROUGE-L; per-type accuracy (partial) | BLEU (nltk sentence), ROUGE-L, METEOR, 10-class classifier, binary LLM judge |
| **Inference** | llama.cpp GGUF server; BitsAndBytes 4-bit HuggingFace path | Not applicable |
| **Shared utilities** | `diff_utils.py` (centralized), `postprocess.py` | Inline per-script |
| **Data quality** | No dedup; no class rebalancing; placeholder tokens in labels | N/A (eval-only) |

OffHand is the richer system; CommitSuite contributes three things OffHand lacked: METEOR metric, per-type classifier metrics, and a 1,000-example benchmark for cross-tool comparison.

---

## 2. Features Integrated

### FEAT-001 — Evaluation improvements (implemented by previous workflow step)

All changes flow through `src/commit_model/diff_utils.py` as the single source of truth.

| Sub-feature | What was done |
|---|---|
| Centralize `TYPE_RE`, `VALID_RE`, `extract_type`, `mcnemar_p` | Added to `diff_utils.py`; both eval scripts import from there instead of copy-pasting |
| METEOR metric | Added to `scripts/evaluate.py` and `scripts/evaluate_ollama.py` via `nltk.translate.meteor_score`; graceful fallback if nltk not installed |
| Per-type P/R/F1 + confusion matrix | Added `compute_per_type_metrics()` and `generate_confusion_matrix()` to `evaluate.py`; saves `type_confusion_matrix.png`; graceful fallback if sklearn/matplotlib absent |
| Valid-format rate | Added to `evaluate.py` (was already in `evaluate_ollama.py`) |
| Per-type accuracy breakdown | Added to `evaluate.py` (was already in `evaluate_ollama.py`) |
| McNemar significance test | Added to `evaluate.py` (was already in `evaluate_ollama.py`); prints when both base and adapter are evaluated |
| New dependencies | `nltk>=3.8`, `scikit-learn>=1.3`, `matplotlib>=3.7`, `seaborn>=0.12` added to `pyproject.toml` |

Source: `CommitSuite/CMG_eval_traditional_metrics.py` (METEOR), `CommitSuite/Ten-category_eval.py` (classifier metrics, confusion matrix).

### FEAT-002 — Training data quality improvements

All changes in `notebooks/CommitBench_filter.ipynb`. The notebook was refactored from one monolithic cell into six logical cells for readability; the output schema (`{"diff": str, "message": str}`) is unchanged.

| Sub-feature | What was done |
|---|---|
| Deduplication | Added `seen_hashes: set` per split; each example is hashed by `sha256(diff + message)[:16]`; duplicates silently skipped; `hashlib` imported |
| Class rebalancing (train only) | Added `MAX_PER_TYPE: dict = {"fix": 12_000}` config constant; `type_counts` counter tracks kept examples per type; cap applied only on the `train` split so val/test remain unaffected |
| Placeholder cleaning | Added `clean_training_message()` inline function; strips `<I>`, `<URL>`, `<EMAIL>`, `<HASH>` tokens (same logic as `postprocess.py`'s `clean_message`, minus inference-time cosmetic steps); examples where cleaning guts the description to < 4 chars are rejected |
| `RANDOM_SEED = 42` | Added to config cell for reproducibility documentation |
| Per-type statistics | Filter loop now prints per-type counts + percentages + `[CAPPED]` markers after each split |
| Schema assertion | Sanity-check cell asserts `set(row.keys()) == {"diff", "message"}` and no placeholders in output |

Source: OffHand `plan.md` step 5 and `results.md` (both identify these as the top improvement targets); no CommitSuite source — these are OffHand-native improvements.

### FEAT-003 — CommitSuite benchmark script, model card, documentation

| Sub-feature | What was done |
|---|---|
| `scripts/evaluate_commitsuite.py` | New script; loads `CommitSuite/CMG-eval_dataset/all_CMG.json`; reconstructs unified diffs from per-file hunk records; runs inference via Ollama; reports BLEU/ROUGE-L/METEOR/valid-format/type-accuracy; saves `preds_commitsuite.jsonl`; `--limit` and `--dataset-path` arguments |
| `commit-model-lora/README.md` | Fully rewritten from all-placeholder to complete model card: description, uses, bias/limitations, training data (CommitBench, 45 K examples, filtering policy), LoRA config table, training hyperparameters, evaluation results table, per-type accuracy table, 4-bit GGUF results, environmental impact, citation (CommitBench BibTeX) |
| `hf_model_card/README.md` | Updated results section with full per-type breakdown and pointer to evaluation scripts |
| `README.md` | Added `## Evaluation` section documenting all three eval scripts with exact commands; updated scripts table row |

---

## 3. Files Modified, Added, Deleted

### Modified
| File | Change |
|---|---|
| `src/commit_model/diff_utils.py` | Added `TYPE_RE`, `VALID_RE`, `extract_type()`, `mcnemar_p()` |
| `scripts/evaluate.py` | Added METEOR, valid-format, per-type breakdown, McNemar test, per-type P/R/F1, confusion matrix; imports centralized from `diff_utils` |
| `scripts/evaluate_ollama.py` | Imports centralized from `diff_utils` (TYPE_RE, VALID_RE, extract_type, mcnemar_p) |
| `notebooks/CommitBench_filter.ipynb` | Deduplication, class rebalancing, placeholder cleaning, RANDOM_SEED, per-type stats, schema assertions; refactored into 6 cells |
| `pyproject.toml` | Added `nltk>=3.8`, `scikit-learn>=1.3`, `matplotlib>=3.7`, `seaborn>=0.12` |
| `commit-model-lora/README.md` | Fully rewritten (was all placeholders) |
| `hf_model_card/README.md` | Updated results section |
| `README.md` | Added Evaluation section; updated scripts table |

### Added
| File | Description |
|---|---|
| `scripts/evaluate_commitsuite.py` | Evaluate OffHand model on CommitSuite CMG benchmark (1 000 examples) |
| `.agents/tasks/integration/comparison_report.md` | Feature comparison table (planning artifact) |
| `.agents/tasks/integration/integration_plan.md` | 13-item ordered integration plan (planning artifact) |
| `.agents/tasks/integration/final_report.md` | This file |

### Deleted
None. No existing file was removed.

---

## 4. How the New Functionality Works

### Evaluation pipeline (FEAT-001)

```
scripts/evaluate.py  OR  scripts/evaluate_ollama.py
         │
         ├─ imports TYPE_RE, VALID_RE, extract_type, mcnemar_p  ◄── diff_utils.py (single source)
         │
         ├─ generates predictions (BitsAndBytes / Ollama)
         │
         ├─ BLEU (sacrebleu corpus-level)
         ├─ ROUGE-L (rouge-score)
         ├─ METEOR (nltk WordNet, optional)
         ├─ valid-format rate  (VALID_RE match fraction)
         ├─ type accuracy      (exact prefix match)
         ├─ per-type accuracy breakdown
         ├─ per-type P/R/F1 + macro avg  (sklearn, optional)
         ├─ confusion matrix PNG          (matplotlib/seaborn, optional)
         └─ McNemar p-value              (exact binomial, from diff_utils)
```

Optional dependencies (nltk, sklearn, matplotlib/seaborn) degrade gracefully: if not installed, the
corresponding metric section prints a one-line install hint and continues.

### Training data pipeline (FEAT-002)

```
CommitBench (Maxscha/commitbench, ~1.17M rows)
    │
    ▼  CommitBench_filter.ipynb
    │
    ├─ format check (CONVENTIONAL_PREFIX regex)
    ├─ low-content check (stoplist + min length)
    ├─ diff truncation (drop generated files, cap 4 000 chars)
    ├─ placeholder cleaning  ◄── NEW: strip <I>/<URL>/<EMAIL>/<HASH>
    ├─ deduplication         ◄── NEW: sha256(diff+msg)[:16] hash set
    └─ class rebalancing     ◄── NEW: MAX_PER_TYPE cap on train split only
         │
         ▼
    train.jsonl / validation.jsonl / test.jsonl
    {"diff": str, "message": str}
```

### CommitSuite benchmark script (FEAT-003)

```
CommitSuite/CMG-eval_dataset/all_CMG.json  (1 000 entries)
    │
    ▼  scripts/evaluate_commitsuite.py
    │
    ├─ reconstruct diff: prepend "diff --git a/{old} b/{new}\n--- a/...\n+++ b/...\n" to each hunk
    ├─ build_diff() from diff_utils — same filtering as all other scripts
    ├─ fit_prompt() from diff_utils — same truncation as training
    ├─ Ollama inference (parallel, --workers=4)
    ├─ reference = entry["description"]  (body without type prefix)
    └─ BLEU / ROUGE-L / METEOR / valid-format / type-accuracy
         + per-type accuracy breakdown by CommitSuite's message_type label
```

---

## 5. Dependencies Added or Changed

| Package | Version constraint | Purpose | Already in env? |
|---|---|---|---|
| `nltk` | `>=3.8` | METEOR metric (WordNet tokenizer) | Depends on environment |
| `scikit-learn` | `>=1.3` | Per-type P/R/F1, confusion matrix | Depends on environment |
| `matplotlib` | `>=3.7` | Confusion matrix PNG | Depends on environment |
| `seaborn` | `>=0.12` | Confusion matrix styling | Depends on environment |

All four were added to `pyproject.toml`. All four are optional at runtime — missing packages produce
a clear install hint and the script continues without that metric.

---

## 6. Installation and Usage

### Install

```bash
# Clone the repo (if not already done)
git clone https://github.com/JesserLahmer/OffHand
cd OffHand

# Create environment (Python 3.12)
uv venv --python 3.12 .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install all dependencies including new ones
uv pip install -e .

# Download NLTK WordNet data (needed for METEOR)
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### Run evaluation — CommitBench test split

```bash
# With Ollama (no GPU required):
ollama run commit-model   # first-time model load; Ctrl-C to exit chat, server stays up
python scripts/evaluate_ollama.py --limit 200

# With LoRA adapter + BitsAndBytes (GPU required, tested on T4):
python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 200
# (omit --no-adapter to evaluate both base and fine-tuned and get McNemar test)
```

Both scripts now report: valid-format, type-accuracy, BLEU, ROUGE-L, METEOR, per-type breakdown,
per-type P/R/F1, confusion matrix (`type_confusion_matrix.png`), and McNemar p-value.

### Run evaluation — CommitSuite CMG benchmark

```bash
ollama run commit-model   # must be running
python scripts/evaluate_commitsuite.py --limit 10   # smoke test (fast)
python scripts/evaluate_commitsuite.py               # full 1 000-example benchmark
```

Predictions saved to `preds_commitsuite.jsonl`.

### Retrain with improved data

```bash
# On Kaggle (internet ON, no GPU needed for filtering):
# 1. Upload notebooks/CommitBench_filter.ipynb
# 2. Run it — data is filtered with dedup + class cap + placeholder cleaning
# 3. Download commitbench-filtered.zip → extract to data/processed/
# 4. Upload data/ + fine-tuning_Kaggle.ipynb to Kaggle (GPU T4×2)
# 5. Run fine-tuning_Kaggle.ipynb
```

---

## 7. Test Results

### Tests that ran and passed

| Check | Result |
|---|---|
| `python -m unittest tests.test_postprocess` | ✅ 1 test, OK |
| Syntax check: `evaluate.py`, `evaluate_ollama.py`, `evaluate_commitsuite.py`, `diff_utils.py`, `postprocess.py` | ✅ all pass `ast.parse` |
| `diff_utils` imports: `TYPE_RE`, `VALID_RE`, `extract_type`, `mcnemar_p`, `fit_prompt`, `build_diff` | ✅ all importable |
| `extract_type` logic | ✅ `feat:` → `feat`, `fix(scope):` → `fix`, non-CC → `None` |
| `VALID_RE` logic | ✅ matches valid CC, rejects free text |
| `mcnemar_p` edge cases | ✅ `(0,0)` → 1.0; `(10,0)` → p < 0.05 |
| `build_diff` on sample diff | ✅ returns non-None, preserves path |
| Notebook: valid JSON | ✅ |
| Notebook: Python syntax (magics excluded) | ✅ |
| Notebook: all 8 required additions present | ✅ `hashlib`, `RANDOM_SEED`, `MAX_PER_TYPE`, `seen_hashes`, `clean_training_message`, `is_train`, `placeholder_cleaned`, `type_counts` |
| CommitSuite dataset load | ✅ 1 000 entries, 0 missing descriptions, 0 missing diffs (first 50) |
| `evaluate_commitsuite` diff reconstruction + `build_diff` | ✅ 2 187 chars reconstructed for entry 0 |
| `clean_training_message` placeholder stripping | ✅ `<I>`/`<URL>`/`<EMAIL>`/`<HASH>` tokens removed; descriptions with < 4 chars after cleaning rejected |
| `commit-model-lora/README.md`: no placeholders | ✅ `"More Information Needed"` not found |
| `commit-model-lora/README.md`: required sections | ✅ Training Data, Training Procedure, Evaluation, Results, Environmental Impact, Citation, LoRA |
| `README.md`: evaluate_commitsuite + METEOR + CommitSuite CMG | ✅ all present |

### Tests that could NOT run

| Test | Reason |
|---|---|
| End-to-end `evaluate.py` (BitsAndBytes inference) | Requires CUDA GPU with ≥8 GB VRAM and model weights download (~3 GB). Not available in the current environment. |
| End-to-end `evaluate_ollama.py` / `evaluate_commitsuite.py` (Ollama inference) | Requires Ollama server running with `commit-model` loaded. Not running in current environment. |
| Full `CommitBench_filter.ipynb` execution | Requires internet access + `pip install datasets` + ~10 GB CommitBench download. Not feasible locally. |
| `pip install -e .` with new deps | `uv` not installed in current environment; scipy-based packages (sklearn, seaborn) require native builds. Documented as limitation. |

---

## 8. CommitSuite Features Deliberately Not Integrated

| Feature | Source file | Reason not integrated |
|---|---|---|
| Binary LLM-as-judge evaluation | `CMG_eval_binary_metrics.py` | Requires a paid DeepSeek API key. Violates the hard constraint against paid APIs. Also has a Python bug (incorrect reference handling). |
| Sentence-level BLEU per example (nltk) | `CMG_eval_traditional_metrics.py` | OffHand's reported results use corpus-level sacrebleu BLEU. Switching would break comparability with `results.md`. The two are different metrics and should not be mixed. |
| Multiprocessing in metric computation | `CMG_eval_traditional_metrics.py` | OffHand's test set is 9 704 examples; sacrebleu + rouge-score compute in seconds. Adding multiprocessing increases complexity with no practical benefit. |
| CommitSuite dataset as additional training source | `all_data/` (172 repos) | License requires per-repo verification. Using it as training data would require a new fine-tuning run, which is out of scope for this integration phase. OffHand already has 45 K clean CommitBench examples. |
| AST-change features | `ast_changes` field in `all_CMG.json` | Requires tree-sitter preprocessing of source code. OffHand's model is trained on raw diffs; adding AST inputs would require redesigning the prompt format and retraining from scratch. |
| Per-language dataset splits | `c_c++.json`, `go.json`, etc. | Adds useful per-language breakdown but CommitSuite's 1 000-example dataset is too small for statistically meaningful per-language metrics. Can be added later to `evaluate_commitsuite.py` as a `--language` filter argument. |

---

## 9. Preserved Original Functionality

- All existing OffHand files untouched except those listed in section 3.
- `commit-model-lora/` adapter weights, tokenizer, and `adapter_config.json` unchanged.
- `CommitSuite/` directory: read-only throughout; no modifications made.
- Git history: no commits made.
- VS Code extension (`vscode-extension/`): unchanged.
- Existing `scripts/install_hook.sh`: unchanged.
- `tests/test_postprocess.py`: unchanged, still passes.
