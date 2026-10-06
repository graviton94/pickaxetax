> Working memo from cycle E3 of `research/phase2/log.md`, written by an analysis agent and reviewed there. Numbers only; computed from the private transcripts at the dataset-v2 snapshots.

# E3 - dependence on the lexical reuse detector

Method. Own module (e3.py, run.py in this folder; repo untouched) re-parses the 10 sessions exactly as bound.read_trace_lines
does (checked: V0 reproduces the published figures), swaps the tokenizer / linker, then calls bound.calibrate and bound.bound
unchanged; pooled with bound.merge. Defaults min_shared=1, common_frac=0.02, calibrated. Percent = share of measured input.

Outputs that count as "use" (existing behaviour, so V3 == V1): assistant text blocks and the JSON of every tool_use input
(including Write/Edit/MultiEdit content). Not counted: thinking, tool results, user prompts.

## Table (pooled, 10 sessions)
| Variant | P=inf | P=1000 | P=0 | carried dead | carried idle | paging gain (1000 - inf) | token share of residency with a later use |
|---|---:|---:|---:|---:|---:|---:|---:|
| V0 lexical-v1 | 5.6 | 41.5 | 46.1 | 5.1 | 37.7 | 35.9 | 96.4% |
| V1 punct stripped + basename | 5.4 | 41.1 | 45.9 | 4.9 | 37.5 | 35.7 | 96.7% |
| V2 V1 + Hangul 2+ + ident 4+ | 3.0 | 34.9 | 41.6 | 2.8 | 33.9 | 31.9 | 98.2% |
| V3 V1 (tool inputs already counted) | 5.4 | 41.1 | 45.9 | 4.9 | 37.5 | 35.7 | 96.7% |
| V4 V1, min_shared=3 | 18.9 | 51.9 | 53.1 | 16.7 | 43.3 | 33.0 | 83.6% |
| V5 window 50 calls, >=20% coverage | 50.2 | 54.0 | 55.0 | 42.8 | 45.3 | 3.8 | 61.6% |

Supplementary (same pipeline):
| Variant | P=inf | P=1000 | P=0 | dead | idle |
|---|---:|---:|---:|---:|---:|
| S1 V1 min_shared=2 | 13.0 | 48.9 | 51.0 | 11.7 | 41.7 |
| S2 V1, outputs = assistant text only | 13.8 | 53.5 | 54.8 | 12.3 | 44.4 |
| S3 V1, outputs = tool inputs/writes only | 6.2 | 43.2 | 47.5 | 5.6 | 38.8 |
| S4 V2 min_shared=3 | 12.9 | 48.2 | 50.5 | 11.5 | 41.2 |
| S5 V5 gate only (uses beyond 50 calls kept) | 26.1 | 47.1 | 50.4 | 21.0 | 41.1 |
| S6 V5 on V2 tokens | 49.0 | 52.8 | 54.2 | 42.2 | 44.9 |
| S7 window 50, coverage >= 10% | 48.0 | 53.2 | 54.4 | 41.8 | 45.0 |
| S8 window 50, coverage >= 40% | 54.0 | 55.6 | 56.2 | 44.7 | 45.9 |
| S9 V1 common_frac=0.05 | 3.2 | 34.6 | 41.3 | 3.0 | 33.6 |
| S10 V1 common_frac=0.01 | 7.9 | 45.7 | 49.0 | 7.2 | 40.1 |

Per-session paging gain (P=1000 minus P=inf), min / median / max: V0 12.9 / 35.4 / 41.3; V2 11.6 / 30.1 / 37.9; V4 12.6 / 28.0 / 38.3; V5 1.4 / 4.0 / 9.6.

## Robustness
(a) Paging beats forgetting by a wide margin: robust across every lexical variant (V0-V4, S1-S4, S9-S10: gain 31-40 points pooled, at least
11.6 points in every one of the 10 sessions). NOT robust to V5: when most segments are declared "never used again" there is nothing to page
(gain 1.6-5.2 points). So (a) depends on the assumption that a segment is needed when ANY distinctive token reappears.
(b) Forgetting alone is small: robust within lexical variants (3.0-19% at min_shared 1-3; 3.2-7.9% across common_frac 0.05-0.01), but it is the
conclusion most sensitive to detector strictness (4x from min_shared 1 to 3) and it is overturned by V5 (50.2%). It holds only while "reuse" means
"any shared token". Note V5 is a harsh and arguably biased proxy: a 20% coverage gate marks big tool results as unused even if one line was needed.
(c) Size of the paging opportunity: the most robust number. P=0 spans 41.6-55.0% over all main variants (45.9% V1, 41.6% V2, 53.1% V4,
55.0% V5), P=1000 spans 34.9-54.0%. The opportunity is real and of the same order (~35-55%) under every detector, but its exact size
cannot be pinned below +-10 points. The split between "paging" and "forgetting" is where the detector matters, not the total.

Other findings. V1 is a no-op in effect (-0.2 pt); V2 (looser tokens) lowers the bound by 2.6 pt (P=inf) to 6.6 pt (P=1000) because more coincidental
or genuine matches turn gaps into uses. Output source: assistant text alone and tool inputs alone both give higher bounds than combined, and
tool inputs carry most of the signal (S3 close to V1); reuse that happens in thinking is invisible to every variant.

## Proposal for lexical-v2 (to be validated against blind labels, not adopted on this evidence)
V1 as the default (punctuation stripped, basename matching, otherwise unchanged thresholds): it fixes two known tokenization defects, changes
the headline by 0.2 point, adds no new tunable, so v1 and v2 stay comparable. Report V2 (conservative: more recall, more coincidences) and
V4 (optimistic: stricter) as the published band, and let the labels decide whether V2's extra tokens add recall or only noise. V5-type windowed
detectors should not be adopted without labels: they flip conclusion (b) and their 20% gate is size-biased.

## Caveats
One pooled sample of 10 sessions by one user; no ground truth, so no variant can be called better, only more or less strict. Common-token cut-off
recomputed per variant. V5 parameters (50 calls, 20%) were given, with 10% / 40% as sensitivity; the result is insensitive to them.
