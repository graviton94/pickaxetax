"""Turn re-read tokens into energy, CO2 and trees, with every factor sourced.

These are estimates, not measurements: no provider publishes energy per token.
The chain is deliberately simple so anyone can swap a factor and recompute.
site/carbon.js carries the same constants (tests/test_carbon.py checks parity).

  Wh per input token, upper   = 5.671 Wh / 10,000 input tokens
      Jegham et al. 2025, "How Hungry is AI?" (arXiv 2505.09598): Claude 3.7 Sonnet,
      long prompt (10,000 input + 1,500 output tokens) = 5.671 ± 0.302 Wh per query.
      The whole query's energy is charged to its input, so this over-counts.
  Wh per re-read token, central = upper × 0.1
      Re-read context is served from the prompt cache, which Anthropic prices at
      0.1× base input. Price is used as a proxy for compute: an assumption.
  CO2 per kWh                 = 445 g   (IEA, Electricity 2025: world average, 2024)
  one tree                    = 60 kg CO2 over 10 years  (US EPA GHG Equivalencies:
      a medium-growth urban seedling grown 10 years sequesters 0.060 t CO2)
  one smartphone charge       = 19 Wh   (US EPA GHG Equivalencies)
  one dry twig                = carbon in dry wood, 0.47 g C per g  (IPCC 2006
      Guidelines, Vol. 4, default carbon fraction), × 44/12 to CO2
"""

from __future__ import annotations

WH_PER_TOKEN_UPPER = 5.671 / 10_000
CACHE_READ_RATIO = 0.1
WH_PER_TOKEN = WH_PER_TOKEN_UPPER * CACHE_READ_RATIO
G_CO2_PER_KWH = 445.0
TREE_G_CO2 = 60_000.0
TREE_YEARS = 10
PHONE_CHARGE_WH = 19.0
WOOD_CARBON_FRACTION = 0.47
G_CO2_PER_G_WOOD = WOOD_CARBON_FRACTION * 44 / 12

TREE_G_PER_YEAR = TREE_G_CO2 / TREE_YEARS
TREE_G_PER_HOUR = TREE_G_PER_YEAR / (365.25 * 24)


def footprint(tokens: int, wh_per_token: float = WH_PER_TOKEN) -> dict:
    wh = tokens * wh_per_token
    g = wh / 1000 * G_CO2_PER_KWH
    return {
        "tokens": tokens,
        "wh": wh,
        "g_co2": g,
        "trees_10y": g / TREE_G_CO2,
        "tree_years": g / TREE_G_PER_YEAR,
        "tree_hours": g / TREE_G_PER_HOUR,
        "phone_charges": wh / PHONE_CHARGE_WH,
        "twig_g": g / G_CO2_PER_G_WOOD,
    }


def summary(tokens: int) -> dict:
    return {"central": footprint(tokens), "upper": footprint(tokens, WH_PER_TOKEN_UPPER)}
