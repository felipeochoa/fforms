
from .fields import BoundField
from .schema import make_from_literal


def expand_dots(base_dict):
    """
    Expands a serialized nested dictionary.

    The deserialization converts a dict like follows:

    >>> (expand_dots({'parent.child1': 'value1', 'parent.child2': 'value2'})
    ...   == {'parent': {'child1': 'value1', 'child2': 'value2'}})
    True

    It is an error to have a key with and without dots:

    >>> expand_dots({'parent': 'naked', 'parent.child': 'value'})
    Traceback (most recent call last):
      ...
    ValueError: 'parent' specified as both naked and parent key

    The error can occur deeper in the dictionary as well:

    >>> expand_dots({'parent.a.b': 'child', 'parent.a': 'child'})
    Traceback (most recent call last):
      ...
    ValueError: 'a' specified as both naked and parent key

    Lists are denoted using colons, as follows:

    >>> expand_dots({'parent:0': 'a', 'parent:1': 'b'})
    {'parent': ['a', 'b']}

    The actual indeces of the items are only used for sorting, so gaps are
    allowed:

    >>> expand_dots({'parent:5': 'a', 'parent:7': 'b'})
    {'parent': ['a', 'b']}

    Nesting through lists also works:

    >>> (expand_dots({'parent:0.a': 'A', 'parent:0.b': 'B', 'parent:1': 1})
    ...   == {'parent': [{'a': 'A', 'b': 'B'}, 1]})
    True

    List indeces must be integers, though:
    >>> expand_dots({'parent:a': 'A'})
    Traceback (most recent call last):
      ...
    ValueError: invalid literal for int() with base 10: 'a'

    >>> expand_dots({'parent': 'child'})
    {'parent': 'child'}
    >>> expand_dots({'parent.a': 'A', 'parent:1': 1})
    Traceback (most recent call last):
      ...
    ValueError: 'parent' specified as both dict and list
    >>> expand_dots({'parent.a': 'child'})
    {'parent': {'a': 'child'}}
    >>> expand_dots({'parent.a.b': 'child'})
    {'parent': {'a': {'b': 'child'}}}
    >>> (expand_dots({'parent.a.b': 'child', 'parent.a.c': 'child2'})
    ...   == {'parent': {'a': {'c': 'child2', 'b': 'child'}}})
    True
    >>> (expand_dots({'parent.a.b': 'child',
    ...              'parent.a.c': 'child2',
    ...              'parent.b': 12})
    ...   == {'parent': {'a': {'c': 'child2', 'b': 'child'}, 'b': 12}})
    True
    >>> (expand_dots({'a.b': 1, 'a.c': 2, 'b.a': 3, 'b.b': 4})
    ...  == {'a': {'c': 2, 'b': 1}, 'b': {'a': 3, 'b': 4}})
    True
    >>> expand_dots({'a:b': 1, 'a': 2})
    Traceback (most recent call last):
      ...
    ValueError: 'a' specified as both naked and parent key

    """
    import re
    if not base_dict:
        return {}
    new_dict = {}
    singles = {}
    lists = {}
    for key, val in base_dict.items():
        if '.' not in key and ':' not in key:
            if key in new_dict or key in lists:
                raise ValueError("%r specified as both naked and parent key" %
                                 key)
            singles[key] = val
            continue
        head, kind, tail = re.split('([:.])', key, 1)
        if head in singles:
            raise ValueError("%r specified as both naked and parent key" %
                             head)
        if kind == '.':
            if head in lists:
                raise ValueError("%r specified as both dict and list" % head)
            new_dict.setdefault(head, {})[tail] = val
        else:
            if head in new_dict:
                raise ValueError("%r specified as both dict and list" % head)
            lists.setdefault(head, {})[tail] = val

    final_dict = {key: expand_dots(val) for key, val in new_dict.items()}
    for head, subdict in lists.items():
        final_dict[head] = [val for _, val in
                            sorted(expand_dots(subdict).items(),
                                   key=lambda x: int(x[0]))]

    final_dict.update(singles)
    return final_dict


def bind_dotted(schema, data, data2=None):
    "Bind the given data to the schema, returning a BoundField."
    if data2 is not None:
        data = data.copy()
        data.update(data2)
    data = expand_dots({key: val for key, val in data.items() if val != ""})
    return schema.bind(BoundField, data)
