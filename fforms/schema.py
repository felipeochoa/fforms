
from . import validators


class Schema:

    """
    Base class for all schema.

    Schema have the following attributes:

    * children: A tuple with any child nodes
    * validator: The validator responsible for converting and validating the
                 field's data.
    * name: The name of this field in its parent. self.parent[name] == self

    The preferred way to access children is using __getitem__(name):

      parent['field_name']

    """

    is_sequence = False

    def __init__(self, children, name=""):
        self.children = tuple(children)
        self.validator = validators.noop
        self.pre_processor = validators.noop
        self.name = name

    def __getitem__(self, child_name):
        raise NotImplementedError

    def validate(self, data):
        """
        Validate the given data.

        Validation is performed across all child nodes, depth first, and the
        validator attached to this node is only run after all the child
        validators.

        If the validator raises a ValidationError, this method returns that
        error, otherwise, it returns the output from the validator.

        """
        raise NotImplementedError

    def _run_validator(self, data):
        """
        Run the validator on the given data.

        If the validator raises a ValidationError, this method returns that
        error, otherwise, it returns the output from the validator.

        """
        try:
            return self.validator(data)
        except validators.ValidationError as err:
            return err

    def __iter__(self):
        return iter(self.children)

    def bind(self, factory, data):
        """Create a bound form from the given data."""
        return factory(self, data)


class MapSchema(Schema):

    """
    A key-value schema.

    __init__ params:

    * children: A mapping of child names to child schema
    * name: Same as for its parent class

    """

    def __init__(self, children, name=""):
        super().__init__(children.values(), name)
        self._child_by_name = children
        self.validator = validators.all_children

    def __getitem__(self, child_name):
        return self._child_by_name[child_name]

    def validate(self, data):
        if data is None:
            data = {}
        clean_data = {name: child.validate(data.get(name))
                      for name, child in self._child_by_name.items()}
        return self._run_validator(clean_data)


class SequenceSchema(Schema):

    """
    A single-type array.

    __init__ params:

    * child: The schema for the contained items
    * name: Same as for its parent class

    Defines one additional attribute:

    * child: The schema of its contained items. Equivalent to children[0]

    """

    is_sequence = True

    def __init__(self, child, name=""):
        super().__init__((child,), name)
        self.child = child
        self.validator = validators.all_children

    def validate(self, data):
        if data is None:
            data = []
        clean_data = [self.child.validate(elem) for elem in data]
        return self._run_validator(clean_data)


class LeafSchema(Schema):

    """
    A single datum.
    """

    def __init__(self, name=""):
        super().__init__((), name)

    def __getitem__(self, child_name):
        raise TypeError("LeafSchema do not have children")

    def validate(self, data):
        return self._run_validator(data)


def make_from_literal(literal, name=""):
    """
    Converts a literally specified schema into a Schema.

    This function traverses a set of nested dicitonaries and lists to create
    a schema tree made up of MapSchema, SequenceSchema, and LeafSchema
    objects. dicts are turned into MapSchema, lists are turned into
    SequenceSchema, and other values are turned into LeafSchema. For
    LeafSchema, the value given is assumed to be a validator, which is
    attached to the node.

    """
    if isinstance(literal, dict):
        children = {key: make_from_literal(value, name=key)
                    for key, value in literal.items()}
        schema = MapSchema(children, name)
    elif isinstance(literal, list):
        if len(literal) != 1:
            raise ValueError("Sequence Schema must have exactly one child")
        child = make_from_literal(literal[0], name=0)
        schema = SequenceSchema(child, name)
    else:  # Otherwise it should be a validator!
        schema = LeafSchema(name)
        schema.validator = literal
    return schema
