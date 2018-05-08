"""Facilitate materialization of resources indicated in configuration."""

from importlib import import_module
from types import ModuleType


def read_ini_files(*config_files, encoding='utf-8'):
    """Get a settings object (dict-like) by reading some ``config_files``."""
    from configparser import ConfigParser
    settings = ConfigParser()
    settings.read(config_files, encoding=encoding)
    return settings


def resolve(resource_spec):
    """Return the variable referred to in the ``resource_spec`` string.

    Example resource_spec: ``"my.python.module:some_callable"``.
    """
    if isinstance(resource_spec, ModuleType   # arg is a python module
                  ) or callable(resource_spec):    # arg is a callable
        return resource_spec
    parts = resource_spec.split(':')  # arg is assumed to be a string
    if len(parts) == 1:
        return import_module(parts[0])
    elif len(parts) == 2:
        module = import_module(parts[0])
        return getattr(module, parts[1])
    else:
        raise ValueError(
            '":" may appear only once in a resource spec, but I received "{}"'
            .format(resource_spec))


def resolve_path(resource_spec):
    """Return a pathlib.Path corresponding to the ``resource_spec`` string.

    Example argument: ``"my.python.module:some/subdirectory"``

    Similar: ``from pyramid.resource import abspath_from_asset_spec``
    """
    from pathlib import Path
    module, var = resource_spec.split(':')  # arg is assumed to be a string
    module = import_module(module)
    return Path(module.__path__[0], var)


def asbool(s):
    """Convert the argument to a boolean.

    Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is a truthy string. If ``s`` is already one of the
    boolean values ``True`` or ``False``, return it.
    """
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    val = _boolean_states.get(str(s).strip().lower())
    if val is None:
        raise ValueError('Not a boolean: "%s"' % s)
    return val


_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


class SettingsReader(object):
    """Convenient for reading configuration settings in an app.

    However, with Python 3.6+ I have used the **pydantic** library
    with better results.
    """

    def __init__(self, adict):
        """``adict`` should be a settings dictionary."""
        self.settings = adict

    def read(self, key, default=None, required=False):
        """Return setting value, or ``default`` if missing.

        Raise RuntimeError if ``required`` is true and value is empty.
        """
        value = self.settings.get(key, default)
        if required and value in (None, ''):
            raise RuntimeError(
                'Settings are missing a "{}" entry.'.format(key))
        return value

    def bool(self, key, default=None, required=False):
        """Return a boolean setting value."""
        value = self.read(key, default=default, required=required)
        return asbool(value)

    def resolve(self, key, default=None, required=False):
        """Return the variable or module indicated in the setting value.

        Therefore the setting value should be a resource specification
        such as ``some.module:SomeClass``.
        """
        resource_spec = self.read(
            key, default=default, required=required)
        return None if resource_spec is None else resolve(resource_spec)

    def resolve_path(self, key, default=None, required=False):
        """Return a pathlib.Path corresponding to the setting value.

        Example argument: ``"my.python.module:some/subdirectory"``
        """
        resource_spec = self.read(
            key, default=default, required=required)
        return None if resource_spec is None else resolve_path(resource_spec)
