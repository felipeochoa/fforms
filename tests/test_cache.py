import gc
import unittest
import weakref
from fforms import cache


class TestWeakableDict(unittest.TestCase):

    def test_make_weak_ref(self):
        d = cache.WeakableDict()
        called = False

        def on_destroy(_):
            nonlocal called
            called = True

        ref = weakref.ref(d, on_destroy)
        self.assertIs(ref(), d)
        del d
        gc.collect()
        self.assertTrue(called)


class TestIdDict(unittest.TestCase):

    def test_basic_usage(self):
        key = cache.WeakableDict()
        val = object()
        d = cache.WeakKeyNonHashingDict()
        d[key] = val
        self.assertIs(d[key], val)
        del d[key]
        with self.assertRaises(KeyError):
            d[key]

    def test_weakness(self):
        d = cache.WeakKeyNonHashingDict()
        val = object()
        key = cache.WeakableDict()
        d[key] = val
        self.assertEqual(len(d), 1)
        del key
        gc.collect()
        self.assertEqual(len(d), 0)

    def test_len(self):
        d = cache.WeakKeyNonHashingDict()
        self.assertEqual(len(d), 0)
        v1 = cache.WeakableDict()
        d[v1] = object()
        self.assertEqual(len(d), 1)
        v2 = cache.WeakableDict()
        d[v2] = object()
        self.assertEqual(len(d), 2)
        del d[v1]
        self.assertEqual(len(d), 1)
        del v2
        gc.collect()
        self.assertEqual(len(d), 0)


class TestWeakCache(unittest.TestCase):

    def test_cache_miss(self):
        calls = 0

        @cache.weak_cache
        def func(_):
            nonlocal calls
            calls += 1
            return calls

        self.assertEqual(func(cache.WeakableDict()), 1)
        self.assertEqual(func(cache.WeakableDict()), 2)

    def test_cache_hit(self):
        calls = 0

        @cache.weak_cache
        def func(_):
            nonlocal calls
            calls += 1
            return calls

        arg = cache.WeakableDict()
        self.assertEqual(func(arg), 1)
        self.assertEqual(func(arg), 1)

    def test_cache_clear(self):
        calls = 0

        @cache.weak_cache
        def func(_):
            nonlocal calls
            calls += 1
            return calls

        arg = cache.WeakableDict()
        self.assertEqual(func(arg), 1)
        self.assertEqual(func(arg), 1)
        self.assertEqual(len(func._cache), 1)
        del arg
        gc.collect()
        self.assertEqual(len(func._cache), 0)
