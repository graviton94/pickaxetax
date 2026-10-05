from pickaxetax.analyze import analyze
from pickaxetax.analyze import intent as I
from pickaxetax.ingest import parse_transcript
from pickaxetax.models import USER


def sk_of(text, salt=b"s"):
    return analyze(parse_transcript(text), salt=salt)


def user_intents(sk):
    return [t.intent for t in sk.turns if t.role == USER]


def test_korean_intents_and_structure(ko_chat):
    sk = sk_of(ko_chat)
    assert sk.language == "ko"
    assert user_intents(sk) == [I.INSTRUCT, I.INSTRUCT, I.CORRECT, I.ACK, I.INSTRUCT, I.ACK]
    types = {(e.src, e.type) for e in sk.edges}
    assert (2, "DEEPENS") in types  # follow-up on the answer's own topics
    assert (4, "CORRECTS") in types
    assert (8, "PIVOTS") in types  # pandas is a different thread
    assert sk.metrics["branches"] == 2
    assert "pandas" in sk.agenda


def test_english_retry_continue_ack(en_chat):
    sk = sk_of(en_chat)
    assert sk.language == "en"
    assert user_intents(sk) == [I.ASK, I.RETRY, I.INSTRUCT, I.CONTINUE, I.ACK]
    assert any(e.type == "RETRIES" for e in sk.edges)
    # the first answer was superseded by the retry
    assert sk.turns[1].redundant and sk.turns[2].redundant


def test_waste_accounting(ko_chat):
    m = sk_of(ko_chat).metrics
    assert m["billed_input_tokens"] > m["visible_tokens"]  # history is re-read
    assert m["optimized_compute_units"] < m["compute_units"]
    assert m["one_shot_compute_units"] <= m["optimized_compute_units"]
    assert 0 < m["savings_pct"] < 100
    assert m["waste"]["ack_units"] > 0
    assert m["waste"]["superseded_units"] > 0


def test_clean_conversation_has_little_waste():
    sk = sk_of("User: What is the capital of France?\nAssistant: Paris is the capital of France.")
    assert sk.metrics["savings_pct"] == 0.0
    assert sk.suggestion["tips"] == []


def test_quadratic_context_growth():
    turns = "".join(f"User: question about topic{i} database index tuning\nAssistant: {'answer ' * 50}\n" for i in range(10))
    m = sk_of(turns).metrics
    assert m["billed_input_tokens"] > 3 * m["visible_tokens"]


def test_id_is_salted_and_deterministic(ko_chat):
    assert sk_of(ko_chat, b"a").id == sk_of(ko_chat, b"a").id
    assert sk_of(ko_chat, b"a").id != sk_of(ko_chat, b"b").id
    assert sk_of(ko_chat, b"a").turns[0].fingerprint != sk_of(ko_chat, b"b").turns[0].fingerprint


def test_pii_never_becomes_topic():
    text = (
        "User: email john.doe@example.com and call +82 10-1234-5678 about the kubernetes deployment, key sk-abcdefghijklmnop1234\n"
        "Assistant: For the kubernetes deployment, check the deployment manifest.\n"
        "User: kubernetes deployment still failing, mail john.doe@example.com\n"
        "Assistant: Check kubernetes events."
    )
    sk = sk_of(text)
    labels = set(sk.agenda) | {x for t in sk.turns for x in t.topics}
    assert "kubernetes" in labels
    for bad in ("john.doe", "example.com", "1234", "5678", "sk-abcdefghijklmnop1234", "abcdefghijklmnop1234"):
        assert not any(bad in label for label in labels)


def test_skeleton_contains_no_sentences(ko_chat):
    import json

    blob = json.dumps(sk_of(ko_chat).to_dict(), ensure_ascii=False)
    for sentence in ("무한 루프가 발생하는 이유", "매 렌더마다 새로 생성되는", "api.get(id)"):
        assert sentence not in blob


def test_prompt_template_language(ko_chat, en_chat):
    assert sk_of(ko_chat).suggestion["prompt_template"].startswith("[목표]")
    assert sk_of(en_chat).suggestion["prompt_template"].startswith("[Goal]")


def test_tips_ranked_by_weight(ko_chat):
    tips = sk_of(ko_chat).suggestion["tips"]
    assert {t["code"] for t in tips} >= {"ack", "redo", "pivot"}
    assert [t["weight"] for t in tips] == sorted((t["weight"] for t in tips), reverse=True)


def test_pivot_detected_even_when_topic_is_privacy_filtered():
    # "pandas" is mentioned once and never echoed, so it is not a stored label,
    # but the turn must still open a new thread.
    text = (
        "User: Why does my React useEffect run in an infinite loop?\n"
        "Assistant: The dependency array contains a function recreated on every render. Use useCallback.\n"
        "User: Show me a useCallback dependency array example\n"
        "Assistant: const f = useCallback(() => load(id), [id]);\n"
        "User: thanks!\n"
        "Assistant: You're welcome!\n"
        "User: How do I merge two pandas dataframes in Python?\n"
        "Assistant: Use pd.merge(df1, df2, on='key').\n"
    )
    sk = sk_of(text)
    assert sk.metrics["branches"] == 2
    assert (6, "PIVOTS") in {(e.src, e.type) for e in sk.edges}
