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
            count = 1  # Fix: Reset count to 1 for the new character
    
    # Append the last run
    result.append((current, count))
    return result


def decode(encoded: list[tuple[str, int]]) -> str:
    """Decode a run-length encoded list back to a string.

    Example: [("a", 3), ("b", 2), ("c", 1)] -> "aaabbc"
    """
    parts: list[str] = []
    for char, count in encoded:
        parts.append(char * count)  # Fix: Use count directly, not (count - 1)
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
    encoded_length_str_format = 0
    for _, count in encoded:
        encoded_length_str_format += 1  # For the character itself
        encoded_length_str_format += len(str(count))  # For the digit(s) of the count
    
    return encoded_length_str_format / len(s)


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
        # Fix: Only update if current count is strictly greater to prefer earlier runs on a tie.
        if count > best_count: 
            best_char = char
            best_count = count

    return (best_char, best_count)

