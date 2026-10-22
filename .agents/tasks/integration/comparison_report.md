# OffHand vs CommitSuite — Comparison Report

## 1. Project Summaries

### OffHand

**Purpose:** An end-to-end commit message generation system. A LoRA-fine-tuned
`Qwen2.5-Coder-1.5B-Instruct` generates Conventional Commits messages from staged diffs. The model
is served via `llama.cpp`'s `llama-server` (GGUF, 4-bit Q4_K_M, ~986 MB) inside a VS Code extension
("Offhand") and a Python CLI tool ("Beemo"). Everything runs 100% locally; no API key or cloud
dependency.

**Architecture layers:**
1. **Data** — CommitBench (HuggingFace, CC BY-NC 4.0) filtered to ~45k `feat:`/`fix:`/… examples
   (`notebooks/CommitBench_filter.ipynb`). Output: `data/processed/{train,validation,test}.jsonl`.
2. **Training** — LoRA (r=16) on Kaggle T4 via `trl.SFTTrainer`, prompt/completion format, loss on
   completion only (`notebooks/fine-tuning_Kaggle.ipynb`). Adapter in
   `commit-model-lora/`.
3. **Merge + Quantize** — Adapter merged into base weights (`merge_adapter_Kaggle.ipynb`), then
   converted to GGUF and quantized to Q4_K_M (`quantize_gguf_Kaggle.ipynb`).
4. **Evaluation** — `scripts/evaluate.py` (Python, 4-bit adapter via BitsAndBytes), `evaluate_Kaggle.ipynb`
   (fp32, batch, two GPUs in parallel), `scripts/evaluate_ollama.py` (Ollama back-end). Metrics:
   valid-format rate, type accuracy, BLEU (sacrebleu), ROUGE-L. Known best: 99.9% valid format,
   67.3% type accuracy, BLEU 19.4.
5. **Inference** — `src/commit_model/{cli,engine,diff_utils,postprocess}.py` for Beemo;
   `vscode-extension/src/` for Offhand.
6. **Post-processing** — `clean_message` strips CommitBench training placeholders (`<I>`,
   `<URL>`, `<EMAIL>`), normalizes capitalization. Shared test cases ensure Python and TypeScript
   implementations stay identical.

### CommitSuite

**Purpose:** A benchmark for two tasks on a new, richer dataset:

- **Ten-category classification** — given a commit, predict its type (10 Conventional Commits
  categories).
- **Commit message generation (CMG)** — given diffs (and optionally issues/PRs/comments/AST changes),
  generate the commit message, evaluated with traditional metrics (BLEU, ROUGE-L, METEOR) and a novel
  LLM-based "binary" rubric (Rationality, Comprehensiveness, Non-redundancy, Authenticity, Logicality).

**Dataset:** 63,581 commits from 243 GitHub repos, six languages. Rich schema: per-file diffs,
issues, PRs, review comments, AST changes (via tree-sitter). Split into
`CMG-eval_dataset/` (1,000 examples for generation) and `Ten-category-eval_dataset/` (1,160
examples for classification).

**Code surface:** Four Python scripts at the repo root:
- `CMG_eval_traditional_metrics.py` — BLEU (sentence-level, nltk), ROUGE-L, METEOR in parallel via
  multiprocessing. Reads `CMG_result.json`, writes `CMG_reports/CMG_eval_traditional_metrics.csv`.
- `CMG_eval_binary_metrics.py` — calls DeepSeek v3 API concurrently (15 workers) to score 5 binary
  dimensions. **Requires a paid API key; contains a bug (`os.open.path.join`).**
- `Ten-category_eval.py` — sklearn classification metrics (accuracy, precision, recall, F1, confusion
  matrix PNG). Reads `Ten-category_result.json`.
- `README.md` — documents dataset schema, workflow, and metric instructions.

---

## 2. Feature Comparison Table

| Feature | OffHand status | CommitSuite status | Proposed integration | Files affected | Benefit & risks |
|---|---|---|---|---|---|
| **Dataset loading (CommitBench)** | Complete. `CommitBench_filter.ipynb` loads via HuggingFace Datasets, filters, writes JSONL. | N/A — CommitSuite ships its own pre-built JSON files. | No change needed. | — | — |
| **Dataset deduplication** | Missing. No dedup step in filter notebook or anywhere else. | N/A | Add exact-duplicate removal (by diff+message hash) to `CommitBench_filter.ipynb`. | `notebooks/CommitBench_filter.ipynb` | Removes ~12 pairs found in test/train overlap mentioned in results.md; prevents data leakage. Low risk. |
| **Training data class rebalancing** | Missing. `fix` is >50% of data; rare types never predicted. | N/A | Cap `fix` examples (e.g. max 20% of train split) and upsample rare types in the filter notebook. | `notebooks/CommitBench_filter.ipynb` | Directly addresses the known model bias documented in results.md. Moderate risk: changes training distribution. |
| **Placeholder cleaning in training data** | Missing. Training messages still contain `<I>`, `<URL>`, `<EMAIL>` placeholders. Post-processing strips them at inference, not training. | N/A | Apply `clean_message` to each training message in the filter notebook before writing JSONL. | `notebooks/CommitBench_filter.ipynb`, `src/commit_model/postprocess.py` | Eliminates placeholder leakage into generated messages. Enables removal of the inference-time cleanup shortcut eventually. Low risk. |
| **Reproducible train/val/test splits** | Present. CommitBench's own splits are used; seed fixed in eval step (`shuffle(seed=42)`). Minor issue: no global seed in filter notebook. | N/A | Add `RANDOM_SEED` constant and `random.seed()` call at top of filter notebook. | `notebooks/CommitBench_filter.ipynb` | Reproducibility. Very low risk. |
| **LoRA fine-tuning** | Complete. `fine-tuning_Kaggle.ipynb`, LoRA r=16 on all 7 projection layers, SFTTrainer, completion-only loss, fp32 weights. | N/A | No change needed. | — | — |
| **Checkpoint saving** | Present. SFTTrainer saves to `CHECKPOINT_DIR`. Only final adapter saved to `OUTPUT_DIR`. | N/A | No change needed. | — | — |
| **GPU/CPU device handling** | Complete in engine and training. | N/A | No change needed. | — | — |
| **BitsAndBytes 4-bit eval** | Present in `scripts/evaluate.py` but uses outdated single-example loop (no batching). | N/A | Optionally add batching. Not a priority. | `scripts/evaluate.py` | Minor speedup. Low risk. |
| **BLEU evaluation** | Present. sacrebleu corpus-level via `evaluate` library in `evaluate.py` and `evaluate_ollama.py`. | Present. sentence-level BLEU via `nltk.sentence_bleu` with smoothing in `CMG_eval_traditional_metrics.py`. | Integrate METEOR metric into OffHand's existing evaluation scripts. BLEU/ROUGE already covered. | `scripts/evaluate.py`, `scripts/evaluate_ollama.py` | Adds METEOR to reported metrics, aligning OffHand with CommitSuite's standard. Low risk. |
| **ROUGE-L evaluation** | Present. `rouge` via `evaluate` library. | Present. `rouge_scorer` directly. | No change; ROUGE-L already covered. | — | — |
| **METEOR evaluation** | **Missing entirely.** | Present in `CMG_eval_traditional_metrics.py` via `nltk.meteor_score`. | Add METEOR to `scripts/evaluate.py` and `scripts/evaluate_ollama.py`. Requires `nltk` + WordNet data. | `scripts/evaluate.py`, `scripts/evaluate_ollama.py`, `pyproject.toml` | Standard CMG metric; makes results comparable to CommitSuite and other benchmarks. Low risk. |
| **Ten-category classification metrics** | Partial. Only type accuracy (proportion correct). No per-type precision/recall/F1, no confusion matrix. | Complete. `Ten-category_eval.py` produces per-type P/R/F1, macro average, and seaborn confusion matrix PNG. | Adapt CommitSuite's classification report logic into OffHand's `scripts/evaluate.py` and `evaluate_ollama.py`. | `scripts/evaluate.py`, `scripts/evaluate_ollama.py` | Full per-type breakdown is much more informative than scalar accuracy. Medium risk: adds sklearn/seaborn dependencies. |
| **CMG binary evaluation (LLM-as-judge)** | Missing. | Present but requires DeepSeek API key (paid) and has a code bug (`os.open.path.join`). | **Do NOT integrate.** Violates hard constraint "no paid API dependencies". | — | Excluded. |
| **Confusion matrix visualization** | Missing. | Present in `Ten-category_eval.py` using matplotlib + seaborn. | Integrate into `scripts/evaluate.py`. | `scripts/evaluate.py`, `pyproject.toml` | Useful visual for thesis. Low risk. |
| **CommitSuite dataset as eval source** | Not used. | Ships 1,000-entry CMG eval and 1,160-entry classification eval sets. | Add a script `scripts/evaluate_commitsuite.py` that loads CommitSuite's CMG eval dataset and runs OffHand's model on it, producing traditional metrics (BLEU/ROUGE-L/METEOR). | `scripts/evaluate_commitsuite.py` | Provides comparable results on CommitSuite's dataset for the thesis. Medium risk: format conversion from CommitSuite JSON to OffHand's prompt format needed. |
| **Valid-format rate** | Present in `evaluate_ollama.py` (`VALID_RE`). Missing from `evaluate.py`. | N/A | Add valid-format rate to `scripts/evaluate.py`. | `scripts/evaluate.py` | Consistency between evaluation scripts. Very low risk. |
| **McNemar significance test** | Present in `evaluate_ollama.py`. Missing from `evaluate.py`. | N/A | Add McNemar test to `evaluate.py` when comparing adapter vs base. | `scripts/evaluate.py` | Rigorous statistical comparison for thesis. Low risk. |
| **Per-type accuracy breakdown** | Present in `evaluate_ollama.py`. Missing from `evaluate.py`. | Present in `Ten-category_eval.py`. | Add to `evaluate.py`. | `scripts/evaluate.py` | Consistency between scripts. Very low risk. |
| **Multiprocessing for metric computation** | Missing. Metrics computed sequentially. | Present in `CMG_eval_traditional_metrics.py`. | Not a priority (sacrebleu/rouge via `evaluate` are already fast). | — | Low value for this project size. |
| **Tokenization & prompt building** | Complete. `diff_utils.py` (Python) and `prompt.ts` (TypeScript) are kept in sync. SEQ_LEN=768. | N/A | No change needed. | — | — |
| **Diff post-processing / filtering** | Complete. Lockfile stripping, file-count cap, length cap. | N/A | No change needed. | — | — |
| **Input validation at inference** | Partial. `build_diff` returns None for empty/all-generated diffs. CLI handles this. | N/A | Add explicit error messages for each None-returning case. | `src/commit_model/cli.py` | Better UX. Low risk. |
| **VS Code extension** | Complete and published. | Not present. | N/A | — | — |
| **Git hook installer** | Complete. `scripts/install_hook.sh`. | Not present. | N/A | — | — |
| **README / documentation** | Exists but outdated (plan.md notes it needs updating). | Present but only covers benchmark use. | Update `README.md` with integration details and new commands. | `README.md` | Documentation quality for thesis. Low risk. |
| **Model card** | Stub in `commit-model-lora/README.md` (all placeholder text). | N/A | Fill out model card with actual training details, metrics, dataset info. | `commit-model-lora/README.md`, `hf_model_card/README.md` | Required for HuggingFace publication. Low risk. |

---

## 3. Incompatible Dependencies, Conflicts, and Integration Risks

### Dependency conflicts

| Library | OffHand (pyproject.toml) | CommitSuite requirement | Risk |
|---|---|---|---|
| `sacrebleu` | `sacrebleu` (via `evaluate`) | `nltk.sentence_bleu` | Both cover BLEU but with different granularity. OffHand uses corpus-level sacrebleu; CommitSuite uses sentence-level nltk. **Use sacrebleu for consistency with OffHand's existing results.** |
| `rouge-score` | `rouge-score` (via `evaluate`) | `rouge_scorer` directly | Same library, no conflict. |
| `nltk` | Not listed | `nltk` (wordnet, meteor) | Adding `nltk` and `nltk.download('wordnet')` is safe. No conflict. |
| `sklearn` | Not listed | `scikit-learn` | Adding for classification metrics. Compatible with Python 3.11. Note: pyproject.toml requires Python 3.12; system Python is 3.11. Install into the existing venv only. |
| `pandas` | Not listed | `pandas` | Adding for metric tabulation. No conflict. |
| `matplotlib`/`seaborn` | Not listed | `matplotlib`+`seaborn` | Adding for confusion matrix. No conflict. |
| `openai` | Not listed | `openai` (DeepSeek binary metrics) | **Not integrating** the binary metrics script. |

### Architectural incompatibilities

- **Data format mismatch:** CommitSuite uses a rich JSON structure per commit (all diffs as `modified_files[].diff`, which are already per-hunk without the `diff --git a/... b/...` header). OffHand expects unified diff format including the `diff --git` header. For `evaluate_commitsuite.py`, diffs must be reconstructed from CommitSuite's per-file hunks by prepending a synthetic `diff --git a/{path} b/{path}` header. This is straightforward and low risk.

- **Task scope mismatch:** CommitSuite's Ten-category classification assumes the model predicts a type label given a commit. OffHand's model generates a full commit message that starts with a type prefix. The ten-category evaluation in OffHand therefore works by extracting the type prefix from the generated message — exactly how `evaluate.py` and `evaluate_ollama.py` already work. No model change required.

- **Binary evaluation incompatibility:** CommitSuite's `CMG_eval_binary_metrics.py` requires a paid DeepSeek API key and has a Python bug (`os.open.path.join` should be `os.path.join`). It also evaluates on CommitSuite's own data, not CommitBench. This component is **excluded entirely** per the hard constraint against paid API dependencies.

- **`os.open.path.join` bug in CommitSuite:** The binary metrics script has a bug at `os.open.path.join(output_dir, file_out_json)`. This would crash at runtime. Relevant only as a note — we are not integrating this script.

- **Python version:** OffHand's `pyproject.toml` requires Python 3.12, but the system has Python 3.11. New packages must be compatible with Python 3.11 (all of nltk, scikit-learn, pandas, matplotlib, seaborn are). Tests should run under 3.11 until the environment is updated.

### Code duplication
- `CONVENTIONAL_PREFIX`, `GENERATED_FILE_PATTERNS`, `LOW_CONTENT_STOPLIST`, `MAX_DIFF_CHARS`, `MAX_FILES_PER_DIFF`, `split_diff_by_file`, `truncate_diff`, `is_generated_path`, `message_is_low_content` all exist in both `src/commit_model/diff_utils.py` and `notebooks/CommitBench_filter.ipynb`. This is intentional (notebook is self-contained) and should stay as-is.

- `TYPE_RE`, `extract_type`, `VALID_RE` are duplicated across `evaluate.py`, `evaluate_ollama.py`, and both notebooks. These should be centralized in `diff_utils.py` or a shared utilities module.

### Integration risks summary
- **Low risk:** METEOR, per-type metrics, valid-format rate, McNemar test, deduplication, reproducibility seed, model card fill-out.
- **Medium risk:** Class rebalancing (changes training distribution — requires re-running fine-tuning), CommitSuite CMG evaluation script (diff format conversion), confusion matrix (new plotting dependencies).
- **High risk / excluded:** Binary LLM-as-judge evaluation (paid API, bug).
- **No risk:** CommitSuite's VS Code extension, git hooks — neither exists in CommitSuite.
