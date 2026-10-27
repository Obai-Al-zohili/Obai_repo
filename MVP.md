# VS Code Extension MVP

Goal: the easiest possible experience. Install one VS Code extension; it downloads the engine and the
model itself, runs fully offline, and turns staged changes into commits with one keystroke.

## Workflow

Everything happens in VS Code's terminal, only right after `git add`. Nothing pops up in the editor.

1. **Bottom-left toggle:** turns the model on (starts the server) or off (stops it and frees memory).
   Download and loading progress show in the toggle itself.
2. **In the terminal**, after a successful `git add` while it's on:
   ```
   $ git add .
   Suggests:  feat: add subtract function
   Commit with this message? [Y/N] y
   ✓ Committed 3f2a1bc  feat: add subtract function
   ```
   - **Y:** runs `git commit` with the suggestion.
   - **N:** asks `Your commit message (empty to cancel):` and commits that; empty cancels.
3. **Nothing staged** after `git add`: it says so and reminds you to save.

## Engine

llama.cpp's `llama-server`, run as a separate process. On first start the extension downloads
the build for the user's system (Vulkan/Metal/CPU) and the model (~986 MB), then runs the server
in the background. A watchdog stops the server when VS Code's extension process ends.

Generation settings match training: plain prompt (no chat template), greedy decoding, first line
only, diff truncated to fit 768 tokens.

## Suggestion cleanup

Raw model output is cleaned before display (`cleanMessage` in `src/postprocess.ts`, mirrored by
`clean_message` in `src/commit_model/postprocess.py`):

- CommitBench placeholder tokens removed (`<I>`, `<URL>`, `<EMAIL>`, `<HASH>`)
- Consistent lowercase start (acronyms and names are kept)

## Code layout

`vscode-extension/`:

| File | Role |
|---|---|
| `src/extension.ts` | toggle, status bar, ✨ button, activity log |
| `src/terminalSetup.ts` | git wrapper on terminals' PATH, on/off state |
| `src/terminal.ts` | terminal prompt: suggestion, Y/N, commit |
| `src/engine.ts` | downloads and runs llama-server, GPU/CPU fallback |
| `src/client.ts` | talks to llama-server: tokenizing, generating |
| `src/postprocess.ts` | suggestion cleanup |
| `src/prompt.ts` | diff filtering and prompt building (mirrors `diff_utils.py`) |

## Testing

| Command | What it runs |
|---|---|
| `npm run test:integration` | full workflow in a real VS Code |
| `npm run test:unit` | cleanup rules (no model) |
| `python -m unittest tests.test_postprocess` | Python cleanup, same cases |
| `npm run test:smoke` | engine alone, outside VS Code |

## Known limitations

- Right type 6/10 on manual scenarios: rare types (`build`, `ci`, `perf`, `style`) get a common type.
- 24% of training messages contain CommitBench placeholders — cleaned at inference, proper fix is
  cleaning training labels (see `plan.md` step 5).
