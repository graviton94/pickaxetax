"""CI-side operations for contributions (run by GitHub Actions, not by users).

* build_site:   discover the worker URL, write site/config.{js,json}, open the
                page's CSP to exactly that origin, and bake the public
                aggregate into site/data/aggregate.js (no runtime fetch needed).
* ingest_issue: validate a GitHub-issue contribution, store it on the
                ``contributions`` branch, comment and close; handle /withdraw.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from .contrib import REPO, _http, aggregate, payload_from_issue, validate

WORKER_NAME = "pickaxetax-contrib"
DATA_BRANCH = "contributions"


# ------------------------------------------------------------------ worker discovery

def discover_worker_url() -> str:
    if os.environ.get("PICKAXETAX_CONTRIB_URL"):
        return os.environ["PICKAXETAX_CONTRIB_URL"].rstrip("/")
    token, account = os.environ.get("CLOUDFLARE_API_TOKEN"), os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        return ""
    status, res = _http("GET", f"https://api.cloudflare.com/client/v4/accounts/{account}/workers/subdomain",
                        headers={"Authorization": f"Bearer {token}"})
    sub = (res.get("result") or {}).get("subdomain") if status == 200 else None
    if not sub:
        return ""
    url = f"https://{WORKER_NAME}.{sub}.workers.dev"
    try:
        ok, _ = _http("GET", url + "/health", timeout=15)
    except OSError:
        return ""
    return url if ok == 200 else ""


def fetch_anonymous(url: str) -> tuple[list[dict], dict]:
    records, after = [], 0
    while True:
        status, res = _http("GET", f"{url}/export?after={after}&limit=1000")
        if status != 200:
            break
        for r in res.get("rows", []):
            if not validate(r["payload"]):  # re-validate: never trust stored data blindly
                records.append({"payload": r["payload"], "verified": False})
        if not res.get("next"):
            break
        after = res["next"]
    status, labels = _http("GET", f"{url}/labels")
    return records, (labels if status == 200 else {})


def load_verified(data_dir: Path) -> list[dict]:
    out = []
    for f in sorted((data_dir / "github").glob("*.json")) if data_dir.exists() else []:
        try:
            rec = json.loads(f.read_text())
        except ValueError:
            continue
        if not validate(rec.get("payload")):
            out.append({"payload": rec["payload"], "verified": True})
    return out


# ------------------------------------------------------------------ site build

_CSP = re.compile(r'(<meta http-equiv="Content-Security-Policy" content="[^"]*?)connect-src [^;"]*')


def build_site(site: Path, data_dir: Path | None = None) -> dict:
    url = ""
    try:
        url = discover_worker_url()
    except OSError:
        url = ""
    cfg = {"contribUrl": url, "repo": REPO}
    (site / "config.js").write_text(f"window.PXT_CONFIG = {json.dumps(cfg)};\n")
    (site / "config.json").write_text(json.dumps(cfg) + "\n")
    index = site / "index.html"
    html = index.read_text()
    new, n = _CSP.subn(lambda m: m.group(1) + (f"connect-src {url}" if url else "connect-src 'none'"), html, count=1)
    if n != 1:
        raise RuntimeError("CSP meta tag with connect-src not found in index.html")
    html = new
    index.write_text(html)

    records, labels = ([], {})
    if url:
        try:
            records, labels = fetch_anonymous(url)
        except OSError:
            records, labels = [], {}
    records += load_verified(data_dir) if data_dir else []
    agg = aggregate(records, labels) if records else None
    (site / "data").mkdir(exist_ok=True)
    (site / "data" / "aggregate.js").write_text(f"window.PXT_AGGREGATE = {json.dumps(agg, ensure_ascii=False)};\n")
    return {"contribUrl": url, "records": len(records)}


# ------------------------------------------------------------------ GitHub issues

def _gh(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    return _http(method, f"https://api.github.com/repos/{os.environ.get('GITHUB_REPOSITORY', REPO)}{path}", body,
                 headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"})


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def _data_checkout(root: Path) -> Path:
    d = root / ".contrib-data"
    remote = _git("config", "--get", "remote.origin.url", cwd=root).strip()
    token = os.environ.get("GITHUB_TOKEN")
    if token and remote.startswith("https://github.com/"):
        # actions/checkout keeps its credentials in the parent repo only
        remote = remote.replace("https://github.com/", f"https://x-access-token:{token}@github.com/", 1)
    if d.exists():  # CI-owned scratch clone: always match the remote exactly
        _git("fetch", "origin", DATA_BRANCH, cwd=d)
        _git("reset", "--hard", f"origin/{DATA_BRANCH}", cwd=d)
        return d
    try:
        _git("clone", "--branch", DATA_BRANCH, "--single-branch", "--depth", "1", remote, str(d), cwd=root)
    except subprocess.CalledProcessError:  # first contribution: create the orphan branch
        d.mkdir()
        _git("init", "-b", DATA_BRANCH, cwd=d)
        _git("remote", "add", "origin", remote, cwd=d)
        (d / "README.md").write_text("# Pickaxe Tax contributions\n\nValidated GitHub contributions (ODbL 1.0). Written by CI only.\n")
    for k, v in (("user.name", "pickaxetax-bot"), ("user.email", "pickaxetax-bot@users.noreply.github.com")):
        _git("config", k, v, cwd=d)
    return d


def _commit_push(d: Path, msg: str) -> None:
    _git("add", "-A", cwd=d)
    if _git("status", "--porcelain", cwd=d).strip():
        _git("commit", "-m", msg, cwd=d)
        _git("push", "-u", "origin", DATA_BRANCH, cwd=d)


def _inline(text: object, limit: int = 200) -> str:
    """Error text quotes keys the submitter chose; keep it inside one inline code span."""
    return " ".join(str(text).replace("`", "'").split())[:limit]


def ingest_issue(event: dict, root: Path) -> str:
    issue = event.get("issue") or {}
    number = issue.get("number")
    author = (issue.get("user") or {}).get("login", "")
    comment = event.get("comment")
    if comment:
        if not str(comment.get("body", "")).strip().startswith("/withdraw"):
            return "ignored comment"
        if (comment.get("user") or {}).get("login") != author:
            _gh("POST", f"/issues/{number}/comments", {"body": "Only the original contributor can withdraw this contribution."})
            return "withdraw denied"
        d = _data_checkout(root)
        f = d / "github" / f"{number}.json"
        if f.exists():
            f.unlink()
            _commit_push(d, f"withdraw contribution #{number}")
        _gh("POST", f"/issues/{number}/comments", {"body": "Withdrawn: the data was removed and will disappear from the public aggregate at the next site build."})
        return "withdrawn"

    try:
        payload = payload_from_issue(issue.get("body") or "")
        errs = validate(payload)
    except ValueError as e:
        errs = [str(e)]
    if errs:
        msg = "Thanks! This contribution did not pass validation, so nothing was stored:\n\n" + "\n".join(f"- `{_inline(e)}`" for e in errs[:15])
        msg += "\n\nGenerate the payload with the web app or `pxt contribute --github`, then edit the issue to retry."
        _gh("POST", f"/issues/{number}/comments", {"body": msg})
        return "invalid"
    d = _data_checkout(root)
    (d / "github").mkdir(exist_ok=True)
    rec = {"issue": number, "login": author, "created_at": issue.get("created_at"), "verified": True, "payload": payload}
    (d / "github" / f"{number}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    _commit_push(d, f"contribution #{number} ({payload['kind']})")
    _gh("POST", f"/issues/{number}/comments", {"body": (
        "✅ Validated and stored as a **verified** contribution. It will appear in the public aggregate at the next site build. "
        "Comment `/withdraw` at any time to remove it. Thank you for helping measure the waste. #AntiTokenMaxing")})
    _gh("PATCH", f"/issues/{number}", {"state": "closed", "state_reason": "completed"})
    return "stored"
