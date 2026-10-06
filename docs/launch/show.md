# Developer communities: GeekNews, Hacker News, Reddit

Posted **after** research note 1 is live on LinkedIn, one community per day. Every number is
from Receipt No. 01 (`research/survey/user01/`); the carbon line is an estimate
(`research/carbon-factors.md`). Facts table: [README.md](README.md#facts-sources-for-every-number-in-the-drafts).

Before posting: the site loads, `pip install pickaxetax` gives 0.4.0 or later, and
`pxt survey measure` works on a fresh machine.

---

## GeekNews (Show GN, 한국어)

**제목:** Show GN: 내 Claude Code가 다시 읽은 토큰, 영수증으로 뽑아 보기

**본문:**

- AI 코딩 에이전트는 호출할 때마다 지금까지의 컨텍스트 전체를 다시 읽습니다. 그게 실제로 얼마인지 궁금해서, 제 석 달치 Claude Code 기록을 제공사가 호출마다 남긴 사용량으로 다시 쟀습니다.
- 결과 (세션 10개, 2026-07-10 ~ 10-05)
  - 처리된 입력 58.7억 토큰. 세션 목록에 표시된 합계의 1.49배였습니다.
  - 지시 586번, 지시 한 번에 평균 약 1,000만 토큰
  - 출력은 입력의 0.2~0.4%
  - 매 호출이 들고 다닌 컨텍스트의 73.6%가 이미 끝난 지시들이 남긴 내용
- 직접 재 볼 수 있습니다: `pip install pickaxetax` → `pxt survey measure --out my.json` → `pxt survey report my.json --out my.html`
  - 데이터셋에는 숫자만 들어갑니다(텍스트·경로·ID 없음). 같은 데이터셋이면 같은 레포트가 바이트 단위까지 똑같이 나옵니다.
- 웹: 대화를 붙여넣으면 브라우저 안에서만 분석합니다. CSP `connect-src 'none'`이라 페이지가 대화를 밖으로 보낼 수 없습니다.
- 한계: 아직 n=1이고 Claude Code만 지원합니다. 탄소 환산(148 kg)은 공개 계수로 낸 추정입니다.
- 측정 방법에 대한 반박, 다른 에이전트 로그 어댑터, 여러분의 영수증(숫자만) 모두 환영합니다.
- https://graviton94.github.io/pickaxetax/ · https://github.com/graviton94/pickaxetax

---

## Hacker News (Show HN)

**Title (≤ 80 chars):** Show HN: I measured how much of my AI agent's input re-read finished work

**URL:** https://github.com/graviton94/pickaxetax

**First comment (from the author):**

> Every call a coding agent makes re-sends the whole context. I wanted to know what that adds up to, so I re-measured three months of my own Claude Code use from the usage the provider records per call (10 sessions):
>
> - 5.87B input tokens processed, 1.49× what the session list showed
> - 586 instructions, ~10M input tokens each on average
> - output was 0.2–0.4% of input
> - 73.6% of the context carried on each call was left over from instructions that were already finished. The cost grows with steps × carried context, and compaction only kicks in near a ~780K ceiling, so long sessions run nearly full
>
> `pxt survey measure` / `pxt survey report` produce the same report from your own transcripts. The dataset is numbers only (no text, paths or ids), and the report is byte-for-byte reproducible from it. There's also a browser analyzer for chat transcripts whose CSP is `connect-src 'none'`, so the page can't send your conversation anywhere.
>
> Caveats: n = 1, Claude Code only so far. The carbon figure on the site is an estimate from published factors and says so. The next step is testing whether handing off a compact task summary at instruction boundaries keeps results equivalent with much less input. I'd like criticism of the method most of all.

Post on a weekday, 8–10 a.m. US Eastern. Stay in the thread for the first 3 hours.

---

## Reddit (r/ClaudeAI)

**Title:** I measured 3 months of my Claude Code usage: 73.6% of each call's context was left over from instructions I'd already finished

**Body:**

> I re-measured all 10 of my Claude Code sessions from the per-call usage in the transcripts (and the provider's records where local transcripts were gone):
>
> - 5.87B input tokens, 1.49× what the session list displayed
> - 586 instructions, ~10M input tokens per instruction on average
> - output was 0.2–0.4% of input
> - 5 long-running sessions were 93% of all input
> - 73.6% of the context on every call was left over from earlier, finished instructions
>
> What I take from it so far: the expensive part isn't the task you're on, it's everything the session still carries from tasks you finished. Splitting work into fresh sessions per task is the obvious thing to test next, and I'll post that measurement when it's done rather than guess at it.
>
> If you want your own numbers: `pip install pickaxetax`, then `pxt survey measure --out my.json` and `pxt survey report my.json --out my.html`. Numbers only, nothing uploaded. Open source (Apache-2.0): https://github.com/graviton94/pickaxetax
>
> Happy to be told where the method is wrong.

Check the subreddit's self-promotion rules on the day; flair as the subreddit asks.
