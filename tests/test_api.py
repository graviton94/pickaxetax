import pytest
from fastapi.testclient import TestClient

from antitoken.graph import GraphStore
from antitoken.web import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(GraphStore(str(tmp_path / "api.sqlite3"))))


def test_analyze_get_delete(client, ko_chat):
    r = client.post("/api/analyze", json={"input": ko_chat, "save": True})
    assert r.status_code == 200, r.text
    [res] = r.json()["results"]
    sid, token = res["skeleton"]["id"], res["delete_token"]
    assert res["saved"] and token

    assert client.get(f"/api/conversations/{sid}").json()["id"] == sid
    assert client.get(f"/api/conversations/{sid}/graph.json").status_code == 200
    assert "MERGE" in client.get(f"/api/conversations/{sid}/cypher").text
    assert client.get("/api/stats").json()["conversations"] == 1

    assert client.delete(f"/api/conversations/{sid}", headers={"X-Delete-Token": "nope"}).status_code == 404
    assert client.delete(f"/api/conversations/{sid}", headers={"X-Delete-Token": token}).status_code == 200
    assert client.get(f"/api/conversations/{sid}").status_code == 404


def test_no_save_persists_nothing(client, en_chat):
    r = client.post("/api/analyze", json={"input": en_chat, "save": False})
    [res] = r.json()["results"]
    assert not res["saved"] and res["delete_token"] is None
    assert client.get(f"/api/conversations/{res['skeleton']['id']}").status_code == 404
    assert client.get("/api/stats").json()["conversations"] == 0


def test_file_upload(client):
    data = b'[{"role":"user","content":"what is a b-tree index"},{"role":"assistant","content":"a balanced tree"}]'
    r = client.post("/api/analyze/file", files={"file": ("c.json", data, "application/json")}, data={"save": "false"})
    assert r.status_code == 200, r.text


def test_bad_inputs(client):
    assert client.post("/api/analyze", json={"input": "no roles here"}).status_code == 400
    r = client.post("/api/analyze", json={"input": "https://evil.example.com/share/1"})
    assert r.status_code == 400 and "not allowed" in r.json()["detail"]


def test_error_does_not_echo_input(client):
    secret = "my secret plan for world domination"
    r = client.post("/api/analyze", json={"input": secret})
    assert secret not in r.text


def test_index_served(client):
    for path in ("/", "/explore", "/c/abc"):
        r = client.get(path)
        assert r.status_code == 200 and "ANTI" in r.text
    assert client.get("/static/app.js").status_code == 200
