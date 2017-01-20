
from .fields import BoundField
from .schema import make_from_literal

import re  # for expand_dots

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

    The actual indices of the items are only used for sorting, so gaps are
    allowed:

    >>> expand_dots({'parent:5': 'a', 'parent:7': 'b'})
    {'parent': ['a', 'b']}

    Nesting through lists also works:

    >>> (expand_dots({'parent:0.a': 'A', 'parent:0.b': 'B', 'parent:1': 1})
    ...   == {'parent': [{'a': 'A', 'b': 'B'}, 1]})
    True
    >>> expand_dots({'b:0:0': 'a'})
    {'b': [['a']]}
    >>> expand_dots({'b:0:0.a.0:0:0.c:0.d:0': 'a'})['b'][0][0]['a']['0'][0][0]['c'][0]['d'][0]
    'a'

    List indices must be integers, though:
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
    >>> expand_dots({})
    {}
    >>> from collections import OrderedDict
    >>> expand_dots(OrderedDict([('head.a', 1), ('head:0', 2)]))
    Traceback (most recent call last):
      ...
    ValueError: 'head' specified as both dict and list
    >>> expand_dots(OrderedDict([('head:0', 1), ('head.a', 2)]))
    Traceback (most recent call last):
      ...
    ValueError: 'head' specified as both dict and list

    """
    if not base_dict:
        return {}
    final_dict = {}
    args = [(base_dict, final_dict)]
    needs_conversion = []
    while args:
        base, into = args.pop()
        singles, dicts, lists = _expand_dots_1(base)
        into.update(singles)
        for key, val in dicts.items():
            into[key] = {}
            args.append((val, into[key]))
        for head, subdict in lists.items():
            into[head] = {}
            args.append((subdict, into[head]))
            needs_conversion.append((into, head))
    for parent, key in reversed(needs_conversion):
        parent[key] = [val for _, val in
                       sorted(parent[key].items(), key=lambda x: int(x[0]))]
    return final_dict


def _expand_dots_1(base_dict):
    "Expand a single layer of dots and colons."
    singles = {}
    dicts = {}
    lists = {}
    for key, val in base_dict.items():
        if '.' not in key and ':' not in key:
            if key in dicts or key in lists:
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
            dicts.setdefault(head, {})[tail] = val
        else:
            if head in dicts:
                raise ValueError("%r specified as both dict and list" % head)
            lists.setdefault(head, {})[tail] = val
    return singles, dicts, lists


def bind_dotted(schema, data, data2=None):
    "Bind the given data to the schema, returning a BoundField."
    if data2 is not None:
        data = data.copy()
        data.update(data2)
    data = expand_dots({key: val for key, val in data.items() if val != ""})
    return schema.bind(BoundField, data)


def _patch_mock_callable(): # pragma: nocover
    "Monkeypatch to allow automocking of classmethods and staticmethods."
    from unittest import mock
    if getattr(mock._callable, "fforms_patched", False):  #pylint: disable=W0212
        return
    def _patched_callable(obj):
        "Monkey patched version of mock._callable."
        # See https://code.google.com/p/mock/issues/detail?id=241 and
        # http://bugs.python.org/issue23078 for the relevant bugs this
        # monkeypatch fixes
        if isinstance(obj, type):
            return True
        if getattr(obj, '__call__', None) is not None:
            return True
        if (isinstance(obj, (staticmethod, classmethod)) and
                mock._callable(obj.__func__)):  #pylint: disable=W0212
            return True
        return False
    _patched_callable.fforms_patched = True
    mock._callable = _patched_callable  #pylint: disable=W0212
