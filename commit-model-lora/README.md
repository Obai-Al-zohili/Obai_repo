---
base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct
library_name: peft
pipeline_tag: text-generation
tags:
- base_model:adapter:Qwen/Qwen2.5-Coder-1.5B-Instruct
- lora
- sft
- transformers
- trl
- commit-message-generation
- conventional-commits
---

# Offhand / Beemo — commit-model LoRA adapter

A LoRA fine-tune of **Qwen2.5-Coder-1.5B-Instruct** that writes
[Conventional Commits](https://www.conventionalcommits.org) messages from git diffs.
Given a unified diff, the model produces a single-line message such as
`feat: add retry logic for network requests` or `fix(auth): handle expired JWT tokens`.

This adapter is the core of [**Offhand**](https://marketplace.visualstudio.com/items?itemName=JesserLahmer.offhand),
a free VS Code extension that suggests a commit message after every `git add`, entirely offline.

---

## Model Details

### Model Description

- **Developed by:** Jesser Lahmer (university senior project, 2025–2026)
- **Model type:** Causal language model, LoRA adapter for parameter-efficient fine-tuning
- **Base model:** [Qwen/Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) (Alibaba Cloud, Apache 2.0)
- **Language(s):** English commit messages; diffs in any programming language
- **License:** CC BY-NC 4.0 (non-commercial), inherited from training data (CommitBench)
- **Fine-tuned from:** Qwen/Qwen2.5-Coder-1.5B-Instruct

### Model Sources

- **Repository:** [github.com/JesserLahmer/OffHand](https://github.com/JesserLahmer/OffHand)
- **Model on Hugging Face:** [Jess2005/commit-model-CLI](https://huggingface.co/Jess2005/commit-model-CLI)
  (the merged + quantized GGUF used by the extension)

---

## Uses

### Direct Use

Load the adapter on top of the base model and pass a formatted diff prompt.
The adapter is designed to be used with the exact prompt template from `diff_utils.py`:

```
Write a Conventional Commits message for this diff.

<unified diff, truncated to ~768 tokens>

Commit message:
```

The model continues from `Commit message:` and generates a single-line message.
Greedy decoding (`do_sample=False`, `max_new_tokens=40`) gives the most consistent results.

Quick example with the Beemo CLI:

```bash
pip install -e .
git add src/
beemo          # prints the suggested message; enter to confirm
```

Or with the Transformers library directly:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

base = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
adapter = "Jess2005/commit-model"  # or local path

tokenizer = AutoTokenizer.from_pretrained(base)
model = AutoModelForCausalLM.from_pretrained(
    base,
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    ),
    device_map="auto",
)
model = PeftModel.from_pretrained(model, adapter)
model.eval()

prompt = "Write a Conventional Commits message for this diff.\n\n<your diff>\n\nCommit message:"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=40, do_sample=False,
                         pad_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip())
```

### Downstream Use

The GGUF-quantized version (Q4_K_M, 986 MB) is served by
[llama.cpp](https://github.com/ggerganov/llama.cpp)'s `llama-server` inside the Offhand VS Code
extension. The extension reconstructs a raw diff from `git diff --cached`, formats the prompt,
and displays the model's first output line to the user.

### Out-of-Scope Use

- **Not suitable for commercial use** (CC BY-NC 4.0 license).
- Not designed to generate commit message bodies (multi-line descriptions); only the subject line is trained for.
- Not a general code-completion model; its outputs are unreliable outside the commit message domain.
- Should not be used as a classifier directly — it generates text, not logits over a label set.

---

## Bias, Risks, and Limitations

- **Type bias:** `fix` comprises about 53% of the training data. The model defaults to `fix` for
  ambiguous diffs and rarely predicts `build`, `ci`, `perf`, or `style` even when appropriate.
  This is the primary known quality issue. Rebalancing the training data (capping `fix` at ~12,000
  examples) is the next planned improvement.
- **Placeholder leakage:** 24% of CommitBench messages contain `<I>`, `<URL>`, `<EMAIL>` tokens
  from anonymisation. This adapter was trained on the unfiltered messages; the Beemo CLI strips
  these tokens at inference time via `postprocess.py`. Future fine-tunes will clean training labels.
- **English only:** all training messages are in English.
- **Subject-line only:** the model generates only the first line of a commit message.
- **Format dependency:** the prompt template is fixed. Using a different prompt format will produce
  degraded or incoherent output.

### Recommendations

Use the GGUF version via the Offhand extension or Beemo CLI rather than the raw adapter, as both
apply the correct prompt template and post-processing. If using the adapter directly, apply the
`clean_message` function from `src/commit_model/postprocess.py` to strip any remaining placeholders.

---

## How to Get Started with the Model

```bash
# Option 1: VS Code extension (recommended)
# Search "Offhand" in the VS Code Extensions panel.

# Option 2: Beemo CLI
git clone https://github.com/JesserLahmer/OffHand
cd OffHand
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e .
git add .
beemo
```

---

## Training Details

### Training Data

**CommitBench** — [Maxscha/commitbench](https://huggingface.co/datasets/Maxscha/commitbench)
(Maximilian Schall et al., CC BY-NC 4.0).

CommitBench contains ~1.17M real GitHub commits collected from popular open-source repositories.
Only examples satisfying all of the following were kept:

1. The commit message starts with a Conventional Commits prefix (`feat:`, `fix:`, `refactor:`, `chore:`,
   `docs:`, `test:`, `perf:`, `style:`, `build:`, or `ci:`).
2. The message is not in the low-content stoplist (e.g. "fix", "wip", "update", "typo").
3. The diff does not touch only lockfiles, minified files, or generated assets.
4. The diff is non-empty after truncation to `MAX_DIFF_CHARS = 4000` characters.

This filtering keeps about 5% of the raw dataset.

| Split | Examples |
|---|---|
| Train | 45,619 |
| Validation | 2,263 |
| Test | 9,704 |

The filter notebook is at [`notebooks/CommitBench_filter.ipynb`](../notebooks/CommitBench_filter.ipynb).

### Training Procedure

Fine-tuning was run on **Kaggle** with 2× T4 GPUs for approximately 2 hours.

#### LoRA configuration

| Hyperparameter | Value |
|---|---|
| PEFT method | LoRA |
| Rank (`r`) | 16 |
| Alpha (`lora_alpha`) | 32 |
| Dropout | 0.05 |
| Bias | none |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Task type | CAUSAL_LM |
| DoRA | No |
| RSLoRA | No |

#### Training hyperparameters

| Hyperparameter | Value |
|---|---|
| Epochs | 2 |
| Max sequence length | 768 tokens |
| Precision | bf16 mixed |
| Optimizer | AdamW (default TRL/SFTTrainer) |
| Framework | TRL `SFTTrainer`, PEFT 0.21.0, Transformers ≥ 4.46 |

The fine-tuning notebook is at [`notebooks/fine-tuning_Kaggle.ipynb`](../notebooks/fine-tuning_Kaggle.ipynb).

#### Speeds, Sizes, Times

- **Training time:** ~2 hours on Kaggle 2× T4
- **Adapter checkpoint size:** ~48 MB (rank-16 LoRA on 7 projection layers)
- **GGUF (Q4_K_M) size:** 986 MB (merged + quantized with llama.cpp b11476)

---

## Evaluation

### Testing Data

The held-out **CommitBench test split**: 9,704 examples, never seen during training.
A small overlap (~12 diffs, ~0.1%) with the train split was detected post-hoc and is noted here
for transparency; it does not materially affect the results.

### Metrics

| Metric | Description |
|---|---|
| **Valid-format rate** | Fraction of predictions that match the Conventional Commits regex |
| **Type accuracy** | Predicted type prefix (`feat`, `fix`, …) matches the reference |
| **BLEU** | Corpus-level BLEU (sacrebleu) against human-written messages |
| **ROUGE-L** | Longest common subsequence overlap |
| **METEOR** | Unigram F-score with stemming and synonymy via WordNet (added in the CommitSuite integration) |

Type accuracy is the most meaningful single metric for this task: BLEU and ROUGE-L measure wording
overlap, but commit messages for the same change can be phrased many valid ways.

### Results

**CommitBench test split — fp32 inference (9,704 examples)**

| Model | Valid format | Type accuracy | BLEU | ROUGE-L |
|---|---|---|---|---|
| Always `fix:` (majority baseline) | — | 53.3% | — | — |
| Base Qwen2.5-Coder-1.5B-Instruct | 1.9% | 0.9% | 0.5 | 0.022 |
| **Fine-tuned (this adapter)** | **99.9%** | **67.3%** | **19.4** | **0.328** |

**Per-type accuracy (fine-tuned model)**

| Type | Accuracy | Test examples |
|---|---|---|
| fix | 86.2% | 5,170 |
| chore | 37.7% | 1,043 |
| feat | 36.4% | 1,011 |
| test | 72.7% | 973 |
| refactor | 34.5% | 859 |
| docs | 74.6% | 358 |
| build | 23.5% | 102 |
| style | 6.9% | 101 |
| perf | 5.9% | 51 |
| ci | 11.1% | 36 |

**4-bit quantized model (Q4_K_M GGUF, 200-example sample)**

| Model | Valid format | Type accuracy | BLEU |
|---|---|---|---|
| Fine-tuned, fp32 | 99.5% | 67.5% | 16.67 |
| **Fine-tuned, Q4_K_M** | **99.5%** | **71.0%** | **16.45** |

No measurable quality loss from 4-bit quantization on this sample.

Full evaluation details and takeaways: [`results.md`](../results.md).
Evaluation notebook: [`notebooks/evaluate_Kaggle.ipynb`](../notebooks/evaluate_Kaggle.ipynb).

---

## Environmental Impact

- **Hardware:** Kaggle 2× NVIDIA T4 (16 GB VRAM each)
- **Hours used:** ~2 hours for fine-tuning
- **Cloud provider:** Kaggle (Google infrastructure)
- **Compute region:** not specified by Kaggle

---

## Technical Specifications

### Model Architecture and Objective

Base: **Qwen2.5-Coder-1.5B-Instruct** — a 1.5B-parameter decoder-only transformer optimised for
code understanding and generation. Fine-tuning uses **LoRA** (Low-Rank Adaptation), which adds
trainable low-rank matrices to the attention and MLP projection layers while freezing the base
weights. Only ~9M parameters are trained (~0.6% of the model).

Objective: next-token prediction (standard causal language modelling) on `(diff, message)` pairs.
The loss is computed only on the message tokens, not on the prompt.

### Compute Infrastructure

Training: Kaggle free-tier notebooks (2× T4, 16 GB VRAM each, internet-enabled).
Inference: llama.cpp `llama-server` with the Q4_K_M GGUF. Runs on CPU or any GPU supported by
llama.cpp (CUDA, Vulkan, Metal, SYCL).

---

## Citation

If you use this model, please cite CommitBench (the training data source):

```bibtex
@inproceedings{schall2024commitbench,
  title     = {CommitBench: A Benchmark for Commit Message Generation},
  author    = {Schall, Maximilian and Schweikert, Daniel and Sperl, Philip and B{\"o}ttinger, Konstantin},
  booktitle = {Proceedings of the 32nd International Conference on Program Comprehension (ICPC)},
  year      = {2024}
}
```

---

## Model Card Authors

Jesser Lahmer

### Framework versions

- PEFT 0.21.0
- Transformers ≥ 4.46
- TRL ≥ 0.11
- Python 3.12
