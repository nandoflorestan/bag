"""bag library."""

from typing import Callable, Dict, Iterable


def first(iterable: Iterable):
    """Return the first object in ``iterable``, or None if empty."""
    for o in iterable:
        return o


def dict_subset(adict: Dict, predicate: Callable):
    """Return a dict that is a subset of ``adict`` using a filter function.

    The signature of the filter is: ``predicate(key, val) -> bool``
    """
    return {k: v for k, v in adict.items() if predicate(k, v)}
