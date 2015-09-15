"Unit testing of fforms.fields."

import unittest
from unittest import mock

import fforms.fields, fforms.schema
from fforms import _patch_mock_callable
_patch_mock_callable()



class TestBoundFieldCreation(unittest.TestCase):

    "Test the creation of a BoundField class."

    @mock.patch.object(fforms.fields.BoundField, "_make_children", autospec=True)
    def test_init(self, _make_children):
        schema = mock.MagicMock(autospec=fforms.schema.Schema(()))
        field = fforms.fields.BoundField(schema)
        _make_children.assert_called_once_with(field)
        self.assertIs(field._children, _make_children.return_value)
        self.assertIs(field.schema, schema)
        self.assertEqual(field.full_name, "")
        self.assertIs(field._name, schema.name)
        self.assertIs(field.clean_data, None)
        self.assertIs(field.raw_data, schema.pre_processor.return_value)
        self.assertIs(field.error, None)

    @mock.patch.object(fforms.fields.BoundField, "_make_children", autospec=True)
    def test_init_with_data(self, _make_children):
        schema = mock.MagicMock(autospec=fforms.schema.Schema(()))
        data = object()
        field = fforms.fields.BoundField(schema, data, "full_name", 5)
        _make_children.assert_called_once_with(field)
        self.assertIs(field._children, _make_children.return_value)
        self.assertIs(field.schema, schema)
        self.assertEqual(field.full_name, "full_name")
        self.assertIs(field._name, 5)
        self.assertIs(field.clean_data, None)
        self.assertIs(field.raw_data, schema.pre_processor.return_value)
        self.assertIs(field.error, None)

    def test_make_children_sequence_no_data(self):
        schema = fforms.schema.make_from_literal([fforms.validators.noop])
        field = fforms.fields.BoundField(schema)
        self.assertEqual(len(list(field)), 1)
        self.assertIs(field[0].schema, schema.child)
        self.assertEqual(field[0].full_name, ":0")
        self.assertEqual(field[0]._name, 0)
        self.assertEqual(field[0].clean_data, None)
        self.assertEqual(field[0].raw_data, None)
        self.assertEqual(field[0].error, None)

    def test_make_children_sequence_with_data(self):
        schema = fforms.schema.make_from_literal([fforms.validators.noop])
        field = fforms.fields.BoundField(schema, [0, 1, 2, 3])
        self.assertEqual(len(list(field)), 4)
        for i, subfield in enumerate(field):
                self.assertIs(subfield.schema, schema.child)
                self.assertEqual(subfield.full_name, ":%d" % i)
                self.assertEqual(subfield._name, i)
                self.assertEqual(subfield.clean_data, None)
                self.assertEqual(subfield.raw_data, i)
                self.assertEqual(subfield.error, None)

    def test_make_children_mapschema_no_data(self):
        schema = fforms.schema.make_from_literal({
            'key1': fforms.validators.noop,
            'key2': fforms.validators.noop,
        })
        field = fforms.fields.BoundField(schema)
        self.assertEqual(len(list(field)), 2)
        for key in ('key1', 'key2'):
                self.assertIs(field[key].schema, schema[key])
                self.assertEqual(field[key].full_name, "%s" % key)
                self.assertEqual(field[key]._name, key)
                self.assertEqual(field[key].clean_data, None)
                self.assertEqual(field[key].raw_data, None)
                self.assertEqual(field[key].error, None)

    def test_make_children_mapschema_with_data(self):
        schema = fforms.schema.make_from_literal({
            'key1': fforms.validators.noop,
            'key2': fforms.validators.noop,
        })
        field = fforms.fields.BoundField(schema, dict(key1=1))
        self.assertEqual(len(list(field)), 2)
        key = 'key1'
        self.assertIs(field[key].schema, schema[key])
        self.assertEqual(field[key].full_name, "%s" % key)
        self.assertEqual(field[key]._name, key)
        self.assertEqual(field[key].clean_data, None)
        self.assertEqual(field[key].raw_data, 1)
        self.assertEqual(field[key].error, None)
        key = 'key2'
        self.assertIs(field[key].schema, schema[key])
        self.assertEqual(field[key].full_name, "%s" % key)
        self.assertEqual(field[key]._name, key)
        self.assertEqual(field[key].clean_data, None)
        self.assertEqual(field[key].raw_data, None)
        self.assertEqual(field[key].error, None)

    def test_make_children_leaf_no_data(self):
        schema = fforms.schema.LeafSchema()
        field = fforms.fields.BoundField(schema)
        self.assertEqual(len(list(field)), 0)

    def test_make_children_leaf_with_data(self):
        schema = fforms.schema.LeafSchema()
        field = fforms.fields.BoundField(schema, ['a', 'b', 'c'])
        self.assertEqual(len(list(field)), 0)
        self.assertEqual(field.raw_data, ['a', 'b', 'c'])


class TestBoundFieldBehavior(unittest.TestCase):

    "Test non-initializing methods of BoundFields."

    def setUp(cls):
        cls.map_schema = fforms.schema.make_from_literal({
            'key1': fforms.validators.noop,
            'key2': fforms.validators.noop,
        })
        cls.map_field = fforms.BoundField(cls.map_schema)
        cls.map_field_with_data = fforms.BoundField(cls.map_schema,
                                                    {'key1': 1})
        cls.seq_schema = fforms.schema.make_from_literal(
            [fforms.validators.noop])
        cls.seq_field = fforms.BoundField(cls.seq_schema)
        cls.seq_field_with_data = fforms.BoundField(cls.seq_schema,
                                                    [0, 1, 2])
        cls.leaf_schema = fforms.schema.LeafSchema()
        cls.leaf_field = fforms.BoundField(cls.leaf_schema)
        cls.leaf_field_with_data = fforms.BoundField(cls.leaf_schema, "leaf")

    def test_getitem(self):
        self.assertIs(self.map_field['key1'].schema,
                      self.map_schema['key1'])
        self.assertIs(self.map_field['key2'].schema,
                      self.map_schema['key2'])
        self.assertIs(self.map_field_with_data['key1'].schema,
                      self.map_schema['key1'])
        self.assertIs(self.map_field_with_data['key2'].schema,
                      self.map_schema['key2'])
        self.assertIs(self.seq_field[0].schema, self.seq_schema.child)
        for i in range(3):
            self.assertIs(self.seq_field_with_data[i].schema,
                          self.seq_schema.child)

    @mock.patch("fforms.fields.BoundField._propagate_validation", autospec=True)
    def test_is_valid(self, _propagate_validation):
        cases = [
            (self.map_field, {'key1': None, 'key2': None}),
            (self.map_field_with_data, {'key1': 1, 'key2': None}),
            (self.seq_field, []),
            (self.seq_field_with_data, [0, 1, 2]),
            (self.leaf_field, None),
            (self.leaf_field_with_data, "leaf"),
        ]
        for field, exp in cases:
            self.assertIs(field.is_valid(),
                          _propagate_validation.return_value)
            self.assertEqual(_propagate_validation.call_count, 1)
            self.assertEqual(_propagate_validation.call_args[0], (field, exp))
            _propagate_validation.reset_mock()

    def test_propagate_error(self):
        field = mock.MagicMock(autospec=fforms.fields.BoundField,
                               clean_data=None)
        child1 = mock.MagicMock(autospec=fforms.fields.BoundField,
                                _name="key1",
                                clean_data=None)
        child2 = mock.MagicMock(autospec=fforms.fields.BoundField,
                                _name="key2",
                                clean_data=None)
        field.__iter__.return_value = (child1, child2)

        data = {'key1': "data1",
                'key2': fforms.validators.ValidationError("Missing", None)}
        ret_val = fforms.validators.ValidationError("field: {field!r}", data)

        self.assertFalse(
            fforms.fields.BoundField._propagate_validation(field, ret_val))
        self.assertEqual(field.error, "field: %r" % field)
        self.assertIsNone(field.clean_data)

        child1._propagate_validation.assert_called_once_with(data['key1'])
        child2._propagate_validation.assert_called_once_with(data['key2'])

    def test_propagate_data(self):
        field = mock.MagicMock(autospec=fforms.fields.BoundField,
                               error=None,
                               clean_data=None)
        child1 = mock.MagicMock(autospec=fforms.fields.BoundField,
                                _name=0,
                                clean_data=None)
        child2 = mock.MagicMock(autospec=fforms.fields.BoundField,
                                _name=1,
                                clean_data=None)
        child1._propagate_validation.side_effect = lambda x: x
        child2._propagate_validation.side_effect = lambda x: x
        field.__iter__.return_value = (child1, child2)

        data = ["data1", fforms.validators.ValidationError("Missing", None)]
        self.assertTrue(
            fforms.fields.BoundField._propagate_validation(field, data))
        self.assertEqual(field.clean_data, data)
        self.assertIsNone(field.error)

        child1._propagate_validation.assert_called_once_with(data[0])
        child2._propagate_validation.assert_called_once_with(data[1])

    def test_iter(self):
        fields = [
            (self.map_field, 2),
            (self.map_field_with_data, 2),
            (self.seq_field, 1),
            (self.seq_field_with_data, 3),
            (self.leaf_field, 0),
            (self.leaf_field_with_data, 0),
        ]
        for field, count in fields:
            self.assertEqual(set(subfield.schema for subfield in field),
                             set(subschema for subschema in field.schema))
            self.assertEqual(len(set(field)), count)
