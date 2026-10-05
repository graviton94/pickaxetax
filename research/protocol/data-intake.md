# Supplying sessions for the benchmark

How to get sessions from each product, and what happens to them. The analysis follows [backtest-v1.md](backtest-v1.md), which was frozen before any data arrived.

## Two ways to take part

1. **Run it yourself (preferred; nothing leaves your machine):**
   ```bash
   pip install pickaxetax
   pxt backtest run conversations.json --source chatgpt --contributor <any-label>
   ```
   Send only `backtest-report.json`. It holds numbers, not text. Keep `backtest-manifest.txt`: its digest in the report lets you prove later which files were used.
2. **Hand the files to the maintainer.** They are processed on one machine, never committed and never uploaded anywhere else, and deleted after the run. The published report is the same as in option 1.

Several runs (several people, several products) are combined by stratum. Each run counts as one contributor.

## Where to get the files

| Product | What to export | Notes |
|---|---|---|
| ChatGPT | Settings → Data controls → Export data. The e-mailed zip contains `conversations.json` | Supported |
| Claude | Settings → Privacy → Export data. The zip contains `conversations.json` | Supported |
| Gemini (API / AI Studio) | Saved prompt or chat history JSON with `contents` / `parts` | Supported |
| Gemini app | Google Takeout export | **Adapter built from your first sample.** Send one, with anything private removed |
| Grok | The export from your account's data settings, or share pages | **Adapter built from your first sample** |
| Any product | A transcript with `User:` / `Assistant:` markers, or an OpenAI-style `messages` list | Supported (use `--source` to label it) |
| Claude Code | `~/.claude/projects/<project>/<session>.jsonl` | Supported, with measured usage |
| Codex CLI, Gemini CLI, other agents | Session log files | **Adapter built from your first sample** |

Adapters are never written from guesses about a format. The first real sample defines them, and they get a test from a redacted copy.

## Rules

- **Label the source** with `--source` when a file's format doesn't identify the product (OpenAI-style lists, plain transcripts).
- **Nothing is excluded after the fact.** Every session with at least 3 replies counts, including the ones that make the result look worse.
- **Mixed products in one file:** split them into separate files, so each gets its own label.
- **Before publication** the use detector is checked by hand on at least 100 pairs. Use `pxt backtest label` in a terminal. Without a terminal, `pxt backtest label --sheet sheet.md` writes a local sheet, and `pxt backtest answer key.json "1y 2n …"` applies the answers. The sheet contains text, so it stays local and is deleted afterwards; only the answers and pair ids are kept.
