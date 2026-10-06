"""Small statistics helpers, standard library only (cycle D7)."""
import math
from functools import lru_cache


def _betacf(a, b, x):
    # continued fraction for the regularized incomplete beta (Numerical Recipes 6.4)
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > FPMIN else FPMIN)
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > FPMIN else FPMIN)
        c = 1.0 + aa / c
        c = c if abs(c) > FPMIN else FPMIN
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > FPMIN else FPMIN)
        c = 1.0 + aa / c
        c = c if abs(c) > FPMIN else FPMIN
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    bt = math.exp(lbt)
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


@lru_cache(maxsize=None)
def t_ppf(q, df):
    lo, hi = -1000.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def norm_ppf(q):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * math.erfc(-mid / math.sqrt(2)) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def expit(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


@lru_cache(maxsize=None)
def binom_upper(n, k):
    """P(X >= k), X ~ Bin(n, 1/2)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2.0 ** n


def mcnemar_p(n10, n01):
    """Exact McNemar. Returns (two-sided p, one-sided p for n10 > n01)."""
    n = n10 + n01
    if n == 0:
        return 1.0, 1.0
    p1 = binom_upper(n, n10)
    p2 = min(1.0, 2.0 * binom_upper(n, max(n10, n01)))
    return p2, p1


@lru_cache(maxsize=None)
def _signflip_dist(counts):
    """Exact distribution of sum s_i*v_i, s_i = +-1 equiprobable.
    counts[j] = number of units with |D| = j+1. Returns dict sum -> probability."""
    dist = {0: 1.0}
    for j, cnt in enumerate(counts):
        v = j + 1
        for _ in range(cnt):
            new = {}
            for s, p in dist.items():
                new[s + v] = new.get(s + v, 0.0) + p * 0.5
                new[s - v] = new.get(s - v, 0.0) + p * 0.5
            dist = new
    return dist


@lru_cache(maxsize=None)
def _signflip_p(counts, s_obs):
    dist = _signflip_dist(counts)
    p1 = sum(p for s, p in dist.items() if s >= s_obs)
    p2 = sum(p for s, p in dist.items() if abs(s) >= abs(s_obs))
    return min(1.0, p2), min(1.0, p1)


def signflip_p(D, maxabs=7):
    """Exact sign-flip (randomization) test on integer unit differences D.
    Returns (two-sided p, one-sided p for sum D > 0)."""
    counts = [0] * maxabs
    s = 0
    for x in D:
        if x:
            counts[abs(x) - 1] += 1
        s += x
    if s == 0 and not any(counts):
        return 1.0, 1.0
    return _signflip_p(tuple(counts), s)
