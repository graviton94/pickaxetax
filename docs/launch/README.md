# Launch kit

Channels: **X**, **LinkedIn** and **Reddit**. The drafts are ready to post from the maintainer's accounts; every number in them is reproducible (see "Facts" below).

## Before posting (one time)
- [ ] The web app loads at https://graviton94.github.io/pickaxetax/. Click "Try an example", then Analyze.
- [ ] The link preview shows the OG card. Check it in the X or LinkedIn post composer.
- [ ] Optional: the Cloudflare secrets are set, so the *Contribute anonymously* button is live.
- [ ] Optional: the repository description, topics and website are set (see ADR-0007).

## Order
The project is published as **LinkedIn research notes, one at a time**, written together as the research progresses (ADR-0009). The current state is in [linkedin-series/](linkedin-series/README.md). When the tool goes public, and when the X thread and Reddit posts follow, is decided along the way. The checklist above must be done before any post links to the site.

- Reply to every comment within the first 3 hours. Answer criticism with numbers; the FAQ has prepared answers.
- Reddit: one subreddit per day, never cross-posted at once, following each subreddit's self-promotion rules.

`linkedin.md` and `x-thread.md` are kept as material.

## Facts (sources for every number in the drafts)
| Claim | Source |
|---|---|
| 61.8% avoidable in the example chat (367 → 140 compute units) | web app → "Try an example" (English sample) |
| One coding session: 143 API calls, 43,477,948 input tokens processed, 97.8% cache hits, 507,710 peak context, ~350K output | `pxt agent audit` on one real Claude Code session (anonymized) |
| Without de-duplication, transcript usage is overcounted ~3× | 126 of 140 responses were split across lines in the same session (ADR-0005) |
| The web app cannot upload | CSP `connect-src 'none'`, verified in CI (`tests/e2e/site_e2e.mjs`) |
| ~124 input tokens read per output token (same session) | 43,477,948 ÷ 349,743 |
| KV cache ≈ 320 KiB per token on an open 70B-class model; 507,710 tokens ≈ 166 GB | 2 × 80 layers × 8 KV heads × 128 dims × 2 bytes = 327,680 B; × 507,710 = 1.66 × 10¹¹ B (illustration, stated as such) |
| Read amplification 195× | `research/hypotheses.md` H0 (226 calls, 94,880,088 in / 485,860 out) |
| Naive dead-context test: 1% dead; refined: 54% never echoed (upper bound) | `research/hypotheses.md` H1, H1′ |
| Task-scoped sessions with a short summary: 66–70% less input | `research/hypotheses.md` H2 |
| Survey user01 (report): ≥ 5,871,292,005 input tokens over 10 sessions (1.49× the session-list total); 586 instructions, ~1,000만/instruction; top 5 sessions 93.3%; top 10% of 255 instructions use 45.6%; carried-over context 73.6%; largest instruction 219,620,777; output < 1% of input (S01–S03: 0.19–0.43%) | `research/survey/user01/` |
| Note 1 session A (snapshot 7b91c8fa…): 400 calls, 169,482,468 input, 729,447 output (1:232); forget 11.0%, page 49.9%, unjudgeable 42.0%; same report on two runs; order holds in 18 cells | `research/results/note01-session-a.json`, `pxt agent audit` |
| Bound session: 322 calls, 149,273,256 input tokens; forget 9.1%, page 50.1% (47.5% at 1k, 34.7% at 10k); invisible 32.4%; base 10.1%; ceiling 57.5%; persisted writes 25.1% of resident context | `research/results/belady-session-01.json`, `research/belady-bound.md` §4 |
| Paging beats forgetting by ≥ 18 points in every calibrated sensitivity cell | same file, `sensitivity_avoidable_pct` |
| Carbon (estimate, stated as such): one call re-reading 427,524 tokens ≈ 24 Wh, 10.8 g CO₂ ≈ one tree's 16 hours ≈ burning a 6 g dry twig; user01 ≈ 333 kWh, 148 kg CO₂ ≈ one tree's 25 years (×10 without the cache discount) | `research/carbon-factors.md`, `pickaxetax/survey/carbon.py` (Jegham et al. 2025; Anthropic cache price ratio; IEA 445 g/kWh; EPA 60 kg per tree in 10 years; IPCC 0.47 carbon fraction) |

## Rules of engagement
- Don't overclaim. "Avoidable" means *the same results with one focused chat per topic and no waste*, and the definition is in the app. Energy figures are labeled as estimates.
- Never ask for upvotes. On Reddit, follow each subreddit's self-promotion rules, use the right flair, and lead with the free tool and the finding, not the pitch.
- Credit critics publicly when they're right, and open an issue for each valid point.
