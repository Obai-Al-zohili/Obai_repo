# Plan

Goal: ship the fine-tuned model as a local commit-message tool that runs on any VS Code user's machine,
installed as one extension that handles the engine, model download, and running.

**Done:**
- Data filtering, LoRA fine-tuning, evaluation (`results.md`)
- Merge + 4-bit quantization, run locally; no measurable quality loss
- VS Code extension MVP (`vscode-extension/`): llama.cpp's `llama-server` as the engine,
  Start / Stop / Generate commands. Engine verified outside VS Code.

## 1. Finish the MVP
- **Done:** model on Hugging Face, downloaded on first start; packaged `.vsix` tested end to end.
- **Task:** try it by hand on real commits; update the model card on the Hugging Face repo.

## 2. Commit current work
- **Task:** commit the extension, notebooks, scripts, `results.md`, `plan.md`.

## 3. CI tests
- **Task:** GitHub Actions running on every push:
  - Python/TypeScript prompt parity: `diff_utils.py` and `prompt.ts` must build identical prompts
  - Extension compiles; engine smoke test with the model cached

## 4. Package and publish the extension
- **Task:** package the `.vsix`, test on Windows, macOS, and a machine without a GPU, then publish
  to the Marketplace.

## 5. Improve the model
- **Task:** in `notebooks/CommitBench_filter.ipynb`, cap `fix` examples and clean placeholder
  tokens from messages (`<I>`, `<URL>`, `<EMAIL>`); fine-tune again, compare with `results.md`,
  then re-merge, re-quantize, and upload.
- **Why:** the model labels too much as `fix` and never picks the rare types (`build`, `ci`, `perf`,
  `style`). 24% of training messages contain a placeholder.

## 6. Update the README
- **Task:** document the full workflow: data, training, evaluation, merge, quantize, extension.

## Later (optional)
- Auto-unload the model after idle time; use Ollama when it's already installed; message bodies for large diffs.
