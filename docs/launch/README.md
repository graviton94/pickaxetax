# Launch kit

Channels: **X**, **LinkedIn** and **Reddit**. The drafts are ready to post from the maintainer's accounts; every number in them is reproducible (see "Facts" below).

## Before posting (one time)
- [ ] The web app loads at https://graviton94.github.io/pickaxetax/. Click "Try an example", then Analyze.
- [ ] The link preview shows the OG card. Check it in the X or LinkedIn post composer.
- [ ] Optional: the Cloudflare secrets are set, so the *Contribute anonymously* button is live.
- [ ] Optional: the repository description, topics and website are set (see ADR-0007).

## Order
1. **Day 0, morning (US East, Tue–Thu):** post the X thread, then LinkedIn the same day.
2. **Day 0–1:** Reddit, one subreddit per day and never cross-posted at once. Start with r/ClaudeAI (agent audit, where the evidence is strongest), then r/LocalLLaMA (proxy and benchmark with free local models), then r/ChatGPT (the web app).
3. Reply to every comment within the first 3 hours. Answer criticism with numbers; the FAQ has prepared answers.
4. Day 7: post a follow-up with the first public aggregate numbers from contributions.

## Facts (sources for every number in the drafts)
| Claim | Source |
|---|---|
| 61.8% avoidable in the example chat (367 → 140 compute units) | web app → "Try an example" (English sample) |
| One coding session: 143 API calls, 43,477,948 input tokens processed, 97.8% cache hits, 507,710 peak context, ~350K output | `pxt agent audit` on one real Claude Code session (anonymized) |
| Without de-duplication, transcript usage is overcounted ~3× | 126 of 140 responses were split across lines in the same session (ADR-0005) |
| The web app cannot upload | CSP `connect-src 'none'`, verified in CI (`tests/e2e/site_e2e.mjs`) |

## Rules of engagement
- Don't overclaim. "Avoidable" means *the same results with one focused chat per topic and no waste*, and the definition is in the app. Energy figures are labeled as estimates.
- Never ask for upvotes. On Reddit, follow each subreddit's self-promotion rules, use the right flair, and lead with the free tool and the finding, not the pitch.
- Credit critics publicly when they're right, and open an issue for each valid point.
