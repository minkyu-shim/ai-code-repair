"""Tests for the run-length encoding module."""

from buggy import encode, decode, compress_ratio, most_frequent_run


# ---------------------------------------------------------------------------
# Tests for encode
# ---------------------------------------------------------------------------

def test_encode_single_char():
    """A single character encodes to one run of length 1."""
    assert encode("a") == [("a", 1)]


def test_encode_single_run():
    """A string of identical characters is one run."""
    assert encode("aaaa") == [("a", 4)]


def test_encode_multiple_runs():
    """Multiple distinct runs are captured with correct counts."""
    assert encode("aaabbc") == [("a", 3), ("b", 2), ("c", 1)]


def test_encode_alternating():
    """Each character in an alternating string is its own run of length 1."""
    assert encode("abab") == [("a", 1), ("b", 1), ("a", 1), ("b", 1)]


def test_encode_empty():
    """An empty string encodes to an empty list."""
    assert encode("") == []


# ---------------------------------------------------------------------------
# Tests for decode
# ---------------------------------------------------------------------------

def test_decode_simple():
    """Decode reconstructs the original string from runs."""
    assert decode([("a", 3), ("b", 2), ("c", 1)]) == "aaabbc"


def test_decode_single_char_runs():
    """Runs of length 1 each produce a single character."""
    assert decode([("x", 1), ("y", 1), ("z", 1)]) == "xyz"


def test_decode_empty():
    """Decoding an empty list returns an empty string."""
    assert decode([]) == ""


# ---------------------------------------------------------------------------
# Tests for roundtrip (encode then decode)
# ---------------------------------------------------------------------------

def test_roundtrip_basic():
    """Encoding then decoding must reproduce the original string."""
    original = "aaabbbcccc"
    assert decode(encode(original)) == original


def test_roundtrip_single_chars():
    """Roundtrip must work for strings with no repeated characters."""
    original = "abcdef"
    assert decode(encode(original)) == original


# ---------------------------------------------------------------------------
# Tests for compress_ratio
# ---------------------------------------------------------------------------

def test_compress_ratio_all_same():
    """A string of all identical chars compresses well."""
    # "aaaaaaaaaa" (10 chars) -> encoded string "a10" (3 chars)
    # ratio = 3 / 10 = 0.3
    assert abs(compress_ratio("a" * 10) - 0.3) < 0.01


def test_compress_ratio_no_compression():
    """Alternating chars produce no compression benefit."""
    # "abcd" -> encoded string "a1b1c1d1" (8 chars)
    # ratio = 8 / 4 = 2.0
    assert abs(compress_ratio("abcd") - 2.0) < 0.01


def test_compress_ratio_empty():
    """Empty string returns 1.0 by convention."""
    assert compress_ratio("") == 1.0


# ---------------------------------------------------------------------------
# Tests for most_frequent_run
# ---------------------------------------------------------------------------

def test_most_frequent_run_clear_winner():
    """The longest run is unambiguous."""
    assert most_frequent_run("aabbbcc") == ("b", 3)


def test_most_frequent_run_tie_first_wins():
    """When runs tie in length, the first one in the string wins."""
    # "bbbcccaaa" has three runs of length 3; first is "b"
    assert most_frequent_run("bbbcccaaa") == ("b", 3)


def test_most_frequent_run_empty():
    """Empty string returns the sentinel value."""
    assert most_frequent_run("") == ("", 0)


# ---------------------------------------------------------------------------
# Hidden tests -- stricter invariants for overfitting detection
# ---------------------------------------------------------------------------

def test_hidden_encode_preserves_total_length():
    """Sum of all run counts must equal the length of the original string."""
    s = "xxyyyzz"
    total = sum(count for _, count in encode(s))
    assert total == len(s)


def test_hidden_roundtrip_stress():
    """Roundtrip must hold for a longer string with many short runs."""
    original = "aabbccddee" * 5  # 50 chars, 25 runs of 2
    assert decode(encode(original)) == original
