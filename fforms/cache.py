from functools import wraps
import weakref


class WeakableDict(dict):
    "dict subclass that can accept weakrefs."
    __slots__ = ('__weakref__')


class WeakKeyNonHashingDict:

    """
    A mapping that uses object IDs instead of hashes to store values.

    Similar to `weakref.WeakKeyDictionary`, this mapping does not keep
    its keys alive. Values are automatically removed from this mapping
    when their key is garbage collected. However, unlike
    `weakref.WeakKeyDictionary`, this mapping allows storing
    non-hashable types (such as dict) with limited overhead (i.e.,
    without converting to a tuple).

    """

    __slots__ = ['_data']

    def __init__(self):
        self._data = {}

    def __getitem__(self, obj):
        return self._data[id(obj)][1]

    def __setitem__(self, obj, value):
        key = id(obj)
        try:
            ref = self._data[key][0]
        except KeyError:
            def on_destroy(_):
                del self._data[key]
            ref = weakref.ref(obj, on_destroy)
        self._data[key] = ref, value

    def __delitem__(self, obj):
        del self._data[id(obj)]

    def __len__(self):
        return len(self._data)


def weak_cache(func):
    "Wrap the given single-argument function using an WeakKeyNonHashingDict."
    cache = WeakKeyNonHashingDict()

    @wraps(func)
    def wrapper(data):
        try:
            return cache[data]
        except KeyError:
            cache[data] = result = func(data)
            return result
    wrapper._cache = cache
    return wrapper
