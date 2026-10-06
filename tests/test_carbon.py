import math
import re
from pathlib import Path

from pickaxetax.survey import carbon

JS = (Path(__file__).resolve().parents[1] / "site" / "carbon.js").read_text()


def js_const(name):
    m = re.search(rf"export const {name} = ([^;]+);", JS)
    assert m, name
    return eval(m.group(1).split("//")[0], {}, {"WOOD_CARBON_FRACTION": carbon.WOOD_CARBON_FRACTION,
                                                "WH_PER_TOKEN_UPPER": carbon.WH_PER_TOKEN_UPPER,
                                                "CACHE_READ_RATIO": carbon.CACHE_READ_RATIO})


def test_site_and_package_use_the_same_factors():
    for name in ("WH_PER_TOKEN_UPPER", "CACHE_READ_RATIO", "WH_PER_TOKEN", "G_CO2_PER_KWH", "TREE_G_CO2",
                 "TREE_YEARS", "PHONE_CHARGE_WH", "WOOD_CARBON_FRACTION", "G_CO2_PER_G_WOOD"):
        assert math.isclose(js_const(name), getattr(carbon, name)), name


def test_chain():
    f = carbon.footprint(10_000, carbon.WH_PER_TOKEN_UPPER)
    assert math.isclose(f["wh"], 5.671)
    assert math.isclose(f["g_co2"], 5.671 * 0.445)
    one_tree = carbon.footprint(round(60_000 / 445 * 1000 / carbon.WH_PER_TOKEN))
    assert math.isclose(one_tree["trees_10y"], 1, rel_tol=1e-6)
    assert math.isclose(one_tree["tree_years"], 10, rel_tol=1e-6)


def test_published_numbers():
    # the figures the site and the launch notes print
    line = carbon.footprint(427_524)
    assert round(line["g_co2"], 1) == 10.8 and round(line["tree_hours"]) == 16 and round(line["twig_g"]) == 6
    user01 = carbon.footprint(5_871_292_005)
    assert round(user01["tree_years"]) == 25 and round(user01["g_co2"] / 1000) == 148
    s = carbon.summary(427_524)
    assert math.isclose(s["upper"]["wh"], 10 * s["central"]["wh"])
