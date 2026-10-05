from antitoken.tokens import estimate_tokens


def test_empty():
    assert estimate_tokens("") == 0


def test_cjk_counts_more_per_char_than_latin():
    assert estimate_tokens("안녕하세요반갑습니다") >= 8
    assert 2 <= estimate_tokens("hello world, how are you") <= 10


def test_monotonic():
    assert estimate_tokens("word " * 100) > estimate_tokens("word " * 10)
