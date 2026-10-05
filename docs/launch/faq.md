# FAQ: answers to likely criticism

**"Prompt caching already makes re-reads cheap."**
Cheaper, yes, but not free. Cache reads are priced at a fraction of normal input, and caches expire (minutes to an hour), after which the next turn pays full price. The compute to serve a cached prefix isn't zero either. We report cache hits separately (e.g. 97.8% in the audited session) and never count cached tokens as "waste" by themselves. The waste is the history you didn't need to keep growing.

**"Short-circuiting 'thanks' is trivial or creepy."**
It's opt-out (`--no-gratitude`), it runs on your machine, and the reply says it was answered locally. "ok" and "yes" are never short-circuited, because in agent workflows they mean "go ahead". It's a small example of a big habit: a polite closing message can cost as much as the whole conversation.

**"Your token counts are estimates."**
Where the provider reports usage (the proxy, the agent transcripts), we use it and label it *measured*. Elsewhere we estimate and label it *estimated*. The "verified savings" metric counts only what can be verified.

**"'Avoidable' is arbitrary."**
It has a fixed definition: the same useful exchanges, one focused chat per topic, without thank-you round trips and without answers that were thrown away by corrections. We also show a one-shot lower bound. Both definitions are documented and computed by open code.

**"The 'compute bubble' framing is speculative."**
The index reports measured gaps, not opinions. Every number carries a source and a grade (measured, reported or estimated). The capital dataset ships empty on purpose: rows are added only with primary sources and a second person's verification.

**"Why should I trust you with my conversations?"**
You don't have to. The web app's Content-Security-Policy blocks all outgoing requests (check it in devtools, and CI verifies it in a real browser). The proxy and auditor store counts only. Contributions are allowlisted numbers that you preview before sending. It's all open source.

**"Is this anti-AI?"**
No. It's pro-efficiency. The people who pay the pickaxe tax are AI users and AI companies. Using the compute we already have well is how AI gets cheaper, greener and more available.

**"Why doesn't the analyzer use an LLM?"**
Because a tool about saving tokens shouldn't spend them. It uses rule-based intent classification, keyword ranking and SimHash, and it runs in milliseconds.
