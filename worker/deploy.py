"""Deploy the contribution worker from CI. Needs CLOUDFLARE_API_TOKEN and
CLOUDFLARE_ACCOUNT_ID. Idempotent: creates the D1 database and the
workers.dev subdomain only if missing, applies the schema, deploys, then
health-checks. Prints the worker URL."""

import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
ACCOUNT = os.environ["CLOUDFLARE_ACCOUNT_ID"]
API = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}"
DB_NAME = "pickaxetax"
WORKER = "pickaxetax-contrib"


def wrangler(*args, capture=True):
    r = subprocess.run(["npx", "--yes", "wrangler", *args], cwd=HERE, capture_output=capture, text=True)
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
        raise SystemExit(f"wrangler {' '.join(args)} failed")
    return r.stdout


def api(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


def database_id():
    for db in json.loads(wrangler("d1", "list", "--json") or "[]"):
        if db.get("name") == DB_NAME:
            return db.get("uuid") or db.get("id") or db.get("database_id")
    wrangler("d1", "create", DB_NAME)
    for db in json.loads(wrangler("d1", "list", "--json") or "[]"):
        if db.get("name") == DB_NAME:
            return db.get("uuid") or db.get("id") or db.get("database_id")
    raise SystemExit("could not create the D1 database")


def subdomain():
    res = api("GET", "/workers/subdomain")
    sub = (res.get("result") or {}).get("subdomain")
    if sub:
        return sub
    for name in ("pickaxetax", f"pickaxetax-{secrets.token_hex(3)}"):
        res = api("PUT", "/workers/subdomain", {"subdomain": name})
        if res.get("success"):
            return name
    raise SystemExit(f"could not register a workers.dev subdomain: {res.get('errors')}")


def main():
    db = database_id()
    toml = (HERE / "wrangler.template.toml").read_text().replace("__DATABASE_ID__", db)
    (HERE / "wrangler.toml").write_text(toml)
    wrangler("d1", "execute", DB_NAME, "--remote", "--file", "schema.sql", "--yes")
    sub = subdomain()
    wrangler("deploy")
    url = f"https://{WORKER}.{sub}.workers.dev"
    for _ in range(12):  # new subdomains take a moment to resolve
        try:
            with urllib.request.urlopen(url + "/health", timeout=10) as r:
                if r.status == 200:
                    print(url)
                    return
        except OSError:
            pass
        time.sleep(10)
    print(url)
    sys.stderr.write("warning: health check did not pass yet; the site build will retry\n")


if __name__ == "__main__":
    main()
