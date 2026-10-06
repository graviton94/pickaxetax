// Re-read tokens -> energy, CO2, trees. Estimates, not measurements: no provider
// publishes energy per token. Same constants and sources as pickaxetax/survey/carbon.py
// (tests/test_carbon.py checks they match).

export const WH_PER_TOKEN_UPPER = 5.671 / 10000; // Jegham et al. 2025, Claude 3.7 Sonnet, 10k-in/1.5k-out query
export const CACHE_READ_RATIO = 0.1; // Anthropic prompt-cache read price, 0.1x base input (proxy for compute)
export const WH_PER_TOKEN = WH_PER_TOKEN_UPPER * CACHE_READ_RATIO;
export const G_CO2_PER_KWH = 445; // IEA, Electricity 2025: world average, 2024
export const TREE_G_CO2 = 60000; // US EPA: one urban seedling grown 10 years
export const TREE_YEARS = 10;
export const PHONE_CHARGE_WH = 19; // US EPA: one smartphone charge
export const WOOD_CARBON_FRACTION = 0.47; // IPCC 2006 Guidelines, Vol. 4: dry wood
export const G_CO2_PER_G_WOOD = (WOOD_CARBON_FRACTION * 44) / 12;

const TREE_G_PER_YEAR = TREE_G_CO2 / TREE_YEARS;
const TREE_G_PER_HOUR = TREE_G_PER_YEAR / (365.25 * 24);

export function footprint(tokens, whPerToken = WH_PER_TOKEN) {
  const wh = tokens * whPerToken;
  const g = (wh / 1000) * G_CO2_PER_KWH;
  return {
    tokens, wh, g_co2: g,
    trees_10y: g / TREE_G_CO2,
    tree_years: g / TREE_G_PER_YEAR,
    tree_hours: g / TREE_G_PER_HOUR,
    phone_charges: wh / PHONE_CHARGE_WH,
    twig_g: g / G_CO2_PER_G_WOOD,
  };
}

export const SOURCES = [
  { id: "jegham", label: "Jegham et al. (2025), How Hungry is AI? Benchmarking Energy, Water, and Carbon Footprint of LLM Inference", url: "https://arxiv.org/abs/2505.09598" },
  { id: "cache", label: "Anthropic, Prompt caching pricing (cache reads 0.1× base input)", url: "https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching" },
  { id: "iea", label: "IEA (2025), Electricity 2025: Emissions", url: "https://www.iea.org/reports/electricity-2025/emissions" },
  { id: "epa", label: "US EPA, Greenhouse Gas Equivalencies Calculator: Calculations and References", url: "https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references" },
  { id: "ipcc", label: "IPCC (2006), Guidelines for National GHG Inventories, Vol. 4, Ch. 4 (carbon fraction of dry wood 0.47)", url: "https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html" },
  { id: "google", label: "Elsworth et al. (2025), Measuring the environmental impact of delivering AI at Google scale (0.24 Wh, 0.03 gCO2e per median text prompt)", url: "https://arxiv.org/abs/2508.15734" },
];
