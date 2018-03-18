"""Nice exception classes."""

from typing import Any


class ArgumentError(ValueError):
    """Use this exception to complain that ``arg`` doesn't accept ``val``."""

    def __init__(self, arg: str, val: Any) -> None:
        """Instantiate error from the parameter name and the wrong value.

        More useful than ValueError, whose argument is an error string.
        """
        self.arg = arg
        self.val = val
        val = str(val)
        if len(val) > 43:
            val = val[:40] + '...'
        super(ArgumentError, self).__init__(
            'Argument "{0}" does not accept value "{1}"'.format(arg, val))
