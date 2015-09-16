"Unit testing of fforms/__init__.py"

import unittest
from unittest import mock
import doctest
import fforms

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(fforms))
    return tests


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
