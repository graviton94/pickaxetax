# Contributing

This project runs on **minimal cost and global contribution**. There are no paid servers to keep alive. The compute comes from contributors' own machines, and the data lives in git. Every kind of help below is useful, and most of it costs you nothing.

## Ways to contribute

### 1. Run the proxy and share your ledger (zero cost)

```bash
pip install -e .
pickaxetax proxy                       # OpenAI-compatible at http://127.0.0.1:8787/v1
                                        # Anthropic SDK: base_url="http://127.0.0.1:8787"
pickaxetax ledger                      # what was spent, re-sent and avoided
pickaxetax ledger --export > my-ledger.json   # anonymous daily aggregates, no text
```

The ledger holds counts only: no prompts, no replies, no keys. Share the export in an issue to feed the usage layer (W) of the [Compute Bubble Index](docs/BUBBLE_INDEX.md).

### 1b. Audit your coding agent (zero cost)

```bash
pxt agent audit                         # Claude Code transcripts in ~/.claude/projects
pxt agent audit --export > agent.json   # anonymous counts only: no paths, commands or ids
```

Using another agent (Codex CLI, Aider, Cline, Cursor…)? Adapters are built from real samples, never guessed. Open an issue with a **redacted** session log that shows the structure, and we'll add support.

### 2. Donate benchmark compute (zero cost with a local model)

Over-computation (CBI layer M) is measured by running a small set of trivial tasks once per model and setting.

```bash
# free: any local OpenAI-compatible server, e.g. Ollama
pickaxetax bench run --base-url http://localhost:11434 --model llama3.2
# or a hosted model with your own key
pickaxetax bench run --base-url https://api.openai.com --model <model> --api-key-env OPENAI_API_KEY
```

The result is written to `bench/results/<model>__<settings>__<taskset>.json`. Open a PR to add it. If a result for the same model, settings and task set already exists, the runner refuses to run again, because a duplicate measurement would itself be waste. Check `bench/results/` first and pick a model that isn't there yet. CI validates every submitted file.

### 3. Curate CBI data (capital and utilization layer)

Add sourced rows to `cbi/drafts.csv`. Rows move to `cbi/capital.csv` once a second person has verified them against the primary source. The rules are in [cbi/README.md](cbi/README.md).

### 4. Code, translation and research

- Code: see the open issues and the roadmap in [docs/CHARTER.md](docs/CHARTER.md). Run `pytest` before opening a PR.
- The analysis engine exists twice: Python (`pickaxetax/`) and browser JavaScript (`site/engine.js`). Change both together. `tests/test_parity.py` fails if their outputs differ. For UI changes to the static site, run the optional browser check: `PWPATH=$(npm root -g)/playwright node tests/e2e/site_e2e.mjs`.
- Translation: the UI strings are in `pickaxetax/web/static/app.js` (`T`), and the docs are in `docs/`.
- Research: methodology critiques of the index and the benchmark are very welcome. Open an issue with your reasoning and data.

## Operating principles

- **Local first.** Raw text and compute stay on the contributor's machine.
- **Measure once.** Don't re-run what has already been measured.
- **Static first.** Use static hosting and free CI tiers. Paid infrastructure is added only when it is proven necessary, and its cost is published.
- **Sourced or it didn't happen.** Every public number carries a source and a grade (measured, reported or estimated).
