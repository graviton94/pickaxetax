import copy
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from pickaxetax import __version__
from pickaxetax import contrib, contrib_ops
from pickaxetax.agent import export as agent_export
from pickaxetax.agent import merge
from pickaxetax.service import process_text

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")


def skeleton(text=None):
    from tests.conftest import KO_CHAT

    return process_text(text or KO_CHAT, store=None, save=False)[0]["skeleton"]


def agent_payload():
    m = merge([{
        "session_id": "s", "api_calls": 3, "subagent_calls": 0, "compactions": 0, "tool_calls": 2,
        "tokens": {"input": 10, "cache_read": 100, "cache_write": 5, "output": 7, "processed_input": 115},
        "cache_hit_pct": 87.0, "peak_context": 60, "avg_context": 38,
        "duplicate_reads": {"count": 1, "tokens": 9, "carried_tokens": 18}, "large_results": {"count": 0, "tokens": 0, "carried_tokens": 0},
        "failed_repeats": {"count": 0, "tokens": 0, "carried_tokens": 0},
        "by_tool": {"Read": {"calls": 2, "result_tokens": 18, "carried_tokens": 18, "errors": 0, "images": 0}}, "_detail": {},
    }])
    return contrib.from_export(agent_export(m))


def bound_block():
    return {"method": "lexical-v1", "sessions": 2, "api_calls": 30, "measured_input": 1000, "pinned_input": 400,
            "written_tokens": 50, "tokenizer_factor": 1.9,
            "avoidable_pct": {"P0": 50.0, "P1000": 45.0, "P10000": 30.0, "Pinf": 9.0},
            "per_session": [[10, 400, 40.0, 55.0, 50.0, 35.0, 10.0], [20, 600, 40.0, 46.7, 41.7, 26.7, 8.3]]}


def agent_bound_payload():
    p = agent_payload()
    p["data"]["bound"] = bound_block()
    return p


def ledger_payload():
    return contrib.from_export({"schema": "pickaxetax.ledger.v1", "rows": [
        {"day": "2026-10-05", "provider": "openai", "model": "gpt-x", "action": "gratitude_local", "requests": 3,
         "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "history_tokens": 0, "avoided_input": 900,
         "avoided_output": 120, "measured_requests": 0}]})


def mutations():
    """(payload, expected_valid) pairs covering every rule."""
    sk = contrib.skeleton_contribution(skeleton(), labels=["react", "useeffect"])
    cases = [(sk, True), (agent_payload(), True), (ledger_payload(), True)]

    def mut(base, fn):
        p = copy.deepcopy(base)
        fn(p)
        return p

    bad = [
        lambda p: p["data"].__setitem__("note", "free text"),
        lambda p: p.__setitem__("extra", 1),
        lambda p: p.__setitem__("schema", "other"),
        lambda p: p.__setitem__("client", "bot"),
        lambda p: p.__setitem__("version", "latest"),
        lambda p: p.__setitem__("kind", "diary"),
        lambda p: p["data"].__setitem__("source", "myblog"),
        lambda p: p["data"].__setitem__("language", "xx"),
        lambda p: p["data"]["metrics"].__setitem__("visible_tokens", 999999),
        lambda p: p["data"]["metrics"].__setitem__("compute_units", -1),
        lambda p: p["data"]["metrics"].__setitem__("savings_pct", 150),
        lambda p: p["data"]["metrics"].__setitem__("user_turns", 1.5),
        lambda p: p["data"]["metrics"].__setitem__("optimized_compute_units", 10**9),
        lambda p: p["data"]["metrics"].pop("branches"),
        lambda p: p["data"]["turns"][0].__setitem__(1, "gossip"),
        lambda p: p["data"]["turns"][0].__setitem__(5, True),
        lambda p: p["data"]["turns"].append(["u", "ask", 0, 0, 5]),
        lambda p: p["data"]["edges"].__setitem__("LIKES", 1),
        lambda p: p["data"].__setitem__("labels", ["a b c"]),
        lambda p: p["data"].__setitem__("labels", ["has_underscore"]),
        lambda p: p["data"].__setitem__("labels", ["x" * 40]),
        lambda p: p["data"].__setitem__("labels", ["dup", "dup"]),
        lambda p: p["data"].__setitem__("labels", [f"w{i}x" for i in range(8)]),
        lambda p: p["data"].__setitem__("labels", ["<script>"]),
        lambda p: p["data"].__setitem__("turns", []),
        lambda p: p["data"].__setitem__("blob", "x" * 40000),
        # Python's "$" also matches before a trailing newline; JS's does not
        lambda p: p.__setitem__("version", p["version"] + "\n"),
        lambda p: p["data"].__setitem__("labels", ["react\n"]),
    ]
    cases += [(mut(sk, f), False) for f in bad]
    good = [
        lambda p: p["data"].pop("labels"),
        lambda p: p["data"].__setitem__("labels", ["서울", "東京", "c++", "node.js", "k8s"]),
    ]
    cases += [(mut(sk, f), True) for f in good]
    ag = agent_payload()
    cases += [
        (mut(ag, lambda p: p["data"]["by_tool"].__setitem__("mcp__secret__x", {"calls": 1, "result_tokens": 1, "carried_tokens": 0, "errors": 0, "images": 0})), False),
        (mut(ag, lambda p: p["data"]["tokens"].__setitem__("processed_input", 1)), False),
        (mut(ag, lambda p: p["data"].__setitem__("agent", "other")), False),
        (mut(ag, lambda p: p["data"].__setitem__("cache_hit_pct", 101)), False),
    ]
    ab = agent_bound_payload()
    cases += [(ab, True)]

    def bset(path, value):
        def f(p):
            obj = p["data"]["bound"]
            for k in path[:-1]:
                obj = obj[k]
            obj[path[-1]] = value
        return f
    bound_bad = [
        bset(["method"], "vibes-v0"),
        bset(["note"], "free text"),
        bset(["avoidable_pct", "Pinf"], 60.0),                     # policies out of order
        bset(["avoidable_pct", "P0"], 101),
        bset(["pinned_input"], 2000),                              # pinned > measured
        bset(["pinned_input"], 900),                               # P0 above the 10% ceiling
        bset(["tokenizer_factor"], 99),
        bset(["per_session"], []),
        bset(["per_session", 0], [10, 400, 40.0, 55.0]),            # short row
        bset(["per_session", 0], [10, 400, 40.0, 10.0, 20.0, 5.0, 1.0]),  # row out of order
        bset(["per_session", 0], [10, 400, 90.0, 55.0, 50.0, 35.0, 10.0]),  # row above its ceiling
        bset(["per_session", 0], [0, 400, 40.0, 55.0, 50.0, 35.0, 10.0]),  # a session needs calls
        bset(["per_session", 0, 1], 401),                          # totals mismatch
        bset(["sessions"], 3),                                     # row count mismatch
        bset(["per_session", 1, 3], "46.7"),
    ]
    cases += [(mut(ab, f), False) for f in bound_bad]
    lg = ledger_payload()
    cases += [
        (mut(lg, lambda p: p["data"]["rows"][0].__setitem__("model", "my secret model name with spaces")), False),
        (mut(lg, lambda p: p["data"]["rows"][0].__setitem__("day", "yesterday")), False),
        (mut(lg, lambda p: p["data"]["rows"][0].__setitem__("measured_requests", 9)), False),
        (mut(lg, lambda p: p["data"]["rows"][0].__setitem__("action", "spy")), False),
        (mut(lg, lambda p: p["data"]["rows"][0].__setitem__("day", p["data"]["rows"][0]["day"] + "\n")), False),
        (mut(lg, lambda p: p["data"]["rows"][0].__setitem__("model", p["data"]["rows"][0]["model"] + "\n")), False),
    ]
    return cases


def test_python_validator_cases():
    for i, (p, ok) in enumerate(mutations()):
        assert (not contrib.validate(p)) is ok, (i, contrib.validate(p))


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_js_python_validators_agree():
    cases = mutations()
    r = subprocess.run([NODE, str(ROOT / "tests/parity/validate.mjs")], input=json.dumps([p for p, _ in cases]),
                       capture_output=True, text=True, check=True)
    js = json.loads(r.stdout)
    py = [not contrib.validate(p) for p, _ in cases]
    assert js == py == [ok for _, ok in cases]


def test_engine_version_matches_package():
    src = (ROOT / "site/app.js").read_text()
    assert re.search(r'ENGINE_VERSION = "([^"]+)"', src).group(1) == __version__


def test_pow_roundtrip():
    nonce = contrib.solve_pow("abc", 10)
    import hashlib

    assert contrib._lzb(hashlib.sha256(f"abc:{nonce}".encode()).digest()) >= 10


def test_github_issue_url_and_parse():
    p = contrib.skeleton_contribution(skeleton())
    url = contrib.github_issue_url(p)
    assert url.startswith("https://github.com/graviton94/pickaxetax/issues/new?template=contribution.yml")
    body = "### Payload\n\n```json\n" + json.dumps(p) + "\n```\n"
    assert contrib.payload_from_issue(body) == p
    with pytest.raises(ValueError):
        contrib.payload_from_issue("no json here")


def test_aggregate_k_anonymity_and_medians():
    recs = []
    for i, topic in enumerate(["postgres", "postgres", "redis"]):
        sk = skeleton(f"User: explain {topic} replication {topic} indexing case{i}x\nAssistant: {topic} replication copies data.\nUser: thanks!\nAssistant: welcome")
        recs.append({"payload": contrib.skeleton_contribution(sk, labels=sk["agenda"][:2]), "verified": i == 0})
    recs.append({"payload": agent_payload(), "verified": False})
    recs.append({"payload": ledger_payload(), "verified": False})
    agg = contrib.aggregate(recs, labels={"labels": [["postgres", 1]], "pairs": []})
    assert agg["contributions"] == {"total": 5, "verified": 1, "anonymous": 4, "by_kind": {"skeleton": 3, "agent": 1, "ledger": 1}}
    assert agg["skeleton"]["conversations"] == 3 and 0 < agg["skeleton"]["avoidable_pct"] < 100
    labels = {n["label"] for n in agg["topics"]["nodes"]}
    assert "postgres" in labels and "redis" not in labels  # 2 verified + 1 anonymous >= 3; redis only once
    assert agg["ledger"]["avoided_input"] == 900 and agg["agent"]["sessions"] == 1
    assert "bound" not in agg["agent"]


def test_aggregate_bound_uses_sessions_as_unit():
    recs = [{"payload": agent_bound_payload(), "verified": False}, {"payload": agent_bound_payload(), "verified": True}]
    b = contrib.aggregate(recs)["agent"]["bound"]
    assert b["sessions"] == 4 and b["method"] == "lexical-v1"
    assert b["P0"]["median"] == 50.9 and b["Pinf"]["q1"] <= b["Pinf"]["median"] <= b["Pinf"]["q3"]


def test_real_export_with_bound_validates(tmp_path):
    from pickaxetax.agent import bound
    from tests.test_bound import session

    path = session(tmp_path)
    m = merge([audit_session_for(path)])
    payload = contrib.from_export(agent_export(m, bound.export([bound.analyze(path)])))
    assert contrib.validate(payload) == []
    assert payload["data"]["bound"]["per_session"][0][0] == 4


def audit_session_for(path):
    from pickaxetax.agent import audit_session, parse

    return audit_session(parse(path))


def test_build_site_without_worker(tmp_path, monkeypatch):
    monkeypatch.delenv("PICKAXETAX_CONTRIB_URL", raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    site = tmp_path / "site"
    shutil.copytree(ROOT / "site", site)
    res = contrib_ops.build_site(site)
    assert res == {"contribUrl": "", "records": 0}
    html = (site / "index.html").read_text()
    assert "connect-src 'none'" in html and "connect-src 'none': this page" in html  # comment intact
    assert (site / "data/aggregate.js").read_text().strip() == "window.PXT_AGGREGATE = null;"


def test_build_site_with_worker(tmp_path, monkeypatch):
    monkeypatch.setenv("PICKAXETAX_CONTRIB_URL", "https://pickaxetax-contrib.example.workers.dev")
    rec = {"payload": contrib.skeleton_contribution(skeleton()), "verified": False}
    monkeypatch.setattr(contrib_ops, "fetch_anonymous", lambda url: ([rec], {"labels": [], "pairs": []}))
    site = tmp_path / "site"
    shutil.copytree(ROOT / "site", site)
    data = tmp_path / "data"
    (data / "github").mkdir(parents=True)
    (data / "github" / "7.json").write_text(json.dumps({"payload": agent_payload(), "verified": True}))
    (data / "github" / "8.json").write_text(json.dumps({"payload": {"bogus": True}}))  # ignored
    res = contrib_ops.build_site(site, data)
    assert res["records"] == 2
    html = (site / "index.html").read_text()
    assert "connect-src https://pickaxetax-contrib.example.workers.dev;" in html
    assert "pickaxetax-contrib.example.workers.dev" in (site / "config.js").read_text()
    agg = json.loads((site / "data/aggregate.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
    assert agg["contributions"]["verified"] == 1 and agg["contributions"]["anonymous"] == 1


@pytest.fixture
def repo_with_remote(tmp_path, monkeypatch):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True)
    calls = []
    monkeypatch.setattr(contrib_ops, "_gh", lambda method, path, body=None: calls.append((method, path, body)) or (200, {}))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    return remote, work, calls


def test_ingest_issue_store_and_withdraw(repo_with_remote):
    remote, work, calls = repo_with_remote
    p = contrib.skeleton_contribution(skeleton())
    issue = {"number": 42, "user": {"login": "alice"}, "created_at": "2026-10-05T00:00:00Z",
             "body": "### Payload\n\n```json\n" + json.dumps(p) + "\n```"}
    assert contrib_ops.ingest_issue({"issue": issue}, work) == "stored"
    files = subprocess.run(["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "contributions"],
                           capture_output=True, text=True, check=True).stdout.split()
    assert "github/42.json" in files
    assert any(m == "PATCH" and b["state"] == "closed" for m, _, b in calls)
    # someone else cannot withdraw
    assert contrib_ops.ingest_issue({"issue": issue, "comment": {"body": "/withdraw", "user": {"login": "mallory"}}}, work) == "withdraw denied"
    assert contrib_ops.ingest_issue({"issue": issue, "comment": {"body": "/withdraw", "user": {"login": "alice"}}}, work) == "withdrawn"
    files = subprocess.run(["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "contributions"],
                           capture_output=True, text=True, check=True).stdout.split()
    assert "github/42.json" not in files


def test_ingest_issue_rejects_invalid(repo_with_remote):
    _, work, calls = repo_with_remote
    issue = {"number": 5, "user": {"login": "bob"}, "body": "```json\n{\"schema\": \"x\"}\n```"}
    assert contrib_ops.ingest_issue({"issue": issue}, work) == "invalid"
    assert "did not pass validation" in calls[0][2]["body"]


def test_invalid_comment_cannot_inject_markdown(repo_with_remote):
    # validation errors quote attacker-chosen keys; they must stay inside one inline code span
    _, work, calls = repo_with_remote
    p = contrib.skeleton_contribution(skeleton())
    p["x` [click](https://evil.example) @someone\n# heading `"] = 1
    issue = {"number": 6, "user": {"login": "eve"}, "body": "```json\n" + json.dumps(p) + "\n```"}
    assert contrib_ops.ingest_issue({"issue": issue}, work) == "invalid"
    body = calls[0][2]["body"]
    for line in body.splitlines():
        if line.startswith("- "):
            assert line.count("`") == 2 and line.startswith("- `") and line.endswith("`")
    assert "\n# heading" not in body


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_worker_rate_limit_buckets_ipv6_per_64():
    root = Path(__file__).resolve().parents[1]
    script = (
        f"import {{ ipBucket }} from '{(root / 'worker/src/index.js').as_uri()}';"
        "console.log(JSON.stringify(['203.0.113.7','2001:db8:1:2:3:4:5:6','2001:DB8:1:2::9','2001:db8:1:3::1','::ffff:198.51.100.2','::1'].map(ipBucket)));"
    )
    out = subprocess.run([NODE, "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout
    a, b, c, d, e, f = json.loads(out)
    assert a == "203.0.113.7" and e == "198.51.100.2"
    assert b == c == "2001:db8:1:2::/64"       # same /64, any interface id, any case or compression
    assert d != b                               # a different /64 is a different bucket
    assert f == "0:0:0:0::/64"
