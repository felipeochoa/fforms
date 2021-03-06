
from .validators import ValidationError


class BoundField:

    """
    Fields are nodes in a tree (the form) which encompass validation.

    __init__ params:

    * `schema`: The unbound Field creating this BoundField
    * `full_name`: A dotted path of names from the root to here
    * `data`: A serliazed representation of the data to be validated against
              the schema. AKA "cstruct"


    BoundFields have the following attributes:

    * raw_data: The data fed to the field, if any (defaults to None). Any
                gaps in data are filled with `None`. This is the result of
                calling schema.pre_processor() using the passed in data.
    * clean_data: The data after the field and its children have validated
                  all of the inputs. If there are errors validating this
                  field, clean_data is None. (Note that the converse is not
                  True; clean_data may be None even though the field had no
                  errors)
    * name: The name of this field in its parent. parent[self.name] == self
    * error: An error message generated while validating this field's input.
             Errors specific to a child field are not included in the parent
             message.
    * full_name: A dotted/coloned path from the root node to self. Colons are
                 used when the schema is a sequence, and dots are used when
                 the schema is a map.

    """

    def __init__(self, schema, data=None, full_name="", name=None):
        self.schema = schema
        # name should only be overriden for children of fields bound to
        # SequenceSchema, where there isn't a 1-to-1 mapping of fields and
        # schema
        self.name = name if name is not None else schema.name
        self.full_name = full_name
        self.raw_data = schema.pre_processor(data)
        self._children = self._make_children()
        self.clean_data = None
        self.error = None

    def _make_children(self):
        "Returns a list or dict with child fields mirroring the schema."
        full_name = self.full_name
        data = self.raw_data
        if self.schema.is_sequence:
            full_name += ":"
            child = self.schema.child
            if data:
                return [self.__class__(child, elem, full_name + str(ix), ix)
                        for ix, elem in enumerate(data)]
            else:
                return [self.__class__(child, None, full_name + "0")]
        else:
            if full_name:
                full_name += "."
            return {
                node.name: self.__class__(
                    node,
                    None if data is None else data.get(node.name),
                    full_name + node.name)
                for node in self.schema
            }

    def __getitem__(self, name):
        return self._children[name]

    def is_valid(self):
        "Check the data and populate self.clean_data and self.errors."
        ret = self.schema.validate(self.raw_data)
        return self._propagate_validation(ret)

    def _propagate_validation(self, return_val):
        "Attach the proper errors and values to this and all child fields."
        if isinstance(return_val, ValidationError):
            self.error = return_val.bind(self)
            data = return_val.clean_data
            ret = False
        else:
            self.clean_data = return_val
            data = return_val
            ret = True
        if data is None:
            return ret
        for child in self:
            child._propagate_validation(data[child.name])
        return ret

    def __iter__(self):
        "Iterate over all the child fields."
        if self.schema.is_sequence:
            return iter(self._children)
        return iter(self._children.values())
