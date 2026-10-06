"""D7: power of E2's quality comparison (arm b vs arm a), by simulation. Standard library only.

Outcome: per instruction, 1 if all its fail-to-pass tests pass after the instruction.
Model (logit scale), replicate r, chain c, instruction k, arm m:
    logit p = mu + u[c,k] + w[c] + v[c,r,m] + delta * post[c,k] * [m = b] - carry * fail[c,r,m,k-1]
  u: instruction effect, SD s_u (0.5 / 1.0 / 1.5), drawn once per simulated experiment
  w: chain effect, SD 0.5, shared by arms and replicates
  v: chain-run effect, SD s_v (default 0.5), one per run; independent between arms (design "indep")
     or, in design "fork", arm b branches from arm a's state at the boundary: pre-boundary outcomes
     are shared and b's post-boundary run effect has correlation rho with a's
  post: instructions after the first restart in arm b (A, B, D: 4-7; C: 5-7; from the token model)
  carry: penalty after a failed previous instruction (default 0; sensitivity 1.0)
mu is set so that arm a's pass rate on post-restart instructions equals the baseline p0, and delta
so that arm b's is p0 - X (X = the quality loss in points).

Tests, unit = chain-run pair (4 per replicate), outcome on post-restart instructions only:
  - McNemar exact on discordant instruction pairs (ignores clustering; shown for its error rate)
  - exact sign-flip (randomization) test on D = sum over post instructions of (pass_a - pass_b)
  - non-inferiority: drop estimate sum D / sum n, cluster (ratio) SE, upper one-sided bound with
    t(m-1); "restart not worse by more than M" if the bound < M
Usage: python3 power_quality.py [nsim]   (writes power_quality.json and power_quality.out)
"""
import json
import math
import os
import random
import sys
from multiprocessing import Pool

from stats_util import expit, mcnemar_p, signflip_p, t_ppf

HERE = os.path.dirname(os.path.abspath(__file__))
TOK = json.load(open(os.path.join(HERE, "tokens_cost.json")))
FIRST_POST = {c: v["first_post"] for c, v in TOK["chains"].items()}   # A,B,D: 3 (0-based); C: 4
CHAINS = sorted(FIRST_POST)
NINSTR = 7
RMAX = 10
MARGINS = (0.05, 0.10, 0.15, 0.20)
LOOKS = ((3, 6), (4, 8), (3, 5))


def calib_mean(mu, delta, s_tot):
    """E[expit(mu + delta + s_tot*Z)], Z standard normal, by a fine grid."""
    h = 0.02
    tot = 0.0
    for i in range(-400, 401):
        z = i * h
        tot += expit(mu + delta + s_tot * z) * math.exp(-z * z / 2)
    return tot * h / math.sqrt(2 * math.pi)


def calib_mc(mu, delta, s_u, s_w, s_v, carry, draws):
    """Mean pass probability on post instructions, carry-over model, exact Markov recursion per draw."""
    tot = n = 0
    for (u, w, v) in draws:
        for c in CHAINS:
            pp = 1.0   # P(previous instruction passed)
            for k in range(NINSTR):
                base = mu + s_u * u[c][k] + s_w * w[c] + s_v * v[c]
                d = delta if k >= FIRST_POST[c] else 0.0
                p_ok, p_bad = expit(base + d), expit(base + d - carry)
                p = pp * p_ok + (1 - pp) * p_bad if k > 0 else p_ok
                if k >= FIRST_POST[c]:
                    tot += p
                    n += 1
                pp = p
    return tot / n


def bisect(f, target, lo=-15.0, hi=15.0):
    # f increasing
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def calibrate(p0, X, s_u, s_w, s_v, carry):
    if carry == 0:
        s = math.sqrt(s_u ** 2 + s_w ** 2 + s_v ** 2)
        mu = bisect(lambda m: calib_mean(m, 0.0, s), p0)
        delta = bisect(lambda d: calib_mean(mu, d, s), p0 - X) if X > 0 else 0.0
        return mu, delta
    rng = random.Random(7)
    draws = [({c: [rng.gauss(0, 1) for _ in range(NINSTR)] for c in CHAINS},
              {c: rng.gauss(0, 1) for c in CHAINS}, {c: rng.gauss(0, 1) for c in CHAINS})
             for _ in range(3000)]
    mu = bisect(lambda m: calib_mc(m, 0.0, s_u, s_w, s_v, carry, draws), p0)
    delta = bisect(lambda d: calib_mc(mu, d, s_u, s_w, s_v, carry, draws), p0 - X) if X > 0 else 0.0
    return mu, delta


def run_arm(rng, mu, u, w, vz, s_v, delta, carry, c, k0=0, prev_fail=False, out=None):
    out = out if out is not None else []
    for k in range(k0, NINSTR):
        d = delta if k >= FIRST_POST[c] else 0.0
        lp = mu + u[c][k] + w[c] + s_v * vz + d - (carry if prev_fail else 0.0)
        ok = rng.random() < expit(lp)
        out.append(ok)
        prev_fail = not ok
    return out


def scenario(args):
    (key, p0, X, s_u, s_v, carry, design, rho, nsim, seed) = args
    s_w = 0.5
    mu, delta = calibrate(p0, X, s_u, s_w, s_v, carry)
    delta = -abs(delta) if X > 0 else 0.0   # delta solved as a negative shift already; keep sign
    rng = random.Random(seed)
    tq90 = {m: t_ppf(0.90, m - 1) for m in range(2, 4 * RMAX + 1)}
    tq95 = {m: t_ppf(0.95, m - 1) for m in range(2, 4 * RMAX + 1)}
    acc = {R: dict(mc2=0, mc1=0, sf2=0, sf1=0, ni={M: 0 for M in MARGINS}, est=0.0, est2=0.0,
                   pa=0.0, pb=0.0, disc=0.0) for R in range(1, RMAX + 1)}
    seq = {looks: {M: dict(ni=0, harm=0, inc=0, Rsum=0) for M in MARGINS} for looks in LOOKS}
    for _ in range(nsim):
        u = {c: [rng.gauss(0, s_u) for _ in range(NINSTR)] for c in CHAINS}
        w = {c: rng.gauss(0, s_w) for c in CHAINS}
        units = []   # per replicate: list of (D, n, n10, n01, pass_a, pass_b)
        for r in range(RMAX):
            rep = []
            for c in CHAINS:
                fp = FIRST_POST[c]
                if design == "indep":
                    za, zb = rng.gauss(0, 1), rng.gauss(0, 1)
                    a = run_arm(rng, mu, u, w, za, s_v, 0.0, carry, c)
                    b = run_arm(rng, mu, u, w, zb, s_v, delta, carry, c)
                else:   # fork: shared prefix, b branches at the boundary
                    z0 = rng.gauss(0, 1)
                    pre = run_arm(rng, mu, u, w, z0, s_v, 0.0, carry, c)[:fp]
                    pf = not pre[-1]
                    zb = rho * z0 + math.sqrt(1 - rho * rho) * rng.gauss(0, 1)
                    a = run_arm(rng, mu, u, w, z0, s_v, 0.0, carry, c, fp, pf, list(pre))
                    b = run_arm(rng, mu, u, w, zb, s_v, delta, carry, c, fp, pf, list(pre))
                pa = a[fp:]
                pb = b[fp:]
                n10 = sum(1 for x, y in zip(pa, pb) if x and not y)
                n01 = sum(1 for x, y in zip(pa, pb) if y and not x)
                rep.append((n10 - n01, len(pa), n10, n01, sum(pa), sum(pb)))
            units.append(rep)
        # cumulative analysis
        Ds = []
        S_D = S_n = S_DD = S_Dn = S_nn = 0.0
        N10 = N01 = 0
        PA = PB = 0
        decided = {looks: {M: None for M in MARGINS} for looks in LOOKS}
        for R in range(1, RMAX + 1):
            for (Dv, n, n10, n01, sa, sb) in units[R - 1]:
                Ds.append(Dv)
                S_D += Dv; S_n += n; S_DD += Dv * Dv; S_Dn += Dv * n; S_nn += n * n
                N10 += n10; N01 += n01; PA += sa; PB += sb
            m = len(Ds)
            A = acc[R]
            p2, p1 = mcnemar_p(N10, N01)
            A["mc2"] += p2 < 0.05
            A["mc1"] += p1 < 0.10
            s2, s1 = signflip_p(Ds)
            A["sf2"] += s2 < 0.05
            A["sf1"] += s1 < 0.10
            th = S_D / S_n
            ss = max(0.0, S_DD - 2 * th * S_Dn + th * th * S_nn)
            se = math.sqrt(m / (m - 1) * ss) / S_n
            for M in MARGINS:
                A["ni"][M] += (th + tq90[m] * se) < M
            A["est"] += th; A["est2"] += th * th
            A["pa"] += PA / S_n; A["pb"] += PB / S_n; A["disc"] += (N10 + N01) / S_n
            # sequential rules: at each look, NI at one-sided 0.05, harm = sign-flip one-sided p < 0.05
            for looks in LOOKS:
                if R in looks:
                    for M in MARGINS:
                        if decided[looks][M] is not None:
                            continue
                        if (th + tq95[m] * se) < M:
                            decided[looks][M] = ("ni", R)
                        elif s1 < 0.05:
                            decided[looks][M] = ("harm", R)
                        elif R == looks[-1]:
                            decided[looks][M] = ("inc", R)
        for looks in LOOKS:
            for M in MARGINS:
                outc, R = decided[looks][M]
                seq[looks][M][outc] += 1
                seq[looks][M]["Rsum"] += R
    res = {}
    for R, A in acc.items():
        est = A["est"] / nsim
        res[R] = dict(mc2=A["mc2"] / nsim, mc1=A["mc1"] / nsim, sf2=A["sf2"] / nsim, sf1=A["sf1"] / nsim,
                      ni={str(M): A["ni"][M] / nsim for M in MARGINS},
                      est=est, sd=math.sqrt(max(0.0, A["est2"] / nsim - est * est)),
                      pa=A["pa"] / nsim, pb=A["pb"] / nsim, disc=A["disc"] / nsim)
    seqres = {"/".join(map(str, looks)): {str(M): {k: v / nsim for k, v in d.items()} for M, d in dd.items()}
              for looks, dd in seq.items()}
    return key, dict(p0=p0, X=X, s_u=s_u, s_v=s_v, carry=carry, design=design, rho=rho,
                     mu=mu, delta=delta, by_R=res, seq=seqres)


def main():
    nsim = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    jobs = []
    seed = 1000
    # main grid: independent runs, s_v 0.5, no carry-over
    for p0 in (0.60, 0.75, 0.90):
        for X in (0.0, 0.05, 0.10, 0.15, 0.20):
            for s_u in (0.5, 1.0, 1.5):
                seed += 1
                jobs.append((f"main|{p0}|{X}|{s_u}", p0, X, s_u, 0.5, 0.0, "indep", 0.0, nsim, seed))
    # sensitivity at baseline 75%, s_u 1.0
    for X in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
        for (tag, s_v, carry, design, rho) in (("sv0", 0.0, 0.0, "indep", 0.0),
                                               ("sv1", 1.0, 0.0, "indep", 0.0),
                                               ("carry1", 0.5, 1.0, "indep", 0.0),
                                               ("fork", 0.5, 0.0, "fork", 0.5),
                                               ("fork_carry1", 0.5, 1.0, "fork", 0.5),
                                               ("main30", 0.5, 0.0, "indep", 0.0)):
            if tag == "main30" and X != 0.30:
                continue
            for p0 in ((0.60, 0.75, 0.90) if tag in ("fork", "main30") else (0.75,)):
                seed += 1
                jobs.append((f"{tag}|{p0}|{X}|1.0", p0, X, 1.0, s_v, carry, design, rho, nsim, seed))
    with Pool(4) as pool:
        out = dict(pool.map(scenario, jobs, chunksize=1))
    json.dump(dict(nsim=nsim, margins=MARGINS, looks=LOOKS, results=out),
              open(os.path.join(HERE, "power_quality.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
