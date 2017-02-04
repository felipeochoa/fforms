"Unit testing of fforms/__init__.py"

import gc
import unittest
from unittest import mock
import doctest
import fforms
import fforms.cache


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(fforms))
    return tests


class TestMakeCachedBindDotter(unittest.TestCase):

    def test_sample_usage(self):
        data = fforms.cache.WeakableDict({
            'a.b': 1, 'a.c': 2, 'b.a': 3, 'b.b:0': 4, 'b.b:1': 5
        })
        ed = fforms.make_cached_expand_dots()
        res = ed(data)
        self.assertEqual(res,
                         {'a': {'b': 1, 'c': 2}, 'b': {'a': 3, 'b': [4, 5]}})
        self.assertIs(ed(data), res)
        self.assertEqual(len(ed._cache), 1)
        del data
        gc.collect()
        self.assertEqual(len(ed._cache), 0)


class TestBindDotted(unittest.TestCase):

    "Testing of the bind_dotted function."

    @mock.patch("fforms.expand_dots", autospec=True)
    def test_one_data(self, expand_dots):
        schema = mock.MagicMock(autospec=fforms.schema.Schema)
        data = {"key1": 'a', 'key2': ""}
        self.assertIs(fforms.bind_dotted(schema, data),
                      schema.bind.return_value)
        expand_dots.assert_called_once_with({'key1': 'a'})
        schema.bind.assert_called_once_with(fforms.BoundField,
                                            expand_dots.return_value)

    @mock.patch("fforms.expand_dots", autospec=True)
    def test_two_data(self, expand_dots):
        schema = mock.MagicMock(autospec=fforms.schema.Schema)
        data1 = {"key1": 'a', 'key2': ""}
        data2 = {"key3": None, "key4": 0, "key5": ""}
        self.assertIs(fforms.bind_dotted(schema, data1, data2),
                      schema.bind.return_value)
        expand_dots.assert_called_once_with({'key1': 'a',
                                             "key3": None, "key4": 0})
        schema.bind.assert_called_once_with(fforms.BoundField,
                                            expand_dots.return_value)
