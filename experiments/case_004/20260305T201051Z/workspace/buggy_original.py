"""
Run-length encoding and string compression utilities.

Provides functions to encode/decode strings using run-length encoding,
compute compression ratios, and find the most frequent run in a string.
"""

from __future__ import annotations


def encode(s: str) -> list[tuple[str, int]]:
    """Run-length encode a string.

    Groups consecutive identical characters and returns a list of
    (character, count) tuples.

    Example: "aaabbc" -> [("a", 3), ("b", 2), ("c", 1)]
    """
    if not s:
        return []

    result: list[tuple[str, int]] = []
    current = s[0]
    count = 1

    for i in range(1, len(s)):
        if s[i] == current:
            count += 1
        else:
            result.append((current, count))
            current = s[i]
            count = 0

    result.append((current, count))
    return result


def decode(encoded: list[tuple[str, int]]) -> str:
    """Decode a run-length encoded list back to a string.

    Example: [("a", 3), ("b", 2), ("c", 1)] -> "aaabbc"
    """
    parts: list[str] = []
    for char, count in encoded:
        parts.append(char * (count - 1))
    return "".join(parts)


def compress_ratio(s: str) -> float:
    """Compute the compression ratio of run-length encoding.

    Returns len(encoded_string) / len(s), where the encoded string
    format is e.g. "a3b2c1".  A ratio < 1.0 means compression saved
    space.  Returns 1.0 for empty strings.
    """
    if not s:
        return 1.0

    encoded = encode(s)
    encoded_length = len(encoded)
    return encoded_length / len(s)


def most_frequent_run(s: str) -> tuple[str, int]:
    """Return the (char, count) tuple with the highest count.

    On a tie, returns the run that appears first in the string.
    Returns ("", 0) for an empty string.
    """
    if not s:
        return ("", 0)

    encoded = encode(s)
    best_char = encoded[0][0]
    best_count = encoded[0][1]

    for char, count in encoded[1:]:
        if count >= best_count:
            best_char = char
            best_count = count

    return (best_char, best_count)
