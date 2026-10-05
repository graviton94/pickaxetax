# Pickaxe Tax

[![PyPI](https://img.shields.io/pypi/v/pickaxetax)](https://pypi.org/project/pickaxetax/)
[![CI](https://github.com/graviton94/pickaxetax/actions/workflows/ci.yml/badge.svg)](https://github.com/graviton94/pickaxetax/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue)](https://github.com/graviton94/pickaxetax/blob/HEAD/LICENSE)
[![Data: ODbL](https://img.shields.io/badge/data-ODbL--1.0-blue)](https://github.com/graviton94/pickaxetax/blob/HEAD/DATA_LICENSE.md)

> **Stop paying the pickaxe tax.** `#AntiTokenMaxing`
>
> In a gold rush, the people selling pickaxes get rich. In the AI boom, every turn of a chat re-sends the entire conversation, and you pay for every re-read.

Pickaxe Tax measures how much AI compute you didn't need, and cuts it. It is local-first and open source, and it calls no AI model itself.

**[Try it in your browser →](https://graviton94.github.io/pickaxetax/)** (nothing is uploaded) · `pip install pickaxetax` · [한국어](#한국어)

![A conversation analyzed by Pickaxe Tax: 61.8% of its compute was avoidable](https://raw.githubusercontent.com/graviton94/pickaxetax/HEAD/docs/img/result.png)

## What it does

| | |
|---|---|
| **Web app** | Paste a chat, drop a ChatGPT/Claude export, or use a share link through a bookmarklet. You get the conversation's skeleton (agenda, flow, depth) and where the compute leaked: thank-you messages, discarded answers, re-sent unrelated topics. You also get a one-shot prompt that would have done it in one go. It runs entirely in your browser; a strict CSP (`connect-src 'none'`) makes uploading impossible. |
| **Coding agents** | `pxt agent audit` reads your Claude Code transcripts. It reports cache hits, peak context, re-reads of unchanged files, huge tool outputs, repeated failures, and how many times each result was re-sent afterwards. An optional guard hook blocks re-reads of unchanged files and logs the tokens it saved. |
| **Local proxy** | `pxt proxy` sits between your app and OpenAI- or Anthropic-compatible APIs. It measures every request and answers a bare "thanks" locally instead of re-reading the whole chat. It also drops dead thank-you exchanges from history. It uses your own key, which is never stored. |
| **Public index** | Contributions (numbers only, one click, no account) feed the [Compute Bubble Index](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/BUBBLE_INDEX.md): how much of the deployed AI compute actually produced value. |

## Quick start

```bash
pip install pickaxetax            # Python 3.10+; `pxt` is the short command

pxt analyze chat.txt              # a pasted transcript or export file
pxt agent audit                   # your Claude Code sessions
pxt proxy                         # OpenAI-compatible at http://127.0.0.1:8787/v1
pxt ledger                        # what the proxy measured and avoided
```

Claude Code plugin (guard hook):

```text
/plugin marketplace add graviton94/pickaxetax
/plugin install pickaxetax@pickaxetax
```

## What one real coding-agent session looked like

Output of `pxt agent audit` on one long session (anonymized):

```text
sessions        1  ·  API calls 143  ·  tool calls 176
input processed 43,477,948 tokens  (cache hits 97.8%)  ·  output 349,743
peak context    507,710 tokens  ·  tool results re-read later: 3.3% of all input
- Context peaked at 507,710 tokens. Start a fresh session (/clear) when the task changes.
```

The agent read 43 million input tokens to write about 350 thousand. Caching made most of those reads cheap, but not free. The biggest lever wasn't any single tool output; it was the session simply growing.

## Why

Most of the cost of chat AI isn't the answer you see. It is the re-reading. Every reply re-processes the whole history, so the cost grows with the square of the conversation's length. Late constraints, re-asks, "thanks!" and topic switches inside one chat all pay that tax. Multiply that by everyone using AI and you get demand for more GPUs, more data centers and more power, a large share of which is avoidable.

We think the AI boom should be measured by how little compute it needs, not how much it burns. Pickaxe Tax provides the tools and the public evidence: the [charter](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/CHARTER.md) (Korean) and the [Compute Bubble Index design](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/BUBBLE_INDEX.md).

## Privacy, by construction

- **The web app can't upload.** Its Content-Security-Policy blocks every outgoing request (verified in a real browser in CI).
- **The proxy and the auditor store counts only:** no prompts, no replies, no keys, no file contents.
- **Contributions are allowlisted structure and numbers.** You see the exact JSON before sending, topic words are off by default, and topics are published only after at least 3 independent contributions.
- **The analyzer calls no LLM.**

Details: [docs/PRIVACY.md](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/PRIVACY.md).

## Contribute

- **One click, no account:** after an analysis in the web app, press *Contribute anonymously*.
- **From the terminal:** `pxt agent audit --export | pxt contribute send -`, or `pxt contribute github FILE` for a verified contribution.
- **Benchmark compute:** run the over-computation benchmark on a free local model: `pxt bench run --base-url http://localhost:11434 --model <model>`.
- **Data and code:** sourced capital and utilization data for the index, adapters for other coding agents, translations. See [CONTRIBUTING.md](https://github.com/graviton94/pickaxetax/blob/HEAD/CONTRIBUTING.md).

## Status

**Alpha (0.x).** Parsers and heuristics improve with real-world feedback. Please open an issue when something looks wrong. Decisions are recorded in [docs/decisions](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/decisions/README.md), and the architecture is described in [docs/ARCHITECTURE.md](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/ARCHITECTURE.md).

## License

Code: [Apache-2.0](https://github.com/graviton94/pickaxetax/blob/HEAD/LICENSE) · Data: [ODbL 1.0](https://github.com/graviton94/pickaxetax/blob/HEAD/DATA_LICENSE.md)

---

## 한국어

> **곡괭이세를 그만 내자.** `#AntiTokenMaxing`
> 골드러시에서 돈을 버는 건 곡괭이 판매자다. AI 대화는 매 턴 전체 대화를 다시 읽고, 우리는 그 재독 비용을 낸다.

Pickaxe Tax는 쓰지 않아도 됐던 AI 연산을 측정하고 줄이는 오픈소스 도구다. 로컬에서 동작하며, 분석기 자체는 AI 모델을 호출하지 않는다.

- **웹앱** ([바로 써 보기](https://graviton94.github.io/pickaxetax/)): 대화를 붙여넣거나, 내보내기 파일을 올리거나, 북마클릿으로 공유 링크를 읽으면 대화의 골격(아젠다·흐름·깊이)과 낭비 지점을 보여 준다. 한 번에 끝내는 프롬프트도 제안한다. 브라우저 밖으로 아무것도 나가지 않는다.
- **코딩 에이전트**: `pxt agent audit`로 Claude Code 세션을 감사한다. 가드 훅은 바뀌지 않은 파일을 다시 읽는 것을 막는다.
- **로컬 프록시**: `pxt proxy`는 모든 요청을 측정하고, "고마워" 같은 메시지는 모델을 호출하지 않고 로컬에서 응답한다.
- **공익 지수**: 숫자만 담긴 익명 원클릭 기여를 모아 [연산 버블 지수](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/BUBBLE_INDEX.md)를 만든다.

```bash
pip install pickaxetax
pxt agent audit
pxt proxy
```

배경과 원칙은 [프로젝트 헌장](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/CHARTER.md), 결정 과정은 [결정 기록](https://github.com/graviton94/pickaxetax/blob/HEAD/docs/decisions/README.md)에 있다.
