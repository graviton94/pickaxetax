import pytest

from pickaxetax.analyze import analyze
from pickaxetax.graph import GraphStore, skeleton_cypher, skeleton_graph_json
from pickaxetax.ingest import parse_transcript


@pytest.fixture
def store(tmp_path):
    s = GraphStore(str(tmp_path / "g.sqlite3"))
    yield s
    s.close()


def chat(topic: str, extra: str = "") -> str:
    return (
        f"User: explain {topic} replication and {topic} indexing {extra}\n"
        f"Assistant: {topic} replication copies data; {topic} indexing speeds queries.\n"
        f"User: more about {topic} indexing performance\n"
        f"Assistant: {topic} indexing performance depends on selectivity.\n"
    )


# Distinct conversations on the same topic. Skeleton ids are built from simhash
# fingerprints, which are locality-sensitive on purpose: texts that differ by a single
# word ("case1" / "case2") can share an id under some salts and be stored as duplicates.
VARIANTS = ("for sharded clusters on kubernetes", "when restoring nightly backups", "during online schema migrations")


def test_roundtrip(store, ko_chat):
    sk = analyze(parse_transcript(ko_chat), salt=store.salt)
    assert store.save(sk, delete_token="tok")
    back = store.get(sk.id)
    assert back.to_dict() == sk.to_dict()


def test_duplicate_not_double_counted(store, ko_chat):
    sk = analyze(parse_transcript(ko_chat), salt=store.salt)
    assert store.save(sk, "a")
    assert not store.save(sk, "b")
    assert store.stats()["conversations"] == 1


def test_k_anonymity(store):
    for v in VARIANTS[:2]:
        assert store.save(analyze(parse_transcript(chat("postgres", v)), salt=store.salt), "t")
    assert store.topics(k=3)["nodes"] == []
    assert store.save(analyze(parse_transcript(chat("postgres", VARIANTS[2])), salt=store.salt), "t")
    labels = {n["label"] for n in store.topics(k=3)["nodes"]}
    assert "postgres" in labels
    assert all(n["conversations"] >= 3 for n in store.topics(k=3)["nodes"])


def test_k_cannot_be_lowered(store):
    store.save(analyze(parse_transcript(chat("redis")), salt=store.salt), "t")
    assert store.topics(k=1)["nodes"] == []


def test_delete(store):
    sks = [analyze(parse_transcript(chat("mongo", v)), salt=store.salt) for v in VARIANTS]
    for i, sk in enumerate(sks):
        assert store.save(sk, f"tok{i}")
    assert "mongo" in {n["label"] for n in store.topics()["nodes"]}
    assert not store.delete(sks[0].id, "wrong")
    assert store.delete(sks[0].id, "tok0")
    assert store.get(sks[0].id) is None
    assert store.stats()["conversations"] == 2
    assert "mongo" not in {n["label"] for n in store.topics()["nodes"]}  # fell below k
    assert store.db.execute("SELECT COUNT(*) FROM nodes WHERE id LIKE ?", (f"turn:{sks[0].id}:%",)).fetchone()[0] == 0


def test_raw_text_never_on_disk(tmp_path, ko_chat):
    path = tmp_path / "p.sqlite3"
    s = GraphStore(str(path))
    s.save(analyze(parse_transcript(ko_chat), salt=s.salt), "t")
    s.close()
    data = b"".join(p.read_bytes() for p in tmp_path.iterdir())
    for sentence in ("무한 루프가 발생하는 이유", "매 렌더마다 새로 생성되는", "api.get(id)", "별말씀을요"):
        assert sentence.encode() not in data


def test_salt_persists(tmp_path):
    a = GraphStore(str(tmp_path / "x.sqlite3"))
    salt = a.salt
    a.close()
    assert GraphStore(str(tmp_path / "x.sqlite3")).salt == salt


def test_exports(store, ko_chat):
    sk = analyze(parse_transcript(ko_chat), salt=store.salt)
    cy = skeleton_cypher(sk)
    assert cy.count("MERGE (t:Turn") == len(sk.turns)
    assert ":PIVOTS]" in cy
    g = skeleton_graph_json(sk)
    assert {n["kind"] for n in g["nodes"]} == {"turn", "topic"}


def test_cypher_escapes_labels():
    from pickaxetax.graph.export import _lit

    assert _lit('a"b\\c') == '"a\\"b\\\\c"'
