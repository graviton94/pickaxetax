"""D7: replicates needed beyond R=10 (normal approximation from the simulated SD at R=10),
and the stopping rule's error rates at every baseline. Reads power_quality.json."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "power_quality.json")))["results"]
print("### T10. Replicates for 80% power, normal approximation from the simulated SD of the loss estimate at R=10\n")
print("SD(R) = SD(10) * sqrt(10/R); R = 10 * (SD(10) * (z_alpha + 0.84) / loss)^2. Cell: one-sided 0.10 / two-sided 0.05.\n")
print("| design | baseline | SD at R=10 (points, no loss) | loss 5 | loss 10 | loss 20 |")
print("|---|---|---|---|---|---|")
for tag in ("main", "fork"):
    for p0 in (0.6, 0.75, 0.9):
        sd0 = R[f"{tag}|{p0}|0.0|1.0"]["by_R"]["10"]["sd"]
        cells = []
        for X in (0.05, 0.1, 0.2):
            sd = R[f"{tag}|{p0}|{X}|1.0"]["by_R"]["10"]["sd"]
            n1 = 10 * (sd * (1.2816 + 0.8416) / X) ** 2
            n2 = 10 * (sd * (1.96 + 0.8416) / X) ** 2
            cells.append(f"{math.ceil(n1)} / {math.ceil(n2)}")
        print(f"| {'independent' if tag=='main' else 'forked'} | {round(p0*100)}% | {100*sd0:.1f} | " + " | ".join(cells) + " |")
print("\n### T11. Stopping rule, looks 3/6, M = 15: P(NI) / P(harm) / P(inconclusive) and mean R, by baseline (independent runs)\n")
print("| baseline | loss 0 | loss 5 | loss 10 | loss 15 (P(NI) = size) | loss 20 |")
print("|---|---|---|---|---|---|")
for p0 in (0.6, 0.75, 0.9):
    cells = []
    for X in (0.0, 0.05, 0.1, 0.15, 0.2):
        d = R[f"main|{p0}|{X}|1.0"]["seq"]["3/6"]["0.15"]
        cells.append(f"{100*d['ni']:.0f} / {100*d['harm']:.0f} / {100*d['inc']:.0f}, R̄ {d['Rsum']:.1f}")
    print(f"| {round(p0*100)}% | " + " | ".join(cells) + " |")
print("\nSize of the stopping rule's NI claim when the true loss equals M (looks 3/6), %:\n")
print("| baseline | M=10 | M=15 | M=20 |")
print("|---|---|---|---|")
for p0 in (0.6, 0.75, 0.9):
    print(f"| {round(p0*100)}% | " + " | ".join(f"{100*R[f'main|{p0}|{M}|1.0']['seq']['3/6'][str(M)]['ni']:.0f}" for M in (0.1, 0.15, 0.2)) + " |")
