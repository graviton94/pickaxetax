# Reddit

Post one per day. Read each subreddit's rules first (self-promotion ratio, flair). Lead with the finding and the free tool; stay in the comments.

## r/ClaudeAI — flair: Tool / Project

**Title:** I audited a long Claude Code session: 43.5M input tokens read to write ~350K. Free tool to check your own sessions.

**Body:**
Claude Code keeps every tool result in context and re-reads it on every call until compaction. I wanted to see what that adds up to, so I wrote an auditor for the local transcripts (`~/.claude/projects/*.jsonl`).

One real session:
- 143 API calls, 176 tool calls
- 43,477,948 input tokens processed, 97.8% cache hits
- peak context 507,710 tokens
- ~350K output tokens

One gotcha if you parse these yourself: a single response is written as several lines that repeat the same `usage`, so naive sums overcount by about 3×. The tool de-duplicates by message id.

`pip install pickaxetax && pxt agent audit` shows cache hits, peak context, re-reads of unchanged files, huge tool outputs, repeated failures, and how many times each result was re-sent afterwards. There's also an optional guard hook (or `/plugin install pickaxetax@pickaxetax` after adding the marketplace `graviton94/pickaxetax`). It blocks a re-read of an unchanged file once; asking again allows it, and compaction resets it.

Everything is local and counts-only. Open source (Apache-2.0): https://github.com/graviton94/pickaxetax

Curious what your sessions look like. Especially the peak context.

## r/LocalLLaMA — flair: Resources

**Title:** Free local proxy that measures every LLM request and skips the ones that don't need a model (OpenAI-compatible, works with Ollama)

**Body:**
`pxt proxy` sits in front of any OpenAI-compatible server (Ollama, llama.cpp, vLLM, LM Studio) or Anthropic's API. For every request it logs the input, output, reasoning and re-sent-context tokens. It stores counts only, never prompts or responses.

By default it does two conservative things:
- answers a bare "thanks" locally instead of re-reading the whole chat (never "ok"/"yes", never with tools, never after the assistant asked a question)
- drops earlier pure thank-you exchanges from the history

Opt-in: an exact-duplicate cache for temperature-0 requests.

There's also a tiny over-computation benchmark: 30 trivial questions that need no reasoning, run once per model. It shows how many tokens (visible + reasoning) a model burns on "What is 17 + 25?". It's crowd-run on free local models and refuses to re-run a model/setting that's already been measured.

`pip install pickaxetax` · https://github.com/graviton94/pickaxetax (Apache-2.0)

## r/ChatGPT — flair: Resources / Use cases

**Title:** Your "thanks!" at the end of a long chat makes the model re-read the whole thing. I made a free page that shows how much of a chat was avoidable.

**Body:**
Every reply re-processes the entire conversation. So late requirements, re-asks, topic switches in one chat and the polite "thanks" at the end all cost far more than they look.

Paste a conversation (or use the share-link bookmarklet) and you get:
- where the compute went: thank-yous, discarded answers, unrelated topics re-sent
- the conversation's structure (topic threads and depth)
- a one-shot prompt that would have gotten the same result in one go

It runs entirely in your browser. The page technically can't upload anything (strict Content-Security-Policy, and you can check it in devtools).

https://graviton94.github.io/pickaxetax/

The example chat comes out at 61.8% avoidable. What's yours?
