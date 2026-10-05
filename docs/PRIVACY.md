# Privacy design / 개인정보 설계

## What is stored / 저장하는 것

| Stored | Not stored |
|---|---|
| Token counts, intents, depth and branch per turn | Any message text |
| Topic labels (PII-scrubbed keywords) | Titles, names, URLs, emails, numbers |
| Typed edges between turns | Code blocks (only a `has_code` flag) |
| Salted 64-bit SimHash per turn | IP addresses, or any link between an upload and a person |
| Aggregate metrics | The share URL itself |

## Safeguards / 안전장치

1. **Text is processed in memory only.** `RawConversation.turns` is cleared right after analysis, and `RawConversation.__repr__` hides the text so it can't leak into logs or tracebacks. Error messages never echo input (covered by a test).
2. **PII scrubbing runs before keyword extraction**, covering emails, URLs, IPs, phone, card and ID numbers, API-key-like strings and long opaque tokens.
3. **Rare-word filter.** A word mentioned once and never echoed by the assistant does not become a stored label. Personal details are usually like this.
4. **Salted identifiers.** Conversation IDs and fingerprints are HMAC'd or keyed with a per-deployment secret, so nobody holding a transcript can check whether it was uploaded.
5. **k-anonymity on public views.** A topic and its co-occurrence edges appear in `/api/topics` and Cypher exports only after ≥ k distinct conversations (default 3). The API cannot lower k.
6. **Consent and withdrawal.** Contribution is opt-in per upload. Opting out stores nothing. Every contribution gets a one-time delete token (only its hash is stored). Deleting it removes the turns and edges and decrements the topic and co-occurrence counts exactly.
7. **No tracking.** No cookies, no analytics, `Referrer-Policy: no-referrer` and `Cache-Control: no-store`. The browser keeps delete tokens in localStorage only.

## Known limits / 알려진 한계

- Topic labels are still words from the conversation. A person whose rare project name is frequently discussed could appear as a label once k conversations mention it. Planned mitigations: client-side extraction, differential privacy for aggregates, and a reviewed label vocabulary.
- Share-link fetching sends a request to the AI provider from the server. Uploading an export or pasting the text avoids that.
- Running your own instance gives you full control: `antitoken serve` with a local DB.
