"""D7: E2 token model, cost per replicate, and replicates needed for the saving's CI.

Reads only research/phase3/e2-tasks-v0.json (public). Standard library only.
Usage: python3 tokens_cost.py /path/to/ANTITOKENMAXING > tokens_cost.out
Writes tokens_cost.json next to this script.
"""
import json
import math
import os
import random
import statistics
import sys

from stats_util import norm_ppf, t_ppf

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(REPO, "research/phase3/e2-tasks-v0.json")))
K = D["estimate_constants"]
BASE, CALLS, COLD, THR = K["base"], K["calls_per_instruction"], K["cold_start"], K["restart_threshold"]
SUMMARY = {"a": None, "b": K["summary_b"], "c": K["summary_c"]}
OUT_PER_INSTR = 20000          # D6 / C3: about 20k output and reasoning per instruction
PRICE = dict(read=0.1, write=2.0, out=5.0)   # C5 ratios, uncached input = 1; main sessions wrote 1h cache
PHASE2_RATE = 7.5e6            # C3 median input per commit

tasks = {t["commit"][:7]: t for t in D["tasks"]}


def run_chain(growth, summary, charge_summary_call=False):
    """D6 bottom-up model, extended with a price split.
    Returns dict with input tokens, per-instruction input, restart flags, price units."""
    C = BASE
    tot = 0.0
    per_instr = []
    post = []
    restarts = 0
    writes = 0.0       # tokens written to cache (new content), priced at 2.0
    out_tok = 0.0
    extra_in = 0.0     # summary-request calls, not in D6's figure
    for k, g in enumerate(growth):
        if summary is not None and C > THR:
            if charge_summary_call:
                extra_in += C
            out_tok += summary
            C = BASE + summary + COLD
            writes += summary + COLD
            restarts += 1
        post.append(restarts > 0)
        x = sum(C + g * j / CALLS for j in range(CALLS))
        per_instr.append(x)
        tot += x
        writes += g
        out_tok += OUT_PER_INSTR
        C += g
    inp = tot + extra_in
    price_in = PRICE["read"] * (inp - writes) + PRICE["write"] * writes
    return dict(input=tot, input_with_summary_call=inp, per_instr=per_instr, post=post,
                restarts=restarts, writes=writes, out=out_tok,
                price_in=price_in, price_out=PRICE["out"] * out_tok,
                price_total=price_in + PRICE["out"] * out_tok)


chains = {}
for c in D["chains"]:
    g = [tasks[x]["context_estimate"]["growth_bottom_up"] for x in c["tasks"]]
    res = {arm: run_chain(g, SUMMARY[arm], charge_summary_call=True) for arm in "abc"}
    # check against D6
    for arm in "abc":
        assert abs(res[arm]["input"] - c["est_input"][arm]) < 1, (c["chain"], arm)
    first_post = res["b"]["post"].index(True)
    P = sum(res["a"]["per_instr"][:first_post])  # pre-boundary input, identical in all arms
    chains[c["chain"]] = dict(growth=g, res=res, first_post=first_post, P=P,
                              Q={arm: res[arm]["input"] - P for arm in "abc"},
                              phase2_scale=c["est_input_phase2_rate"] / res["a"]["input"])

print("## Token model (D6, reproduced exactly)\n")
print("| chain | post-restart instructions | restarts b/c | a (M) | b (M) | c (M) | pre-boundary P (M) | saving b | saving c | price/input a | price/input b |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
tot = {arm: 0.0 for arm in "abc"}
totp = {arm: 0.0 for arm in "abc"}
totw = {arm: 0.0 for arm in "abc"}
for name, ch in chains.items():
    r = ch["res"]
    for arm in "abc":
        tot[arm] += r[arm]["input"]
        totp[arm] += r[arm]["price_total"]
        totw[arm] += r[arm]["input_with_summary_call"]
    print(f"| {name} | {ch['first_post']+1}-7 ({7-ch['first_post']}) | {r['b']['restarts']}/{r['c']['restarts']} | "
          f"{r['a']['input']/1e6:.1f} | {r['b']['input']/1e6:.1f} | {r['c']['input']/1e6:.1f} | {ch['P']/1e6:.1f} | "
          f"{1-r['b']['input']/r['a']['input']:.1%} | {1-r['c']['input']/r['a']['input']:.1%} | "
          f"{r['a']['price_total']/r['a']['input']:.3f} | {r['b']['price_total']/r['b']['input']:.3f} |")
n_post = sum(7 - ch["first_post"] for ch in chains.values())
S_b = 1 - tot["b"] / tot["a"]
S_c = 1 - tot["c"] / tot["a"]
print(f"\nTotals: a {tot['a']/1e6:.1f}M, b {tot['b']/1e6:.1f}M, c {tot['c']/1e6:.1f}M; saving b {S_b:.1%}, c {S_c:.1%}; "
      f"post-restart instructions per replicate: {n_post} of 28.")
print(f"With the summary-request call charged: b {totw['b']/1e6:.1f}M, c {totw['c']/1e6:.1f}M "
      f"(saving b {1-totw['b']/tot['a']:.1%}, c {1-totw['c']/tot['a']:.1%}).")
print(f"Price units (input side B4 rule + output at 5): a {totp['a']/1e6:.1f}M, b {totp['b']/1e6:.1f}M, c {totp['c']/1e6:.1f}M; "
      f"price saving b {1-totp['b']/totp['a']:.1%}, c {1-totp['c']/totp['a']:.1%}.")
for wp in (1.25,):
    alt = {}
    for arm in "abc":
        s = 0.0
        for ch in chains.values():
            r = ch["res"][arm]
            s += PRICE["read"] * (r["input_with_summary_call"] - r["writes"]) + wp * r["writes"] + PRICE["out"] * r["out"]
        alt[arm] = s
    print(f"Variant, 5-minute cache writes at {wp}: a {alt['a']/1e6:.1f}M, b {alt['b']/1e6:.1f}M, c {alt['c']/1e6:.1f}M; "
          f"price saving b {1-alt['b']/alt['a']:.1%}, c {1-alt['c']/alt['a']:.1%}.")
outshare = sum(ch['res']['a']['price_out'] for ch in chains.values()) / totp['a']
print(f"Output share of arm a's price: {outshare:.1%}.")
inprice = {arm: sum(ch['res'][arm]['price_in'] for ch in chains.values()) for arm in "abc"}
print(f"Input-side price only: a {inprice['a']/1e6:.1f}M ({inprice['a']/tot['a']:.3f}/token), "
      f"b {inprice['b']/1e6:.1f}M, c {inprice['c']/1e6:.1f}M. Phase 2 (C3): 0.92M/7.5M = {0.92/7.5:.3f}/token.")

# ---------------------------------------------------------------- cost per replicate by design
P_tot = sum(ch["P"] for ch in chains.values())
scale_hi = sum(ch["res"]["a"]["input"] * ch["phase2_scale"] for ch in chains.values()) / tot["a"]
designs = {
    "3 arms, independent runs (a+b+c)": dict(inp=tot["a"] + tot["b"] + tot["c"],
                                            price=totp["a"] + totp["b"] + totp["c"]),
    "2 arms, independent runs (a+b)": dict(inp=tot["a"] + tot["b"], price=totp["a"] + totp["b"]),
    "3 arms, forked at the boundary (a + b-branch + c-branch)": None,
    "2 arms, forked at the boundary (a + b-branch)": None,
}
# forked: pre-boundary part run once; its price is shared too.
def pre_price(ch):
    # price of the shared prefix: same rule restricted to pre-boundary instructions of arm a
    g = ch["growth"][:ch["first_post"]]
    return run_chain(g, None)["price_total"]
P_price = sum(pre_price(ch) for ch in chains.values())
designs["3 arms, forked at the boundary (a + b-branch + c-branch)"] = dict(
    inp=tot["a"] + (tot["b"] - P_tot) + (tot["c"] - P_tot),
    price=totp["a"] + (totp["b"] - P_price) + (totp["c"] - P_price))
designs["2 arms, forked at the boundary (a + b-branch)"] = dict(
    inp=tot["a"] + (tot["b"] - P_tot), price=totp["a"] + (totp["b"] - P_price))

print("\n## Cost of one replicate (4 chains) by design\n")
print(f"Shared pre-boundary input P = {P_tot/1e6:.1f}M tokens ({P_tot/tot['a']:.0%} of arm a). "
      f"High scenario = model x {scale_hi:.2f} (arm a at the phase 2 rate of 7.5M per instruction, same saving).\n")
print("| design | input tokens, model | input tokens, high | price units, model | price units, high |")
print("|---|---|---|---|---|")
for name, v in designs.items():
    print(f"| {name} | {v['inp']/1e6:.0f}M | {v['inp']*scale_hi/1e6:.0f}M | {v['price']/1e6:.1f}M | {v['price']*scale_hi/1e6:.1f}M |")

print("\n## Total cost by number of replicates (input tokens, model / high; price units model / high)\n")
print("| R | " + " | ".join(designs) + " |")
print("|---|" + "---|" * len(designs))
for R in (1, 2, 3, 4, 5, 6, 8, 10):
    cells = []
    for v in designs.values():
        cells.append(f"{R*v['inp']/1e9:.2f}–{R*v['inp']*scale_hi/1e9:.2f}B tok; {R*v['price']/1e6:.0f}–{R*v['price']*scale_hi/1e6:.0f}M u")
    print(f"| {R} | " + " | ".join(cells) + " |")

# ---------------------------------------------------------------- precision of the saving
# Per chain-run input is lognormal with coefficient of variation CV around the model mean.
# Independent design: a and b runs independent.  Forked design: pre-boundary part P shared;
# P, Qa, Qb independent lognormal with a segment CV chosen so that a whole arm-(a) run still has CV.
CVS = (0.2, 0.35, 0.5)
mu = {name: (ch["res"]["a"]["input"], ch["res"]["b"]["input"], ch["P"]) for name, ch in chains.items()}


def lognorm(rng, mean, cv):
    s2 = math.log(1 + cv * cv)
    return mean * math.exp(rng.gauss(-s2 / 2, math.sqrt(s2)))


def analytic_hw(R, cv, design, z=1.645):
    """Half-width (points) of a 90% interval for the pooled saving 1 - sum b / sum a,
    delta method with known CV (ideal analysis)."""
    A = sum(m[0] for m in mu.values()) * R
    B = sum(m[1] for m in mu.values()) * R
    r = B / A
    if design == "indep":
        va = sum((cv * m[0]) ** 2 for m in mu.values()) * R
        vb = sum((cv * m[1]) ** 2 for m in mu.values()) * R
        var_r = r * r * (va / A ** 2 + vb / B ** 2)
    else:
        va = vb = cab = 0.0
        for a_, b_, P in mu.values():
            Qa, Qb = a_ - P, b_ - P
            cs = cv * a_ / math.sqrt(P * P + Qa * Qa)   # segment CV giving whole-run CV = cv
            vP, vQa, vQb = (cs * P) ** 2, (cs * Qa) ** 2, (cs * Qb) ** 2
            va += vP + vQa
            vb += vP + vQb
            cab += vP
        va, vb, cab = va * R, vb * R, cab * R
        var_r = r * r * (va / A ** 2 + vb / B ** 2 - 2 * cab / (A * B))
    return 100 * z * math.sqrt(var_r)


def sim_one(rng, R, cv, design):
    """Returns (pooled saving, practical 90% half-width in points or None).
    Practical analysis: per chain-run log ratio l = log(b/a); R=1: t over 4 units (df 3);
    R>=2: chain-stratified mean, pooled within-chain SD, df = 4(R-1)."""
    ls = {}
    A = B = 0.0
    for name, (a_, b_, P) in mu.items():
        for _ in range(R):
            if design == "indep":
                xa, xb = lognorm(rng, a_, cv), lognorm(rng, b_, cv)
            else:
                Qa, Qb = a_ - P, b_ - P
                cs = cv * a_ / math.sqrt(P * P + Qa * Qa)
                p = lognorm(rng, P, cs)
                xa, xb = p + lognorm(rng, Qa, cs), p + lognorm(rng, Qb, cs)
            A += xa
            B += xb
            ls.setdefault(name, []).append(math.log(xb / xa))
    S = 1 - B / A
    if R == 1:
        v = [x[0] for x in ls.values()]
        L = statistics.mean(v)
        se = statistics.stdev(v) / math.sqrt(4)
        df = 3
    else:
        L = statistics.mean(statistics.mean(x) for x in ls.values())
        ss = sum(sum((y - statistics.mean(x)) ** 2 for y in x) for x in ls.values())
        df = 4 * (R - 1)
        s2 = ss / df
        se = math.sqrt(s2 / R / 4)   # var of mean of 4 chain means, each of R runs
    t = t_ppf(0.95, df)
    lo, hi = 1 - math.exp(L + t * se), 1 - math.exp(L - t * se)
    return S, 100 * (hi - lo) / 2


rng = random.Random(20261006)
NSIM = 4000
prec = {}
print("\n## Precision of the input saving (b vs a), 90% interval half-width in points\n")
print("ideal = delta method with the CV known; sim = 5-95% spread of the pooled estimate (simulated); "
      "practical = mean half-width of a chain-stratified t interval on log ratios (simulated).\n")
for design in ("indep", "fork"):
    print(f"\n### design: {design}\n")
    print("| CV | " + " | ".join(f"R={R}" for R in range(1, 11)) + " | R for ±5 (ideal) | R for ±5 (practical) |")
    print("|---|" + "---|" * 12)
    for cv in CVS:
        cells = []
        rows = []
        for R in range(1, 11):
            a_hw = analytic_hw(R, cv, design)
            sims = [sim_one(rng, R, cv, design) for _ in range(NSIM)]
            Ss = sorted(s for s, _ in sims)
            sim_hw = 100 * (Ss[int(0.95 * NSIM)] - Ss[int(0.05 * NSIM)]) / 2
            prac = statistics.mean(h for _, h in sims)
            rows.append(dict(R=R, ideal=a_hw, sim=sim_hw, practical=prac))
            cells.append(f"{a_hw:.1f} / {sim_hw:.1f} / {prac:.1f}")
        # R for +-5: ideal analytic scales 1/sqrt(R)
        R_ideal = next(R for R in range(1, 1000) if analytic_hw(R, cv, design) <= 5.0)
        R_prac = None
        for R in range(2, 80):
            sims = [sim_one(rng, R, cv, design)[1] for _ in range(800)]
            if statistics.mean(sims) <= 5.0:
                R_prac = R
                break
        prec[f"{design}_{cv}"] = dict(rows=rows, R_ideal=R_ideal, R_practical=R_prac)
        print(f"| {cv} | " + " | ".join(cells) + f" | {R_ideal} | {R_prac} |")

json.dump(dict(chains={k: dict(first_post=v["first_post"], P=v["P"], Q=v["Q"],
                               input={a: v["res"][a]["input"] for a in "abc"},
                               price={a: v["res"][a]["price_total"] for a in "abc"},
                               restarts={a: v["res"][a]["restarts"] for a in "abc"})
                       for k, v in chains.items()},
               totals=tot, price_totals=totp, saving_b=S_b, saving_c=S_c, scale_hi=scale_hi,
               designs=designs, precision=prec, n_post=n_post),
          open(os.path.join(HERE, "tokens_cost.json"), "w"), indent=1)
