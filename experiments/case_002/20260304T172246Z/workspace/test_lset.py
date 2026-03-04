import random
import sys
import os

# Make the directory containing this file (and lset.py) importable.
HERE = os.path.abspath(os.path.dirname(__file__))
PARENT = os.path.abspath(os.path.join(HERE, ".."))

# Support both layouts:
#   case_002/lset.py + case_002/test_lset.py
#   case_002/lset.py + case_002/tests/test_lset.py
if os.path.exists(os.path.join(HERE, "lset.py")):
    sys.path.insert(0, HERE)
else:
    sys.path.insert(0, PARENT)

import_exception = None
try:
    from lset import *
except Exception as e:
    print(e)
    import_exception = e

from lset import AlgTestCase

num_repetitions = 100
test_size = 10


def random_list():
    return [random.choice(range(100))
            for k in range(test_size)
            if random.choice([True, False])]


not_lsets = [[1, 1],
             [[], []],
             [{'a': 1}, {'a': 1}, {'a': 1}]
             ]

lsets = [[],
         [1],
         [1, 2, 3],
         [{'a': 1}],
         [{'a': 1}, {'a': 2}],
         [{'a': 1}, {'a': 2}, {'a': 4}],
         [{1}],
         [{1}, {2}],
         [{1}, {2}, {4}],
         [({1}, {2}), ({1}, {3}), ({2}, {3})]
         ]


class LsetTestCase(AlgTestCase):
    def test_code_check(self):
        self.code_check(["lset.py"], import_exception)

    def test_line_count(self):
        self.check_line_count(["lset.py"])

    def check_lsets(self):
        # The purpose of this method is to try to call all tests
        #  to fail if the student used set() to implement the lset functions
        for s in lsets:
            self.assertTrue(is_lset(s), f"is_lset miscalculated.  {s} should be considered an lset")
        for s in not_lsets:
            self.assertFalse(is_lset(s), f"is_lset miscalculated.  {s} should NOT be considered an lset")
        self.assertEqual(distinct([{1}, {1}]), [{1}], f"distinct failed")
        self.assertEqual(distinct([({1}, {2}), ({1}, {2})]), [({1}, {2})], f"distinct failed")
        self.assertEqual(find_duplicates([{1}, {1}]), [{1}], f"find_duplicates failed")
        self.assertEqual(find_duplicates([({1}, {2}), ({1}, {2})]), [({1}, {2})], f"find_duplicates failed")

    def test_find_duplicates_0(self):
        self.assertEqual(find_duplicates([]), [])
        self.assertEqual(find_duplicates([1]), [])
        self.assertEqual(find_duplicates([1, 2]), [])
        self.assertEqual(find_duplicates([1, 3]), [])
        self.check_lsets()

    def test_find_duplicates_1(self):
        self.assertEqual(find_duplicates([1, 1]), [1])
        self.assertEqual(find_duplicates([1, 1, 1]), [1])
        self.assertEqual(find_duplicates([1, 1, 1, 1]), [1])
        self.assertEqual(find_duplicates([1, 1, 2, 2, 3, 3]), [1, 2, 3])
        self.check_lsets()

    def test_find_duplicates_detect_change(self):
        for _ in range(num_repetitions):
            data1 = random_list()
            data2 = [x for x in data1]
            find_duplicates(data1)
            self.assertEqual(data1, data2, f"a call to find_duplicated changed the input list from {data2} to {data1}")
        self.check_lsets()

    def test_find_duplicates_order(self):
        for _ in range(num_repetitions):
            data = [k for k in range(test_size)
                    if random.choice([True, False])]
            self.assertEqual(find_duplicates(data + data), data)
            self.assertEqual(find_duplicates(data + data + data), data)
        self.check_lsets()

    def test_find_duplicates_non_int(self):
        self.assertEqual(find_duplicates([[1], [1], [2], [2], [3], [3]]), [[1], [2], [3]])
        for _ in range(num_repetitions):
            for data in [[{k} for k in range(test_size)
                          if random.choice([True, False])],
                         [[k] for k in range(test_size)
                          if random.choice([True, False])],
                         [{k, k + 1} for k in range(test_size)
                          if random.choice([True, False])],
                         [[k, k + 1] for k in range(test_size)
                          if random.choice([True, False])]]:
                self.assertEqual(find_duplicates(data + data), data)
        self.check_lsets()

    def test_distinct_0(self):
        self.assertEqual(distinct([]), [])
        self.assertEqual(distinct([1]), [1])
        self.assertEqual(distinct([1, 1]), [1])
        self.assertEqual(distinct([1, 1, 1]), [1])
        self.check_lsets()

    def test_distinct_1(self):
        from random import shuffle
        for r in range(num_repetitions):
            data = []
            for k in range(test_size):
                data += [{k} for j in range(3)
                         if random.choice([True, False])]
            shuffle(data)
            dis = distinct(data)
            for d in dis:
                self.assertTrue(d in data, f"{d} not in {data} when {dis=}")
            for d in data:
                self.assertTrue(d in dis, f"{d} not in {dis} when {data=}")
            for d in dis:
                c = len([x for x in dis if d == x])
                self.assertEqual(1, c, f"{d} appears {c} times in {dis=} when {data=}")
        self.check_lsets()

    def test_distinct_2(self):
        from random import shuffle
        for r in range(num_repetitions):
            data = []
            for k in range(test_size):
                data += [k for j in range(3)
                         if random.choice([True, False])]
            shuffle(data)
            copy_data = [d for d in data]
            dis = distinct(data)
            self.assertEqual(data, copy_data, f"distinct(...) mutated its input")
        self.check_lsets()

    def test_is_set_0(self):
        self.assertFalse(is_lset({}))
        self.assertFalse(is_lset(0))
        self.assertFalse(is_lset({'a': 3}))
        self.check_lsets()

    def test_is_set_1(self):
        self.assertTrue(is_lset([]))
        self.assertTrue(is_lset([1]))
        self.assertTrue(is_lset([1, 2]))
        self.assertTrue(is_lset([1, 2, 3]))
        self.assertFalse(is_lset([1, 1]))
        self.assertFalse(is_lset([1, 2, 3, 1, 2, 3]))
        self.check_lsets()

    def test_is_set_2(self):
        self.assertTrue(is_lset([]))
        self.assertTrue(is_lset([[]]))
        self.assertTrue(is_lset([[[]]]))
        self.assertTrue(is_lset([[[[]]]]))
        self.check_lsets()

    def test_is_set_3(self):
        self.assertTrue(is_lset([]))
        self.assertTrue(is_lset([{}]))
        self.assertFalse(is_lset([{}, {}]))
        self.check_lsets()

    def test_is_set_4(self):
        self.assertTrue(is_lset([]))
        self.assertTrue(is_lset([{'a': 1}]))
        self.assertFalse(is_lset([{'a': 1}, {'a': 1}]))
        self.assertTrue(is_lset([{'a': 1}, {'a': 2}]))
        self.assertTrue(is_lset([{'a': 1}, {'a': 2}, {'a': 4}]))
        self.check_lsets()

    def test_is_lset_modified(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            data1 = random_list()
            data2 = [k for k in data1]
            is_lset(data1)
            self.assertEqual(data1, data2,
                             f"a call to is_lset modified its input from {data2} to {data1}")

    # renamed to avoid overriding the earlier test_is_set_1
    def test_is_set_randomized(self):
        self.check_lsets()
        self.assertTrue(is_lset([{}]))
        for _ in range(num_repetitions):
            self.assertTrue(is_lset([k for k in range(test_size)
                                     if random.choice([True, False])]))
            self.assertTrue(is_lset([[k] for k in range(test_size)
                                     if random.choice([True, False])]))
            self.assertTrue(is_lset([{k} for k in range(test_size)
                                     if random.choice([True, False])]))
            for x in [[j for k in range(test_size)
                       if random.choice([True, False])
                       for j in [k, k]
                       ],
                      [j for k in range(test_size)
                       if random.choice([True, False])
                       for j in [[k], [k]]],
                      [j for k in range(test_size)
                       if random.choice([True, False])
                       for j in [{k}, {k}]]
                      ]:
                if x != []:
                    self.assertFalse(is_lset(x), f"{x} should not be an lset")

    def test_lset_subset_0(self):
        self.check_lsets()
        self.assertTrue(lset_subset([], []))
        self.assertTrue(lset_subset([], [1]))
        self.assertFalse(lset_subset([1], []))
        self.assertTrue(lset_subset([1], [1]))

    def test_lset_subset_modified(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            data1 = random_list()
            data1_copy = [k for k in data1]
            data2 = random_list()
            data2_copy = [k for k in data2]
            lset_subset(data1, data2)
            self.assertEqual(data1, data1_copy,
                             f"a call to is_lset modified its 1st input from {data1_copy} to {data1}")
            self.assertEqual(data2, data2_copy,
                             f"a call to is_lset modified its 2nd input from {data2_copy} to {data2}")

    def test_lset_subset(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            super = [[k] for k in range(test_size)
                     if random.choice([True, False])]
            sub = [x for x in super
                   if random.choice([True, False])]
            self.assertTrue(lset_subset(sub, super))
            self.assertFalse(lset_subset(sub + [-1], super))

    def test_lset_equal_0(self):
        self.check_lsets()
        self.assertTrue(lset_equal([1, 2, 3], [2, 1, 3]))
        self.assertTrue(lset_equal([], []))
        self.assertFalse(lset_equal([1, 1], [1, 2]))  # not equal lsets because not lsets
        self.assertFalse(lset_equal([1, 2, 3], [2, 3]))
        self.assertFalse(lset_equal([2, 3], [1, 2, 3]))

    def test_lset_equal_0b(self):
        self.check_lsets()
        self.assertTrue(lset_equal([{1}, {2}, {3}], [{2}, {1}, {3}]))
        self.assertTrue(lset_equal([], []))
        self.assertFalse(lset_equal([{1}, {2}, {3}], [{2}, {3}]))
        self.assertFalse(lset_equal([{2}, {3}], [{1}, {2}, {3}]))

    def test_lset_equal_0c(self):
        self.check_lsets()
        self.assertTrue(lset_equal([1, 2, 3], [2, 1, 3]))
        self.assertTrue(lset_equal([], []))
        self.assertFalse(lset_equal([1, 2, 3], [2, 3]))
        self.assertFalse(lset_equal([2, 3], [1, 2, 3]))

    def test_lset_equal_1(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            g = [k for k in range(test_size)
                 if random.choice([True, False])]
            h = [k for k in reversed(g)]
            self.assertTrue(lset_equal(g, h))

    def test_lset_intersection(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            g = distinct([{k, -k} for k in range(test_size)
                          if random.choice([True, False])])
            h = distinct([{k, -k} for k in range(test_size)
                          if random.choice([True, False])])
            a = lset_intersection(h, g)
            self.assertTrue(is_lset(a), f"lset_intersection failed to return an lset, {a}")
            for x in a:
                self.assertTrue(x in g)
                self.assertTrue(x in h)
            for x in g:
                if x in h:
                    self.assertTrue(x in a)
            for x in h:
                if x in g:
                    self.assertTrue(x in a)

    def test_lset_range(self):
        self.check_lsets()
        self.assertFalse(is_lset([range(1, -1, 2), range(4, -4, 2)]))
        self.assertFalse(is_lset([range(2, -2, 2), range(6, -6, 2)]))

    def test_lset_union(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            g = distinct([{k, -k} for k in range(test_size)
                          if random.choice([True, False])])
            h = distinct([{k, -k} for k in range(test_size)
                          if random.choice([True, False])])
            a = lset_union(h, g)
            self.assertTrue(is_lset(a), f"lset_union failed to return an lset, {a}")
            for x in a:
                self.assertTrue(x in g or x in h)
            for x in g:
                self.assertTrue(x in a)
            for x in h:
                self.assertTrue(x in a)

    def test_lset_xor(self):
        self.check_lsets()
        for _ in range(num_repetitions * 10):
            g = distinct([range(k, -k, 2) for k in range(test_size)
                          if random.choice([True, False])])
            h = distinct([range(k, -k, 2) for k in range(test_size)
                          if random.choice([True, False])])
            a = lset_xor(h, g)
            for i, x in enumerate(a):
                for j, y in enumerate(a):
                    if i != j:
                        assert x != y, f"lset_xor failed to return an lset, lset_xor returned {a}, but {x} = {y}"
            self.assertTrue(is_lset(a), f"lset_xor failed to return an lset, {a}")
            for x in a:
                if x in g:
                    self.assertFalse(x in h)
                else:
                    self.assertTrue(x in h)
                if x in h:
                    self.assertFalse(x in g)
                else:
                    self.assertTrue(x in g)
            for x in g:
                if x in h:
                    self.assertFalse(x in a)
                else:
                    self.assertTrue(x in a)
            for x in h:
                if x in g:
                    self.assertFalse(x in a)
                else:
                    self.assertTrue(x in a)

    def test_lset_minus(self):
        self.check_lsets()
        for _ in range(num_repetitions * 50):
            g = distinct([range(k, -k, 2) for k in range(test_size)
                          if random.choice([True, False])])
            h = distinct([range(k, -k, 2) for k in range(test_size)
                          if random.choice([True, False])])
            a = lset_minus(h, g)
            for i, x in enumerate(a):
                for j, y in enumerate(a):
                    if i != j:
                        assert x != y, f"lset_minus({h},{g}) failed to return an lset, lset_minus returned {a}, but {x} = {y}"
            self.assertTrue(is_lset(a), f"lset_minus failed to return an lset, {a}")
            for x in a:
                self.assertTrue(x in h)
            for x in g:
                self.assertFalse(x in a)
            for x in h:
                if x in g:
                    self.assertFalse(x in a)
                else:
                    self.assertTrue(x in a)

    def test_set_operations(self):
        self.check_lsets()
        self.assertTrue(lset_equal(lset_intersection([], []),
                                   []))
        self.assertTrue(lset_equal(lset_union([], []),
                                   []))
        self.assertTrue(lset_equal(lset_xor([], []),
                                   []))
        self.assertTrue(lset_equal(lset_minus([], []),
                                   []))

        self.assertTrue(lset_equal(lset_intersection([1], []),
                                   []))
        self.assertTrue(lset_equal(lset_union([1], []),
                                   [1]))
        self.assertTrue(lset_equal(lset_xor([1], []),
                                   [1]))
        self.assertTrue(lset_equal(lset_minus([1], []),
                                   [1]))

        self.assertTrue(lset_equal(lset_intersection([1], [1, 2]),
                                   [1]))
        self.assertTrue(lset_equal(lset_union([1], [1, 2]),
                                   [1, 2]))
        self.assertTrue(lset_equal(lset_xor([1], [1, 2]),
                                   [2]))
        self.assertTrue(lset_equal(lset_minus([1], [1, 2]),
                                   []))
        self.assertTrue(lset_equal(lset_minus([1, 2], [1]),
                                   [2]))

    def test_lset_commutative(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            g = [{k, k + 1, k - 1} for k in range(test_size)
                 if random.choice([True, False])]
            h = [{k, k + 1, k - 1} for k in range(test_size)
                 if random.choice([True, False])]
            self.assertTrue(lset_equal(lset_intersection(g, h),
                                       lset_intersection(h, g)),
                            f"lset intersection should be commutative: h={h} g={g}")
            self.assertTrue(lset_equal(lset_union(g, h),
                                       lset_union(h, g)),
                            f"lset union should be commutative: h={h} g={g}")
            self.assertTrue(lset_equal(lset_xor(g, h),
                                       lset_xor(h, g)),
                            f"lset xor should be commutative: h={h} g={g}")

    def test_lset_demorgan(self):
        self.check_lsets()
        u = [{k} for k in range(test_size)]

        def compl(g):
            return lset_minus(u, g)

        for _ in range(num_repetitions):
            g = distinct([range(k, -k, 2) for k in range(test_size)
                          if random.choice([True, False])])
            h = distinct([range(k, -k, 2) for k in range(test_size)
                          if random.choice([True, False])])
            self.assertTrue(lset_equal(compl(lset_union(g, h)),
                                       lset_intersection(compl(g), compl(h))),
                            f"De Morgan's theorem fails on g={g} h={h}")
            self.assertTrue(lset_equal(compl(lset_intersection(g, h)),
                                       lset_union(compl(g), compl(h))),
                            f"De Morgan's theorem fails on g={g} h={h}")

    def test_union_modified(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            data1 = random_list()
            data1_copy = [k for k in data1]
            data2 = random_list()
            data2_copy = [k for k in data2]
            lset_union(data1, data2)
            self.assertEqual(data1, data1_copy,
                             f"a call to lset_union modified its 1st input from {data1_copy} to {data1}")
            self.assertEqual(data2, data2_copy,
                             f"a call to lset_union modified its 2nd input from {data2_copy} to {data2}")

    def test_equal_modified(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            data1 = random_list()
            data1_copy = [k for k in data1]
            data2 = random_list()
            data2_copy = [k for k in data2]
            lset_equal(data1, data2)
            self.assertEqual(data1, data1_copy,
                             f"a call to lset_equal modified its 1st input from {data1_copy} to {data1}")
            self.assertEqual(data2, data2_copy,
                             f"a call to lset_equal modified its 2nd input from {data2_copy} to {data2}")

    def test_intersection_modified(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            data1 = random_list()
            data1_copy = [k for k in data1]
            data2 = random_list()
            data2_copy = [k for k in data2]
            lset_intersection(data1, data2)
            self.assertEqual(data1, data1_copy,
                             f"a call to lset_intersection modified its 1st input from {data1_copy} to {data1}")
            self.assertEqual(data2, data2_copy,
                             f"a call to lset_intersection modified its 2nd input from {data2_copy} to {data2}")

    def test_xor_modified(self):
        self.check_lsets()
        for _ in range(num_repetitions):
            data1 = random_list()
            data1_copy = [k for k in data1]
            data2 = random_list()
            data2_copy = [k for k in data2]
            lset_xor(data1, data2)
            self.assertEqual(data1, data1_copy,
                             f"a call to lset_xor modified its 1st input from {data1_copy} to {data1}")
            self.assertEqual(data2, data2_copy,
                             f"a call to lset_xor modified its 2nd input from {data2_copy} to {data2}")


if __name__ == '__main__':
    import unittest

    unittest.main()
