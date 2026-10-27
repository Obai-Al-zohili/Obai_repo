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

# AI Commit Message Generator — LoRA Adapter

A LoRA fine-tune of **Qwen2.5-Coder-1.5B-Instruct** that writes
[Conventional Commits](https://www.conventionalcommits.org) messages from git diffs.
Given a unified diff, the model produces a single-line message such as
`feat: add retry logic for network requests` or `fix(auth): handle expired JWT tokens`.

---

## Model Details

### Model Description

- **Developed by:** Obai Al-zohili (university senior project, 2025–2026)
- **Model type:** Causal language model, LoRA adapter for parameter-efficient fine-tuning
- **Base model:** [Qwen/Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) (Alibaba Cloud, Apache 2.0)
- **Language(s):** English commit messages; diffs in any programming language
- **License:** CC BY-NC 4.0 (non-commercial), inherited from training data (CommitBench)
- **Fine-tuned from:** Qwen/Qwen2.5-Coder-1.5B-Instruct

### Model Sources

- **Repository:** [github.com/Obai-Al-zohili/Obai_repo](https://github.com/Obai-Al-zohili/Obai_repo)

---

## Uses

### Direct Use

Load the adapter on top of the base model and pass a formatted diff prompt.
Prompt template:

```
Write a Conventional Commits message for this diff.

<unified diff, truncated to ~768 tokens>

Commit message:
```

Greedy decoding (`do_sample=False`, `max_new_tokens=40`) gives the most consistent results.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

base = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
adapter = "./commit-model-lora"  # local path

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

### Out-of-Scope Use

- **Not suitable for commercial use** (CC BY-NC 4.0 license).
- Not designed to generate multi-line commit message bodies; only the subject line is trained for.
- Not a general code-completion model.

---

## Bias, Risks, and Limitations

- **Type bias:** `fix` comprises about 53% of the training data. The model defaults to `fix` for
  ambiguous diffs and rarely predicts `build`, `ci`, `perf`, or `style`.
- **Placeholder leakage:** 24% of CommitBench messages contain `<I>`, `<URL>`, `<EMAIL>` tokens.
  The CLI strips these at inference time. Future fine-tunes clean training labels directly.
- **English only:** all training messages are in English.
- **Subject-line only:** generates only the first line of a commit message.

---

## Training Details

### Training Data

**CommitBench** — [Maxscha/commitbench](https://huggingface.co/datasets/Maxscha/commitbench) (CC BY-NC 4.0).

Filtering kept ~5% of the raw 1.17M-row dataset:

| Split | Examples |
|---|---|
| Train | ~45 000 |
| Validation | ~2 300 |
| Test | 9 704 |

Filter notebook: [`notebooks/CommitBench_filter.ipynb`](../notebooks/CommitBench_filter.ipynb)

### Training Procedure

Fine-tuning was run on **Kaggle** with 2× T4 GPUs for approximately 2 hours.

#### LoRA configuration

| Hyperparameter | Value |
|---|---|
| Rank (`r`) | 16 |
| Alpha (`lora_alpha`) | 32 |
| Dropout | 0.05 |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Task type | CAUSAL_LM |

#### Training hyperparameters

| Hyperparameter | Value |
|---|---|
| Epochs | 2 |
| Max sequence length | 768 tokens |
| Precision | bf16 mixed |
| Framework | TRL `SFTTrainer`, PEFT 0.21.0 |

---

## Evaluation

### Results

**CommitBench test split — fp32 inference (9 704 examples)**

| Model | Valid format | Type accuracy | BLEU | ROUGE-L |
|---|---|---|---|---|
| Always `fix:` (majority baseline) | — | 53.3% | — | — |
| Base Qwen2.5-Coder-1.5B-Instruct | 1.9% | 0.9% | 0.5 | 0.022 |
| **Fine-tuned (this adapter)** | **99.9%** | **67.3%** | **19.4** | **0.328** |

**Per-type accuracy (fine-tuned)**

| Type | Accuracy | Test examples |
|---|---|---|
| fix | 86.2% | 5 170 |
| chore | 37.7% | 1 043 |
| feat | 36.4% | 1 011 |
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

No measurable quality loss from 4-bit quantization.

---

## Environmental Impact

- **Hardware:** Kaggle 2× NVIDIA T4
- **Hours used:** ~2 hours for fine-tuning

---

## Citation

If you use this model, please cite CommitBench:

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

Obai Al-zohili

### Framework versions

- PEFT 0.21.0
- Transformers ≥ 4.46
- TRL ≥ 0.11
- Python 3.11+
