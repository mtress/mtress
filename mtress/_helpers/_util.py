def update_in_dict(dictionary, keys, value, sep=".", ignore_missing=True):
    """
    Update value in nested dictionary.

    `update_in_dict(d, ['foo', 'bar', 'baz'], 3.1415)` or `update_in_dict(d, 'foo.bar.baz', 3.1415)`
    are equivalent to `d['foo']['bar']['baz'] = 3.1415`.

    :param dictionary: Dictionary which should be updated.
    :param keys: List of keys or dot separated string locating the value in question.
    :param value: New value.
    :param sep: Level separator, defaults to "."
    :param ignore_missing: Ignore missing keys.
    """
    if isinstance(keys, str):
        keys = keys.split(sep)

    *keys, key = keys
    for level in keys:
        if ignore_missing and level not in dictionary:
            dictionary[level] = {}
        dictionary = dictionary[level]

    dictionary[key] = value


def get_from_dict(dictionary, keys, sep=".", default=None):
    """Get value from nested dictionary."""
    if isinstance(keys, str):
        keys = keys.split(sep)

    for key in keys:
        if key not in dictionary and default is not None:
            return default

        dictionary = dictionary[key]

    return dictionary
