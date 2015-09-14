"Unit testing the fforms.schema module."


import unittest
from unittest import mock

import fforms.schema
import fforms.validators

class TestSchema(unittest.TestCase):

    "Test the base schema class"

    def test_is_sequence(self):
        self.assertFalse(fforms.schema.Schema.is_sequence)

    def test_init(self):
        children = ['a', 'b', 'c']
        name = 'A strange name indeed'
        schema = fforms.schema.Schema(children, name)
        self.assertEqual(tuple(children), schema.children)
        self.assertIsInstance(schema.children, tuple)
        self.assertEqual(name, schema.name)
        self.assertIs(schema.validator, fforms.validators.noop)
        self.assertIs(schema.pre_processor, fforms.validators.noop)

    def test_iter(self):
        children = ["a", "b", "c"]
        schema = fforms.schema.Schema(children)
        self.assertEqual(list(schema), children)

    def test_bind(self):
        schema = fforms.schema.Schema(('a', 'b', 'c'))
        factory = mock.MagicMock()
        data = mock.Mock()
        schema.bind(factory, data)
        factory.assert_called_once_with(schema, data)

    def test_run_validator(self):
        schema = fforms.schema.Schema('abc')
        schema.validator = mock.MagicMock()
        data = mock.Mock()
        self.assertIs(schema._run_validator(data),
                      schema.validator.return_value)
        schema.validator.assert_called_once_with(data)

    def test_run_validator_error(self):
        schema = fforms.schema.Schema('abc')
        schema.validator = mock.MagicMock()
        schema.validator.side_effect = fforms.validators.ValidationError("a", {})
        data = mock.Mock()
        self.assertIsInstance(schema._run_validator(data),
                              fforms.validators.ValidationError)
        schema.validator.assert_called_once_with(data)

    def test_getitem(self):
        schema = fforms.schema.Schema(('a', 'b', 'c'))
        self.assertRaises(NotImplementedError, lambda: schema['a'])

    def test_validate(self):
        schema = fforms.schema.Schema(('a', 'b', 'c'))
        self.assertRaises(NotImplementedError, schema.validate, 1)
        self.assertRaises(NotImplementedError, schema.validate, None)


class TestMapSchema(unittest.TestCase):

    "Test the MapSchema class."

    def test_is_sequence(self):
        self.assertFalse(fforms.schema.MapSchema.is_sequence)

    def test__init(self):
        children = {'a': 1, 'b': 2, 'c': 3}
        schema = fforms.schema.MapSchema(children, "NaMe")
        self.assertEqual({1, 2, 3}, set(schema.children))
        self.assertIs(schema.validator, fforms.validators.all_children)
        self.assertIs(schema.pre_processor, fforms.validators.noop)
        self.assertEqual(schema.name, "NaMe")

    def test_immutable(self):
        children = {'a': 1, 'b': 2, 'c': 3}
        schema = fforms.schema.MapSchema(children)
        with self.assertRaises(TypeError):
            schema._child_by_name['a'] = 2
        children['a'] = 2
        self.assertNotEqual(schema['a'], 2)

    def test_getitem(self):
        children = {'a': 1, 'b': 2, 'c': 3}
        schema = fforms.schema.MapSchema(children, "NaMe")
        self.assertEqual(schema['a'], 1)
        self.assertEqual(schema['b'], 2)
        self.assertEqual(schema['c'], 3)

    @mock.patch.object(fforms.schema.Schema, "_run_validator", autospec=True)
    def test_validate_no_data(self, _run_validator):
        children = {}
        for key in 'abc':
            children[key] = mock.MagicMock(autospec=fforms.schema.Schema)
            children[key].validate.side_effect = lambda x: x
        schema = fforms.schema.MapSchema(children)
        self.assertIs(schema.validate(None),
                      _run_validator.return_value)
        _run_validator.assert_called_once_with(
            schema, {'a': None, 'b': None, 'c': None})
        for child in children.values():
            child.validate.assert_called_once_with(None)

    @mock.patch.object(fforms.schema.Schema, "_run_validator", autospec=True)
    def test_validate(self, _run_validator):
        children = {}
        for key in 'abc':
            children[key] = mock.MagicMock(autospec=fforms.schema.Schema)
            children[key].validate.side_effect = lambda x, key=key: x % key
        schema = fforms.schema.MapSchema(children)
        self.assertIs(schema.validate({'a': 'A:%s', 'b': 'B:%s', 'c': 'C:%s'}),
                      _run_validator.return_value)
        _run_validator.assert_called_once_with(
            schema, {'a': 'A:a', 'b': 'B:b', 'c': 'C:c'})
        for key, child in children.items():
            child.validate.assert_called_once_with(key.upper() + ":%s")


class TestSequenceSchema(unittest.TestCase):

    "Tets for SequenceSchema."

    def test_is_sequence(self):
        self.assertTrue(fforms.schema.SequenceSchema.is_sequence)

    def test_init(self):
        child = fforms.schema.Schema(())
        schema = fforms.schema.SequenceSchema(child, "name game")
        self.assertEqual(schema.children, (child,))
        self.assertIs(schema.child, child)
        self.assertIs(schema.validator, fforms.validators.all_children)
        self.assertEqual(schema.name, "name game")

    @mock.patch.object(fforms.schema.Schema, "_run_validator", autospec=True)
    def test_validate_no_data(self, _run_validator):
        child = mock.MagicMock(autospec=fforms.schema.Schema([]))
        schema = fforms.schema.SequenceSchema(child)
        self.assertIs(schema.validate(None), _run_validator.return_value)
        self.assertEqual(child.validate.call_count, 0)
        _run_validator.assert_called_once_with(schema, [])

    @mock.patch.object(fforms.schema.Schema, "_run_validator", autospec=True)
    def test_validate(self, _run_validator):
        child = mock.MagicMock(autospec=fforms.schema.Schema([]))
        child.validate.side_effect = lambda x: x ** 2
        schema = fforms.schema.SequenceSchema(child)
        self.assertIs(schema.validate([1, 2, 3]), _run_validator.return_value)
        self.assertEqual(child.validate.call_args_list,
                         [mock.call(1), mock.call(2), mock.call(3)])
        _run_validator.assert_called_once_with(schema, [1, 4, 9])


class TestLeafSchema(unittest.TestCase):

    "Testing for LeafSchema."

    def test_is_sequence(self):
        self.assertFalse(fforms.schema.LeafSchema.is_sequence)

    def test_init(self):
        schema = fforms.schema.LeafSchema("funkyName")
        self.assertEqual(schema.children, ())
        self.assertEqual(schema.name, "funkyName")

    def test_get_item(self):
        schema = fforms.schema.LeafSchema("funkyName")
        self.assertRaises(TypeError, lambda: schema[0])

    @mock.patch.object(fforms.schema.Schema, "_run_validator", autospec=True)
    def test_validate(self, _run_validator):
        data = mock.MagicMock()
        schema = fforms.schema.LeafSchema("funkyName")
        self.assertIs(schema.validate(data),
                      _run_validator.return_value)
        _run_validator.assert_called_once_with(schema, data)


class TestMakeFromLiteral(unittest.TestCase):

    "Testing for schema.make_from_literal"

    def test_dict(self):
        schema = fforms.schema.make_from_literal({
            'subnode1': 'val1',
            'subnode2': 'val2',
            'subnode3': 'val3',
        })
        self.assertIsInstance(schema, fforms.schema.MapSchema)
        self.assertEqual(schema.name, "")
        self.assertIs(schema.validator, fforms.validators.all_children)
        self.assertEqual(set(type(c) for c in schema),
                         {fforms.schema.LeafSchema,})
        self.assertEqual(len(schema.children), 3)
        self.assertEqual(schema['subnode1'].validator, 'val1')
        self.assertEqual(schema['subnode1'].name, 'subnode1')
        self.assertEqual(schema['subnode2'].validator, 'val2')
        self.assertEqual(schema['subnode2'].name, 'subnode2')
        self.assertEqual(schema['subnode3'].validator, 'val3')
        self.assertEqual(schema['subnode3'].name, 'subnode3')

    def test_list(self):
        schema = fforms.schema.make_from_literal(['child'])
        self.assertIsInstance(schema, fforms.schema.SequenceSchema)
        self.assertEqual(schema.name, "")
        self.assertIs(schema.validator, fforms.validators.all_children)
        self.assertIsInstance(schema.child, fforms.schema.LeafSchema)
        self.assertEqual(schema.child.validator, 'child')
        self.assertEqual(schema.child.name, 0)

    def test_list_multiple_children(self):
        noop = fforms.validators.noop
        self.assertRaises(ValueError,
                          fforms.schema.make_from_literal, [noop, noop])

    def test_leaf(self):
        val = fforms.validators.from_bool_func(lambda x: x == "test", "Error")
        schema = fforms.schema.make_from_literal(val)
        self.assertIsInstance(schema, fforms.schema.LeafSchema)
        self.assertEqual(schema.name, "")
        self.assertIs(schema.validator, val)

    def test_schema(self):
        for subschema in [fforms.schema.Schema(list('abc'), "testing"),
                          fforms.schema.MapSchema({'a': 1}, "map"),
                          fforms.schema.SequenceSchema(123456, "sequence"),
                          fforms.schema.LeafSchema("leaf")]:
            subschema.validator = lambda x: x
            schema = fforms.schema.make_from_literal(subschema)
            self.assertIs(schema.children, subschema.children)
            self.assertIs(schema.validator, subschema.validator)
            self.assertIsNot(schema.name, subschema.name)

    def test_integrated(self):
        f1v = fforms.validators.from_bool_func(lambda x: x == '1', "")
        zip_code_v = fforms.validators.chain(
            fforms.validators.from_regex("^[0-9]+$"),
            fforms.validators.limit_length(min=5, max=5))
        tel_v = fforms.validators.from_regex("^[0-9]+$")
        subschema = fforms.schema.LeafSchema("leaf")
        subschema.validator = lambda x: x
        schema = fforms.schema.make_from_literal({
            'field1': f1v,
            'emails': [fforms.validators.email],
            'address': {
                'street': fforms.validators.ensure_str,
                'zip_code': zip_code_v,
                'telephones': [tel_v],
            },
            'leaves': [subschema],
        })
        self.assertIsInstance(schema, fforms.schema.MapSchema)
        self.assertEqual(set(s.name for s in schema),
                         {'field1', 'emails', 'address', 'leaves'})

        self.assertIsInstance(schema['field1'], fforms.schema.LeafSchema)
        self.assertIs(schema['field1'].validator, f1v)

        self.assertIsInstance(schema['emails'], fforms.schema.SequenceSchema)
        self.assertIs(schema['emails'].validator, fforms.validators.all_children)
        self.assertIsInstance(schema['emails'].child, fforms.schema.LeafSchema)
        self.assertIs(schema['emails'].child.validator,
                      fforms.validators.email)

        self.assertIsInstance(schema['address'], fforms.schema.MapSchema)
        self.assertIs(schema['address'].validator, fforms.validators.all_children)
        self.assertIsInstance(schema['address']['street'],
                              fforms.schema.LeafSchema)
        self.assertIs(schema['address']['street'].validator,
                      fforms.validators.ensure_str)
        self.assertIsInstance(schema['address']['zip_code'],
                              fforms.schema.LeafSchema)
        self.assertIs(schema['address']['zip_code'].validator, zip_code_v)
        self.assertIsInstance(schema['address']['telephones'],
                              fforms.schema.SequenceSchema)
        self.assertIs(schema['address']['telephones'].validator,
                      fforms.validators.all_children)
        self.assertIsInstance(schema['address']['telephones'].child,
                              fforms.schema.LeafSchema)
        self.assertIs(schema['address']['telephones'].child.validator, tel_v)

        self.assertIsInstance(schema['leaves'], fforms.schema.SequenceSchema)
        self.assertIs(schema['leaves'].validator, fforms.validators.all_children)
        self.assertIsInstance(schema['leaves'].child, fforms.schema.LeafSchema)
        self.assertIs(schema['leaves'].child.validator, subschema.validator)
