from antitoken.cbi import COLUMNS, validate_csv

ROW = {
    "id": "acme-capex-ai-2025q1", "entity": "Acme Cloud", "metric": "capex_ai", "value": "12.5", "unit": "USD bn",
    "period_start": "2025-01-01", "period_end": "2025-03-31", "grade": "reported",
    "source_url": "https://example.com/10-q", "source_title": "Form 10-Q", "accessed": "2026-10-01",
    "curator": "alice", "verifier": "bob", "notes": "",
}


def write(tmp_path, rows, header=COLUMNS):
    p = tmp_path / "d.csv"
    lines = [",".join(header)] + [",".join(r.get(c, "") for c in header) for r in rows]
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def test_header_only_is_valid(tmp_path):
    assert validate_csv(write(tmp_path, [])) == []


def test_good_row(tmp_path):
    assert validate_csv(write(tmp_path, [ROW])) == []


def test_two_person_rule(tmp_path):
    assert any("unverified" in e for e in validate_csv(write(tmp_path, [dict(ROW, verifier="")])))
    assert validate_csv(write(tmp_path, [dict(ROW, verifier="")]), require_verified=False) == []
    assert any("differ" in e for e in validate_csv(write(tmp_path, [dict(ROW, verifier="alice")])))


def test_bad_values(tmp_path):
    errs = validate_csv(write(tmp_path, [dict(ROW, metric="vibes", grade="rumor", value="lots",
                                              source_url="http://x", accessed="yesterday")]))
    joined = " ".join(errs)
    for frag in ("unknown metric", "grade", "numeric", "https", "YYYY-MM-DD"):
        assert frag in joined


def test_duplicate_ids_and_header(tmp_path):
    assert any("duplicate" in e for e in validate_csv(write(tmp_path, [ROW, ROW])))
    assert "header" in validate_csv(write(tmp_path, [], header=COLUMNS[:-1]))[0]


def test_repo_data_files_valid():
    assert validate_csv("cbi/capital.csv") == []
    assert validate_csv("cbi/drafts.csv", require_verified=False) == []
