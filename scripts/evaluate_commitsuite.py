"""Evaluate OffHand's commit-model on CommitSuite's CMG evaluation dataset.

CommitSuite ships 1,000 human-curated commits across 7 languages.  Running
OffHand's model on this benchmark allows direct comparison with other CMG tools
that have reported results on the same dataset.

The script reconstructs unified diffs from CommitSuite's per-file hunk records,
runs inference via Ollama (same path as evaluate_ollama.py, so no GPU required),
and reports BLEU, ROUGE-L, METEOR, valid-format rate, and type accuracy.

Requirements:
    Ollama must be running with the commit-model loaded:
        ollama run commit-model

    Python packages (already in pyproject.toml):
        pip install evaluate transformers sacrebleu rouge-score nltk

Usage:
    # Full benchmark (1 000 examples)
    python scripts/evaluate_commitsuite.py

    # Quick smoke test (first 10 examples)
    python scripts/evaluate_commitsuite.py --limit 10

    # Custom dataset path or model name
    python scripts/evaluate_commitsuite.py \\
        --dataset-path CommitSuite/CMG-eval_dataset/all_CMG.json \\
        --model commit-model \\
        --limit 100
"""
import argparse
import json
import sys
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Make the src/ package importable when the script is run from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# ---------------------------------------------------------------------------
# Optional heavy imports — fail gracefully if packages are not installed
# ---------------------------------------------------------------------------
try:
    import nltk
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)
    from nltk.translate.meteor_score import meteor_score as _meteor_score
    _HAS_NLTK = True
except ImportError:
    _HAS_NLTK = False

import evaluate
from transformers import AutoTokenizer

from commit_model.diff_utils import (
    TYPE_RE,
    VALID_RE,
    build_diff,
    extract_type,
    fit_prompt,
)

MAX_NEW_TOKENS = 40
DEFAULT_DATASET = "CommitSuite/CMG-eval_dataset/all_CMG.json"
DEFAULT_MODEL = "commit-model"
DEFAULT_TOKENIZER = "Qwen/Qwen2.5-Coder-1.5B-Instruct"


# ---------------------------------------------------------------------------
# Diff reconstruction
# ---------------------------------------------------------------------------

def reconstruct_diff(entry: dict) -> str | None:
    """Reconstruct a unified diff string from a CommitSuite entry.

    CommitSuite stores each modified file as a dict with ``old_path``,
    ``new_path``, and ``diff`` (a raw ``@@ ... @@`` hunk without the
    ``diff --git`` header).  We prepend the standard header so that
    ``build_diff()`` can apply the same filtering / truncation that all
    other evaluation scripts use.

    Returns None if no usable diff could be reconstructed.
    """
    parts = []
    for mf in entry.get("modified_files") or []:
        old_path = mf.get("old_path") or mf.get("filename") or "unknown"
        new_path = mf.get("new_path") or mf.get("filename") or "unknown"
        hunk = (mf.get("diff") or "").strip()
        if not hunk:
            continue
        header = (
            f"diff --git a/{old_path} b/{new_path}\n"
            f"--- a/{old_path}\n"
            f"+++ b/{new_path}\n"
        )
        parts.append(header + hunk + "\n")

    if not parts:
        return None
    return "".join(parts)


# ---------------------------------------------------------------------------
# Ollama inference
# ---------------------------------------------------------------------------

def _generate_one(args_tuple) -> str | None:
    """Call Ollama and return the first line of the response, or None on error."""
    url, model_name, tokenizer, diff_raw = args_tuple
    diff = build_diff(diff_raw)
    if diff is None:
        return None
    prompt = fit_prompt(tokenizer, diff)
    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "raw": True,
        "stream": False,
        "options": {"temperature": 0, "top_k": 1, "num_predict": MAX_NEW_TOKENS},
    }).encode()
    req = urllib.request.Request(
        f"{url}/api/generate",
        headers={"Content-Type": "application/json"},
        data=payload,
    )
    try:
        response = json.load(urllib.request.urlopen(req, timeout=300))
        text = response.get("response", "").strip()
        return (text.splitlines() or [""])[0].strip()
    except Exception as exc:  # network errors, timeouts, JSON parse errors
        print(f"[WARN] Ollama request failed: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(preds: list[str], refs: list[str]) -> dict:
    """Compute BLEU, ROUGE-L, METEOR, valid-format rate, and type accuracy."""
    bleu_metric = evaluate.load("sacrebleu")
    rouge_metric = evaluate.load("rouge")

    bleu = bleu_metric.compute(
        predictions=preds, references=[[r] for r in refs]
    )["score"]
    rouge_l = rouge_metric.compute(
        predictions=preds, references=refs
    )["rougeL"]

    meteor = None
    if _HAS_NLTK:
        scores = [
            _meteor_score([r.lower().split()], p.lower().split())
            for p, r in zip(preds, refs)
        ]
        meteor = sum(scores) / len(scores)

    ref_types = [extract_type(r) for r in refs]
    valid_format = sum(bool(VALID_RE.match(p)) for p in preds) / len(preds)
    type_acc = sum(
        extract_type(p) == t for p, t in zip(preds, ref_types)
    ) / len(preds)

    return {
        "valid_format": valid_format,
        "type_acc": type_acc,
        "BLEU": bleu,
        "ROUGE-L": rouge_l,
        "METEOR": meteor,
        "ref_types": ref_types,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate commit-model on the CommitSuite CMG benchmark."
    )
    parser.add_argument(
        "--dataset-path",
        default=DEFAULT_DATASET,
        help="Path to CommitSuite's all_CMG.json (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Ollama model name (default: %(default)s)",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:11434",
        help="Ollama server URL (default: %(default)s)",
    )
    parser.add_argument(
        "--tokenizer",
        default=DEFAULT_TOKENIZER,
        help="HuggingFace tokenizer for prompt truncation (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Evaluate only the first N entries (default: all 1 000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Parallel Ollama requests (default: %(default)s)",
    )
    parser.add_argument(
        "--out",
        default="preds_commitsuite.jsonl",
        help="Output JSONL file for predictions (default: %(default)s)",
    )
    args = parser.parse_args()

    # --- Load dataset ---
    dataset_path = Path(args.dataset_path)
    if not dataset_path.exists():
        sys.exit(
            f"Dataset not found: {dataset_path}\n"
            "Make sure CommitSuite is cloned inside the OffHand workspace."
        )
    entries = json.loads(dataset_path.read_text(encoding="utf-8"))
    if args.limit:
        entries = entries[: args.limit]
    print(f"Loaded {len(entries)} entries from {dataset_path}")

    # --- Reconstruct diffs ---
    diffs_raw = []
    valid_entries = []
    skipped_no_diff = 0
    for entry in entries:
        diff_raw = reconstruct_diff(entry)
        if diff_raw is None:
            skipped_no_diff += 1
            continue
        diffs_raw.append(diff_raw)
        valid_entries.append(entry)

    if skipped_no_diff:
        print(f"Skipped {skipped_no_diff} entries with no usable diff.")

    # CommitSuite's 'description' field is the commit message body without the
    # type prefix.  We use it as the reference so metrics measure the quality
    # of the generated description, not the type prefix prediction.
    refs = [e["description"].strip() for e in valid_entries]

    print(
        f"\nNOTE: Ollama must be running with '{args.model}' loaded.\n"
        f"      Start it with:  ollama run {args.model}\n"
    )

    # --- Load tokenizer ---
    print(f"Loading tokenizer: {args.tokenizer}")
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    # --- Generate predictions ---
    work_items = [
        (args.url, args.model, tokenizer, diff_raw)
        for diff_raw in diffs_raw
    ]

    started = time.time()
    preds_raw: list[str | None] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for pred in pool.map(_generate_one, work_items):
            preds_raw.append(pred)
            n = len(preds_raw)
            if n % 50 == 0 or n == len(work_items):
                elapsed = time.time() - started
                print(
                    f"[{elapsed / 60:5.1f} min]  {n}/{len(work_items)} "
                    f"({elapsed / n:.2f}s each)",
                    flush=True,
                )

    # Replace None (failed inference) with empty string so metrics still run
    preds = [p if p is not None else "" for p in preds_raw]
    failed = sum(1 for p in preds_raw if p is None)
    if failed:
        print(f"\nWARN: {failed}/{len(preds)} predictions failed (Ollama errors).")

    # --- Save predictions ---
    with open(args.out, "w", encoding="utf-8") as f:
        for pred, ref, entry in zip(preds, refs, valid_entries):
            f.write(json.dumps({
                "pred": pred,
                "ref": ref,
                "msg": entry.get("msg", ""),
                "message_type": entry.get("message_type", ""),
                "repo": entry.get("repo_name", ""),
            }) + "\n")
    print(f"Predictions saved to {args.out}")

    # --- Compute and print metrics ---
    metrics = compute_metrics(preds, refs)
    ref_types = metrics.pop("ref_types")

    print(f"\n{'='*60}")
    print(f"CommitSuite CMG Benchmark — {args.model}")
    print(f"{'='*60}")
    print(f"Examples evaluated : {len(preds)}")
    print(f"Valid-format rate  : {metrics['valid_format']:.1%}")
    print(f"Type accuracy      : {metrics['type_acc']:.1%}")
    print(f"BLEU               : {metrics['BLEU']:.2f}")
    print(f"ROUGE-L            : {metrics['ROUGE-L']:.3f}")
    if metrics["METEOR"] is not None:
        print(f"METEOR             : {metrics['METEOR']:.3f}")
    else:
        print("METEOR             : (nltk not installed — pip install nltk)")

    # Per-type accuracy breakdown
    print("\nType accuracy by type (reference type from CommitSuite label):")
    cs_types = [e.get("message_type", "") for e in valid_entries]
    type_counter = Counter(cs_types)
    for t, n in type_counter.most_common():
        hits = sum(
            extract_type(p) == t
            for p, ct in zip(preds, cs_types)
            if ct == t
        )
        print(f"  {t:<12} {n:>5} examples   accuracy {hits / n:6.1%}")

    print(f"\nNote: references are CommitSuite 'description' fields (body only,")
    print(f"      no type prefix), so BLEU/ROUGE/METEOR measure description quality.")
    print(f"      Type accuracy uses CommitSuite's 'message_type' label as ground truth.")


if __name__ == "__main__":
    main()
