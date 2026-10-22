"""Evaluate a fine-tuned adapter on the held-out CommitBench test split.

Reports: type-prefix accuracy (did we predict the right feat/fix/refactor/... type),
BLEU, ROUGE-L, METEOR, valid-format rate, per-type accuracy breakdown,
per-type precision/recall/F1, confusion matrix, and (when comparing base vs adapter)
a McNemar significance test.

Prefix accuracy is the metric to trust most here; BLEU/ROUGE/METEOR are tracked
mainly as a between-checkpoint regression signal.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# ---------------------------------------------------------------------------
# Optional heavy imports — fail gracefully if packages not installed
# ---------------------------------------------------------------------------
try:
    import nltk
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)
    from nltk.translate.meteor_score import meteor_score as _meteor_score
    _HAS_NLTK = True
except ImportError:
    _HAS_NLTK = False

try:
    from sklearn.metrics import precision_recall_fscore_support, confusion_matrix as sk_confusion_matrix
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    _HAS_PLOT = True
except ImportError:
    _HAS_PLOT = False

import evaluate
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from commit_model.diff_utils import (
    VALID_RE,
    extract_type,
    fit_prompt,
    mcnemar_p,
)

DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
DEFAULT_ADAPTER_PATH = "checkpoints/commit-model-lora"

# Ordered by test-set frequency from results.md
LABELS = ["fix", "feat", "chore", "test", "refactor", "docs", "build", "style", "perf", "ci"]


def load_model(base_model: str, adapter_path: str | None):
    """Base model in 4-bit, plus the LoRA adapter unless adapter_path is None."""
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base_model, quantization_config=bnb_config, device_map="auto"
    )
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    return model, tokenizer


def generate_message(model, tokenizer, prompt: str, max_new_tokens: int = 40) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.pad_token_id,
        )
    text = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return (text.strip().splitlines() or [""])[0].strip()


def compute_per_type_metrics(predictions, references):
    """Compute per-type precision/recall/F1 using sklearn, filtered to known LABELS."""
    pred_types = [extract_type(p) for p in predictions]
    ref_types = [extract_type(r) for r in references]

    # Keep only examples where the reference type is a known label
    valid_idx = [i for i, t in enumerate(ref_types) if t in LABELS]
    filtered_pred = [pred_types[i] if pred_types[i] in LABELS else "__unknown__" for i in valid_idx]
    filtered_ref = [ref_types[i] for i in valid_idx]

    precision, recall, f1, support = precision_recall_fscore_support(
        filtered_ref, filtered_pred, labels=LABELS, average=None, zero_division=0
    )
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        filtered_ref, filtered_pred, average="macro", zero_division=0
    )
    return precision, recall, f1, support, macro_p, macro_r, macro_f1


def generate_confusion_matrix(predictions, references, output_path: str):
    """Save a confusion-matrix PNG for the ten commit types."""
    pred_types = [extract_type(p) for p in predictions]
    ref_types = [extract_type(r) for r in references]

    valid_idx = [i for i, t in enumerate(ref_types) if t in LABELS]
    filtered_pred = [pred_types[i] if pred_types[i] in LABELS else "__unknown__" for i in valid_idx]
    filtered_ref = [ref_types[i] for i in valid_idx]

    cm = sk_confusion_matrix(filtered_ref, filtered_pred, labels=LABELS)

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Reds",
        xticklabels=LABELS, yticklabels=LABELS,
        cbar=False, linewidths=0.5,
    )
    plt.xlabel("Predicted Label", fontsize=14)
    plt.ylabel("True Label", fontsize=14)
    plt.xticks(rotation=45, ha="right", fontsize=11)
    plt.yticks(rotation=0, fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--adapter-path", default=DEFAULT_ADAPTER_PATH)
    parser.add_argument(
        "--no-adapter",
        action="store_true",
        help="evaluate the base model alone, as a baseline",
    )
    parser.add_argument("--test-file", default="data/processed/test.jsonl")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    examples = [json.loads(l) for l in Path(args.test_file).read_text().splitlines()][: args.limit]

    # When comparing base vs adapter, load both
    if args.no_adapter:
        model, tokenizer = load_model(args.base_model, None)
        base_model_obj = model
        adapter_model_obj = None
    else:
        # Load base first for McNemar comparison, then load with adapter
        base_model_obj, tokenizer = load_model(args.base_model, None)
        adapter_model_obj, _ = load_model(args.base_model, args.adapter_path)

    predictions, references = [], []
    base_predictions = []
    type_correct = 0

    for ex in examples:
        prompt = fit_prompt(tokenizer, ex["diff"])

        if args.no_adapter:
            pred = generate_message(base_model_obj, tokenizer, prompt)
        else:
            pred = generate_message(adapter_model_obj, tokenizer, prompt)
            base_pred = generate_message(base_model_obj, tokenizer, prompt)
            base_predictions.append(base_pred)

        predictions.append(pred)
        references.append(ex["message"])
        if extract_type(pred) == extract_type(ex["message"]):
            type_correct += 1

    bleu_metric = evaluate.load("sacrebleu")
    rouge_metric = evaluate.load("rouge")
    bleu_score = bleu_metric.compute(predictions=predictions, references=[[r] for r in references])
    rouge_score = rouge_metric.compute(predictions=predictions, references=references)

    # --- METEOR ---
    if _HAS_NLTK:
        meteor_scores = [
            _meteor_score([r.lower().split()], p.lower().split())
            for p, r in zip(predictions, references)
        ]
        avg_meteor = sum(meteor_scores) / len(meteor_scores)
    else:
        avg_meteor = None

    # --- Valid-format rate ---
    valid_format = sum(bool(VALID_RE.match(x)) for x in predictions) / len(predictions)

    # --- Print header ---
    model_label = args.base_model + ("" if args.no_adapter else f" + {args.adapter_path}")
    print(f"Model: {model_label}")
    print(f"Examples evaluated: {len(examples)}")
    print(f"Type-prefix accuracy: {type_correct / len(examples):.1%}")
    print(f"Valid-format rate:    {valid_format:.1%}")
    print(f"BLEU:    {bleu_score['score']:.2f}")
    print(f"ROUGE-L: {rouge_score['rougeL']:.3f}")
    if avg_meteor is not None:
        print(f"METEOR:  {avg_meteor:.3f}")
    else:
        print("METEOR:  (nltk not installed — pip install nltk)")

    # --- Per-type accuracy breakdown ---
    ref_types = [extract_type(r) for r in references]
    print("\nType accuracy by type:")
    for t, n in Counter(ref_types).most_common():
        hits = sum(
            extract_type(x) == t
            for x, rt in zip(predictions, ref_types)
            if rt == t
        )
        print(f"  {t:<10}{n:>6}  {hits / n:6.1%}")

    # --- McNemar test (only when both base and adapter predictions are available) ---
    if not args.no_adapter and base_predictions:
        base_ok = [extract_type(x) == t for x, t in zip(base_predictions, ref_types)]
        adapter_ok = [extract_type(x) == t for x, t in zip(predictions, ref_types)]
        only_base = sum(a and not b for a, b in zip(base_ok, adapter_ok))
        only_adapter = sum(b and not a for a, b in zip(base_ok, adapter_ok))
        p_value = mcnemar_p(only_base, only_adapter)
        print(f"\nType right only in base: {only_base}, only in adapter: {only_adapter}")
        print(f"McNemar p = {p_value:.3f} — {'significant change' if p_value < 0.05 else 'no significant change'} in type accuracy")
    else:
        print("\n(McNemar test skipped — run without --no-adapter to compare base vs adapter)")

    # --- Per-type P/R/F1 and confusion matrix ---
    if _HAS_SKLEARN:
        precision, recall, f1, support, macro_p, macro_r, macro_f1 = compute_per_type_metrics(
            predictions, references
        )
        print("\nPer-type classification metrics:")
        print(f"  {'Type':<12}{'Prec':>8}{'Recall':>8}{'F1':>8}{'Support':>10}")
        for i, label in enumerate(LABELS):
            print(f"  {label:<12}{precision[i]:>8.3f}{recall[i]:>8.3f}{f1[i]:>8.3f}{int(support[i]):>10}")
        print(f"  {'Macro avg':<12}{macro_p:>8.3f}{macro_r:>8.3f}{macro_f1:>8.3f}")

        if _HAS_PLOT:
            cm_path = "type_confusion_matrix.png"
            generate_confusion_matrix(predictions, references, cm_path)
            print(f"\nConfusion matrix saved to {cm_path}")
        else:
            print("\n(Confusion matrix PNG skipped — pip install matplotlib seaborn)")
    else:
        print("\n(Per-type P/R/F1 skipped — pip install scikit-learn)")

    print("\nSample predictions:")
    for pred, ref in list(zip(predictions, references))[:10]:
        print(f"  pred: {pred}\n  ref:  {ref}\n")


if __name__ == "__main__":
    main()
