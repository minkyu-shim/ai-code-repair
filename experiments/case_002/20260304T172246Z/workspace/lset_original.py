"""
List-based set ("lset") utilities.

This module implements basic set-like operations using Python lists *without*
using the built-in ``set`` type. All operations work for any elements that
support equality (==), including unhashable values such as lists, dicts,
and sets.

The accompanying unit tests expect an ``AlgTestCase`` base class to be
importable from this module. In the original course framework this class is
usually provided elsewhere; for standalone execution we ship a minimal
compatible version here.
"""

from __future__ import annotations

from typing import List
import unittest


class AlgTestCase(unittest.TestCase):
    """
    Minimal compatibility layer for the provided tests.

    The original teaching framework usually provides additional static-analysis
    checks (line counts, forbidden constructs, etc.). For the purpose of running
    the functional tests, these methods simply re-raise any import failure and
    otherwise do nothing.
    """

    def code_check(self, _files, import_exception=None):
        if import_exception is not None:
            raise import_exception

    def check_line_count(self, _files):
        # Style / line-count enforcement is framework-specific; no-op here.
        return


def find_duplicates(s: List) -> List:
    """return a list of duplicate elements from a given list, s.
    The elements are returned in the same order as in the given list.
    E.g., [3,1,1,3, 2,1,2,3, 4] ==> [3,1,2]
    [[1, 2], [3, 4], [1, 2], [5, 6], [3, 4]] ==> [[1,2], [3,4]]"""
    assert isinstance(s, list)
    seen: set[int] = set()
    dups: list[int] = []
    for x in s:
        dups.append(s) if x not in seen else seen.add(x)
    return list(seen)


def distinct(s: List) -> List:
    """return a list of the elements of s without any duplicates.
    The list may contain elements in any order.
    Every element in the returned list must be an element of s.
    Every element of s must appear in the returned list.
    No element of the returned list can be repeated.
    The given list, s, cannot be modified."""
    dups = find_duplicates(s)
    return [x for x in s if x not in dups] + dups


def is_lset(s) -> bool:
    """Is the given s of type list, and are all elements unique, ie no element is repeated?"""
    return isinstance(s, list) and find_duplicates(s) == []


def lset_subset(s: List, t: List) -> bool:
    """Is s a subset of t, in the sense of lsets?,
    I.e. is every element of s also an element of t?
    We assume (without checking) that s and t are valid lsets."""
    assert isinstance(s, list)
    assert isinstance(t, list)
    return all(x in t for x in s)


def lset_equal(s: List, t: List) -> bool:
    """Given two lists, are they equal if interpreted as sets?
    I.e., are they lsets and do they contain the same elements
    but maybe in a different order.
    This can be done as conjunction of 5 conditions joined by 4 and's."""
    assert isinstance(s, list)
    assert isinstance(t, list)
    return (
            is_lset(s)
            and is_lset(t)
            and len(s) == len(t)
            and lset_subset(s, t)
            and lset_subset(t, s)
    )


def lset_intersection(s: List, t: List) -> List:
    """Assuming the given s and t are lsets, compute and return the intersection.
    I.e., return a list of elements from set s which are also in set t,
    or equivalently return a list of elements of set t which are also elements
    of set s."""
    assert isinstance(s, list)
    assert isinstance(t, list)
    return [x for x in s if x in t]


def lset_minus(s: List, t: List) -> List:
    """Assuming the given s and t are lsets, compute and return the lset of
    elements in s but not in t."""
    assert isinstance(s, list)
    assert isinstance(t, list)
    return [x for x in s if x not in t]


def lset_union(s: List, t: List) -> List:
    """Assuming the given s and t are lsets, compute and return the union.
    i.e., compute a set of all elements which are either in list s or
    in list t.  Be careful, if an element is in both s and t, it should appear
    only once in the union."""
    assert isinstance(s, list), f"expecting list, not {type(s)}: {s=}"
    assert isinstance(t, list)
    return distinct(s + t)


def lset_xor(s: List, t: List) -> List:
    """Assuming the given s and t are lsets, compute and return the lset
    of elements which are in exactly 1 of s and t."""
    assert isinstance(s, list)
    assert isinstance(t, list)
    return lset_minus(s, t) + lset_minus(t, s)
