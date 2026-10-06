"""D7: print markdown tables from power_quality.json (run after power_quality.py)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, "power_quality.json")))
RES = J["results"]
NSIM = J["nsim"]
RS = [str(r) for r in range(1, 11)]


def g(tag, p0, X, su=1.0):
    return RES[f"{tag}|{p0}|{X}|{su}"]


def pct(x):
    return f"{100*x:.0f}"


print(f"Simulations per scenario: {NSIM} (Monte Carlo SE at most {100*(0.25/NSIM)**0.5:.1f} points).\n")

print("### T1. Power to detect a loss (exact sign-flip test, chain-run units), s_u = 1.0, independent runs\n")
print("Cell: one-sided alpha 0.10 / two-sided alpha 0.05, in %.\n")
print("| baseline | loss | " + " | ".join(f"R={r}" for r in RS) + " |")
print("|---|---|" + "---|" * 10)
for p0 in (0.6, 0.75, 0.9):
    for X in (0.05, 0.1, 0.2):
        v = g("main", p0, X)["by_R"]
        print(f"| {pct(p0)}% | {pct(X)} | " + " | ".join(f"{pct(v[r]['sf1'])} / {pct(v[r]['sf2'])}" for r in RS) + " |")

print("\n### T2. Heterogeneity: power (sign-flip, one-sided 0.10) at R = 3 / 5 / 10, by instruction SD\n")
print("| baseline | loss | s_u 0.5 | s_u 1.0 | s_u 1.5 |")
print("|---|---|---|---|---|")
for p0 in (0.6, 0.75, 0.9):
    for X in (0.05, 0.1, 0.2):
        cells = []
        for su in (0.5, 1.0, 1.5):
            v = g("main", p0, X, su)["by_R"]
            cells.append(" / ".join(pct(v[r]["sf1"]) for r in ("3", "5", "10")))
        print(f"| {pct(p0)}% | {pct(X)} | " + " | ".join(cells) + " |")

print("\n### T3. False-positive rate with no true loss (should be 5% two-sided, 10% one-sided)\n")
print("Cell: R = 3 / 6 / 10. McNemar pools instructions and ignores clustering; sign-flip uses chain-run units.\n")
print("| model | McNemar 2-sided 0.05 | McNemar 1-sided 0.10 | sign-flip 2-sided 0.05 | sign-flip 1-sided 0.10 |")
print("|---|---|---|---|---|")
rows = [("main, s_u 0.5, baseline 75%", "main", 0.75, 0.5), ("main, s_u 1.0, baseline 75%", "main", 0.75, 1.0),
        ("main, s_u 1.5, baseline 75%", "main", 0.75, 1.5), ("main, s_u 1.0, baseline 60%", "main", 0.6, 1.0),
        ("main, s_u 1.0, baseline 90%", "main", 0.9, 1.0), ("no chain-run effect (s_v 0)", "sv0", 0.75, 1.0),
        ("chain-run SD 1.0", "sv1", 0.75, 1.0), ("carry-over 1.0", "carry1", 0.75, 1.0),
        ("forked", "fork", 0.75, 1.0), ("forked + carry-over", "fork_carry1", 0.75, 1.0)]
for name, tag, p0, su in rows:
    v = g(tag, p0, 0.0, su)["by_R"]
    cells = [" / ".join(pct(v[r][k]) for r in ("3", "6", "10")) for k in ("mc2", "mc1", "sf2", "sf1")]
    print(f"| {name} | " + " | ".join(cells) + " |")

print("\n### T4. McNemar (pooled instructions) power for comparison, one-sided 0.10, s_u 1.0, R = 3 / 5 / 10\n")
print("| baseline | loss 5 | loss 10 | loss 20 |")
print("|---|---|---|---|")
for p0 in (0.6, 0.75, 0.9):
    cells = []
    for X in (0.05, 0.1, 0.2):
        v = g("main", p0, X)["by_R"]
        cells.append(" / ".join(pct(v[r]["mc1"]) for r in ("3", "5", "10")))
    print(f"| {pct(p0)}% | " + " | ".join(cells) + " |")

print("\n### T5. Non-inferiority: P(conclude 'restart not worse by more than M'), one-sided 0.10, s_u 1.0\n")
print("Upper rows: true loss 0 (power). Lower rows: true loss = M (size; should be <= 10%).\n")
print("| baseline | true loss | M | " + " | ".join(f"R={r}" for r in RS) + " |")
print("|---|---|---|" + "---|" * 10)
for p0 in (0.6, 0.75, 0.9):
    for M in ("0.05", "0.1", "0.15", "0.2"):
        v = g("main", p0, 0.0)["by_R"]
        print(f"| {pct(p0)}% | 0 | {pct(float(M))} | " + " | ".join(pct(v[r]["ni"][M]) for r in RS) + " |")
for p0 in (0.6, 0.75, 0.9):
    for M in ("0.05", "0.1", "0.15", "0.2"):
        v = g("main", p0, float(M))["by_R"]
        print(f"| {pct(p0)}% | {pct(float(M))} | {pct(float(M))} | " + " | ".join(pct(v[r]["ni"][M]) for r in RS) + " |")

print("\n### T6. Sensitivity at baseline 75%, s_u 1.0: power (sign-flip one-sided 0.10) and NI power (M = 15, true loss 0), R = 3 / 5 / 10\n")
print("| model | loss 10 | loss 20 | NI M=15 | NI M=10 | SD of the loss estimate at R=5 (points, loss 0) |")
print("|---|---|---|---|---|---|")
for name, tag in (("main (s_v 0.5, independent)", "main"), ("no chain-run effect", "sv0"), ("chain-run SD 1.0", "sv1"),
                  ("carry-over 1.0", "carry1"), ("forked at the boundary", "fork"), ("forked + carry-over", "fork_carry1")):
    c10 = " / ".join(pct(g(tag, 0.75, 0.1)["by_R"][r]["sf1"]) for r in ("3", "5", "10"))
    c20 = " / ".join(pct(g(tag, 0.75, 0.2)["by_R"][r]["sf1"]) for r in ("3", "5", "10"))
    n15 = " / ".join(pct(g(tag, 0.75, 0.0)["by_R"][r]["ni"]["0.15"]) for r in ("3", "5", "10"))
    n10 = " / ".join(pct(g(tag, 0.75, 0.0)["by_R"][r]["ni"]["0.1"]) for r in ("3", "5", "10"))
    sd = 100 * g(tag, 0.75, 0.0)["by_R"]["5"]["sd"]
    print(f"| {name} | {c10} | {c20} | {n15} | {n10} | {sd:.1f} |")

print("\n### T7. Smallest loss detected with 80% power (sign-flip, one-sided 0.10), s_u 1.0, points (linear interpolation over losses 5/10/15/20/30)\n")
print("| design | baseline | " + " | ".join(f"R={r}" for r in RS) + " |")
print("|---|---|" + "---|" * 10)
for tag in ("main", "fork"):
    for p0 in (0.6, 0.75, 0.9):
        cells = []
        for r in RS:
            pts = [(0.0, g(tag, p0, 0.0)["by_R"][r]["sf1"])]
            for X in (0.05, 0.1, 0.15, 0.2, 0.3):
                key = "main30" if (X == 0.3 and tag == "main") else tag
                pts.append((X, g(key, p0, X)["by_R"][r]["sf1"]))
            mde = None
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if y0 < 0.8 <= y1:
                    mde = x0 + (0.8 - y0) * (x1 - x0) / (y1 - y0)
                    break
            if mde is None and pts[0][1] >= 0.8:
                mde = 0.0
            cells.append(f"{100*mde:.0f}" if mde is not None else ">30")
        print(f"| {'independent' if tag == 'main' else 'forked'} | {pct(p0)}% | " + " | ".join(cells) + " |")

print("\n### T8. Two-look stopping rule (looks at R = 3 and 6, NI and harm each at one-sided 0.05 per look), baseline 75%, s_u 1.0\n")
print("Cell: P(non-inferior) / P(harm found) / P(inconclusive), %, and mean replicates used.\n")
for tag in ("main", "fork"):
    for looks in ("3/6", "4/8", "3/5"):
        print(f"\n{'independent runs' if tag == 'main' else 'forked'}, looks {looks}:\n")
        print("| true loss | M = 10 | M = 15 | M = 20 |")
        print("|---|---|---|---|")
        for X in (0.0, 0.05, 0.1, 0.15, 0.2, 0.3):
            key = "main30" if (X == 0.3 and tag == "main") else tag
            s = g(key, 0.75, X)["seq"][looks]
            cells = []
            for M in ("0.1", "0.15", "0.2"):
                d = s[M]
                cells.append(f"{pct(d['ni'])} / {pct(d['harm'])} / {pct(d['inc'])}, R̄ {d['Rsum']:.1f}")
            print(f"| {pct(X)} | " + " | ".join(cells) + " |")

print("\n### T9. Calibration check (main, s_u 1.0, R = 10): simulated pass rates and discordance\n")
print("| baseline | loss | arm a | arm b | discordant share | mean loss estimate |")
print("|---|---|---|---|---|---|")
for p0 in (0.6, 0.75, 0.9):
    for X in (0.0, 0.05, 0.1, 0.2):
        v = g("main", p0, X)["by_R"]["10"]
        print(f"| {pct(p0)}% | {pct(X)} | {100*v['pa']:.1f} | {100*v['pb']:.1f} | {100*v['disc']:.1f} | {100*v['est']:.1f} |")
