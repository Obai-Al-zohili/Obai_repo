# Integration Plan: CommitSuite → OffHand

## Constraints (non-negotiable)

- Do NOT replace working OffHand functionality with CommitSuite alternatives.
- Do NOT do architectural rewrites.
- Do NOT add paid API dependencies (DeepSeek binary eval is excluded).
- Do NOT download large model checkpoints or datasets.
- Preserve `commit-model-lora/` and all checkpoint files.
- Keep compatible with Python 3.11 (system) and 3.12 (pyproject.toml target).
- Do NOT commit or push.

---

## Implementation Plan

- [ ] 1. Centralize shared evaluation utilities in `src/commit_model/diff_utils.py`.
      The constants `TYPE_RE`, `VALID_RE`, and function `extract_type` are copy-pasted across
      `scripts/evaluate.py`, `scripts/evaluate_ollama.py`, and both evaluation notebooks. Move them
      into `diff_utils.py` so every script imports from one place.
      Decision: add to `diff_utils.py` rather than a new file — it already holds shared
      prompt/diff logic and is already imported by both scripts.
      Files: `src/commit_model/diff_utils.py`, `scripts/evaluate.py`, `scripts/evaluate_ollama.py`
      Verify: `python -m unittest tests.test_postprocess` passes (smoke check that imports still work).

- [ ] 2. Add METEOR metric to `scripts/evaluate.py` and `scripts/evaluate_ollama.py`.
      CommitSuite's `CMG_eval_traditional_metrics.py` computes METEOR via
      `nltk.translate.meteor_score` with WordNet. OffHand currently reports only BLEU and ROUGE-L.
      METEOR is a standard CMG benchmark metric and makes results comparable to CommitSuite.
      Decision: use `nltk.meteor_score` with `nltk.download('wordnet', quiet=True)` at script
      startup — same approach as CommitSuite. Do NOT switch from sacrebleu to nltk BLEU; keep
      sacrebleu for consistency with `results.md`.
      Source: `CommitSuite/CMG_eval_traditional_metrics.py` (lines 14–30, meteor computation).
      Dependencies: add `nltk>=3.8` to `pyproject.toml`.
      Files: `scripts/evaluate.py`, `scripts/evaluate_ollama.py`, `pyproject.toml`
      Verify: `python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 10`
      prints a "METEOR:" line with a float value.

- [ ] 3. Add per-type precision/recall/F1 and confusion matrix to `scripts/evaluate.py`.
      OffHand currently reports only scalar type accuracy. CommitSuite's `Ten-category_eval.py`
      computes per-type P/R/F1 using sklearn and plots a seaborn confusion matrix. Both are
      directly applicable to OffHand since its model generates messages with type prefixes.
      Decision: adapt CommitSuite's `calculate_metrics` and `generate_confusion_matrix` functions
      (from `Ten-category_eval.py` lines 26–80) into `evaluate.py`. The confusion matrix PNG is
      written to the working directory as `type_confusion_matrix.png`.
      Dependencies: add `scikit-learn>=1.3`, `matplotlib>=3.7`, `seaborn>=0.12` to `pyproject.toml`.
      Source: `CommitSuite/Ten-category_eval.py`.
      Files: `scripts/evaluate.py`, `pyproject.toml`
      Verify: `python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 20`
      prints per-type F1 rows and creates `type_confusion_matrix.png`.

- [ ] 4. Add per-type accuracy breakdown and McNemar test to `scripts/evaluate.py`.
      `evaluate_ollama.py` already has both; `evaluate.py` (the BitsAndBytes/HuggingFace script) is
      missing them. Makes the two scripts consistent and adds statistical rigor for thesis comparisons.
      Decision: copy the per-type breakdown loop and `mcnemar_p` function from `evaluate_ollama.py`
      into `evaluate.py`. The `--no-adapter` flag runs the base model; when both models are
      evaluated in the same run, print the McNemar p-value.
      Files: `scripts/evaluate.py`
      Verify: `python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 20`
      prints "Type accuracy by type:" section.

- [ ] 5. Add valid-format rate metric to `scripts/evaluate.py`.
      `evaluate_ollama.py` reports valid-format rate (prediction matches `VALID_RE`); `evaluate.py`
      does not. This is the first metric in `results.md` and the clearest indicator that fine-tuning
      worked.
      Decision: import `VALID_RE` from `diff_utils.py` (after item 1 adds it there) and add the
      valid-format count to `evaluate.py`'s reporting loop.
      Files: `scripts/evaluate.py`
      Verify: `python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 10`
      prints "Valid format:" line.

- [ ] 6. Add deduplication to `notebooks/CommitBench_filter.ipynb`.
      OffHand's filter notebook does not deduplicate. `results.md` notes "12 diffs, ~0.1%, also
      appear in train.jsonl". Removing exact duplicates (by SHA-256 hash of the (diff, message) pair)
      prevents data leakage and is a standard data-hygiene step.
      Decision: add a `seen: set[str]` that hashes `(diff, message)` before writing each example.
      Add a `RANDOM_SEED = 42` constant at top of filter notebook for the eval shuffle call (no
      actual shuffle in the filter itself, but making the constant explicit aids reproducibility).
      No source in CommitSuite — this is an OffHand-specific improvement justified by results.md.
      Files: `notebooks/CommitBench_filter.ipynb`
      Verify: Re-run the filter notebook on a small sample (`LIMIT_PER_SPLIT = 500`) and confirm
      the dedup counter prints 0 duplicates removed (CommitBench has very few). The filter logic
      should be unchanged for non-duplicate rows.

- [ ] 7. Add class rebalancing to `notebooks/CommitBench_filter.ipynb`.
      `fix` comprises >50% of training data; `build`, `ci`, `perf`, `style` are each <3%. The model
      reliably outputs `fix` for ambiguous inputs and almost never picks rare types. OffHand's
      `plan.md` (step 5) and `results.md` both identify this as the primary improvement target.
      Decision: add a `MAX_PER_TYPE: dict` cap (e.g. `fix` → 12,000 examples max; all others
      uncapped initially). Write a per-type counter alongside `seen`. This keeps the approach
      simple and reversible — just change the cap dict to re-run.
      No source in CommitSuite — this is an OffHand improvement justified by plan.md.
      Files: `notebooks/CommitBench_filter.ipynb`
      Verify: Run with `LIMIT_PER_SPLIT = 5000` locally and check printed split statistics show
      `fix` no longer dominates. The JSONL output schema (`{"diff": ..., "message": ...}`) must
      be unchanged.

- [ ] 8. Add placeholder cleaning to training messages in `notebooks/CommitBench_filter.ipynb`.
      24% of CommitBench training messages contain `<I>`, `<URL>`, or `<EMAIL>` placeholders. The
      model learned to generate them; `clean_message` strips them at inference. Cleaning them
      from training messages is the proper fix (identified in `plan.md` step 5).
      Decision: import `clean_message` from `postprocess.py` OR inline the same regex logic in the
      notebook (notebook is intentionally self-contained). Apply it to each `message` in
      `build_example` after the format check. Inline the logic to keep the notebook self-contained.
      Source: `src/commit_model/postprocess.py` `clean_message` function.
      Files: `notebooks/CommitBench_filter.ipynb`
      Verify: Run with `LIMIT_PER_SPLIT = 200` and inspect 3 sample messages — none should contain
      `<I>`, `<URL>`, `<EMAIL>`, `<HASH>`.

- [ ] 9. Create `scripts/evaluate_commitsuite.py` — run OffHand's model on CommitSuite's CMG eval dataset.
      CommitSuite ships `CMG-eval_dataset/all_CMG.json` (1,000 entries). Running OffHand's model
      on it and reporting BLEU/ROUGE-L/METEOR allows direct comparison with other tools that
      evaluated on CommitSuite. This is the most thesis-relevant integration.
      Decision:
        - Load `CommitSuite/CMG-eval_dataset/all_CMG.json`.
        - Reconstruct unified diff from each `modified_files` entry by prepending
          `diff --git a/{old_path} b/{new_path}\n` to the `diff` field (which is already a hunk
          in `@@ ... @@` format). Join multiple files.
        - Use `fit_prompt` from `diff_utils.py` for truncation (same as all other eval scripts).
        - Generate predictions via Ollama (same approach as `evaluate_ollama.py`) so no GPU is
          required. Default to `commit-model` as the Ollama model name.
        - Report BLEU (sacrebleu), ROUGE-L, METEOR, valid-format rate, type accuracy.
        - Compare against CommitSuite's `description` field (the commit message body without the
          type prefix) as the reference — because CommitSuite intentionally separates type from
          description to hide type information.
        - Write predictions to `preds_commitsuite.jsonl`.
      Source: structure based on `scripts/evaluate_ollama.py`; diff reconstruction logic derived
      from CommitSuite's `modified_files` schema.
      Dependencies: none beyond what items 2–3 add. Uses `commit_model.diff_utils` (already in src/).
      Files: `scripts/evaluate_commitsuite.py`
      Verify: `python scripts/evaluate_commitsuite.py --limit 5` (requires Ollama running with
      the commit-model) executes without error and prints metric rows. Document in script that Ollama
      must be running.

- [ ] 10. Fill out the model card in `commit-model-lora/README.md`.
       The current model card is entirely placeholder text ("More Information Needed" everywhere).
       A proper card is required for HuggingFace publication and for the senior project thesis.
       Decision: populate every section with the actual training details already documented in
       `results.md`, `plan.md`, `MVP.md`, `fine-tuning_Kaggle.ipynb`, and `adapter_config.json`.
       Do NOT add speculative or unverified claims.
       Files: `commit-model-lora/README.md`, `hf_model_card/README.md`
       Verify: Read both files and confirm every "More Information Needed" is replaced with real
       content. No functional test required.

- [ ] 11. Update `README.md` with new commands and integration notes.
       `plan.md` notes the README is outdated. New scripts (`evaluate_commitsuite.py`) and new
       metric outputs (METEOR, confusion matrix) should be documented with exact CLI commands.
       Files: `README.md`
       Verify: All new scripts mentioned in items 2–9 have their CLI invocation in the README.

- [ ] 12. Update `pyproject.toml` with new dependencies.
       Items 2 and 3 add `nltk`, `scikit-learn`, `matplotlib`, `seaborn`. Pin to minimum compatible
       versions matching Python 3.11 and 3.12.
       Files: `pyproject.toml`
       Verify: `pip install -e . --dry-run` (or equivalent) shows the new packages. Since the
       environment is bare (only pip/setuptools), actual install of ML packages is not expected to
       run in this environment — document this limitation.

- [ ] 13. Run full verification.
       Run `python -m unittest tests.test_postprocess` to confirm existing tests still pass.
       Run `python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 10`
       and confirm it prints METEOR, valid-format, per-type breakdown rows, and creates
       `type_confusion_matrix.png`.
       Run `python scripts/evaluate.py --no-adapter --test-file data/processed/test.jsonl --limit 20`
       to confirm the McNemar section runs when only one model is evaluated (should print "N/A" or
       skip gracefully).
       Files: (verification only, no file changes)

---

## Priority order and rationale

1. **Items 1–5 (evaluation improvements):** Highest impact for thesis. No retraining required.
   They directly improve the evaluation scripts that generate thesis metrics.
2. **Items 6–8 (dataset improvements):** These improve the training data quality and address the
   known bias problem. Retraining is needed to see the benefit, but the notebook changes are
   self-contained and reversible.
3. **Item 9 (CommitSuite evaluation script):** Enables direct comparison with CommitSuite's
   reported results. Medium implementation effort; depends on items 2–3.
4. **Items 10–12 (documentation and dependencies):** Low effort, needed for publication.
5. **Item 13 (verification):** Always last.

---

## Features deliberately excluded

| Feature | Reason |
|---|---|
| CommitSuite binary LLM-as-judge evaluation (`CMG_eval_binary_metrics.py`) | Requires paid DeepSeek API key. Also has a Python bug. Violates hard constraint. |
| CommitSuite's dataset as a new training source | CommitSuite's license requires verification; training on it would require a new fine-tuning run and is out of scope for the integration phase. OffHand already has 45k good CommitBench examples. |
| Switching from sacrebleu to nltk BLEU | OffHand's reported results use sacrebleu corpus-level BLEU. Switching would break comparability with `results.md`. CommitSuite uses sentence-level nltk BLEU — a different metric. |
| CommitSuite's multiprocessing in metric computation | OffHand's test set is 9,704 examples; sacrebleu+rouge compute in seconds. Multiprocessing adds complexity with no practical gain. |
| Sentence-level BLEU per example output | Not part of OffHand's current reporting; out of scope. |
| AST-change features from CommitSuite | CommitSuite's AST metadata requires tree-sitter preprocessing of source code. OffHand's model is trained on raw diffs; adding AST inputs would require retraining with a different input format. |
