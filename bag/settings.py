"""Facilitate materialization of resources indicated in configuration."""

from importlib import import_module
from types import ModuleType


def resolve(resource_spec):
    """Return the variable referred to in the ``resource_spec`` string.

    Example resource_spec: ``"my.python.module:some_variable"``.
    """
    if isinstance(resource_spec, ModuleType   # arg is a python module
                  ) or callable(resource_spec):    # arg is a callable
        return resource_spec
    module, var = resource_spec.split(':')  # arg is assumed to be a string
    module = import_module(module)
    return getattr(module, var)


def resolve_path(resource_spec):
    """Return a pathlib.Path corresponding to the ``resource_spec`` string.

    Example argument: ``"my.python.module:some/subdirectory"``

    Similar: ``from pyramid.resource import abspath_from_asset_spec``
    """
    from pathlib import Path
    module, var = resource_spec.split(':')  # arg is assumed to be a string
    module = import_module(module)
    return Path(module.__path__[0], var)


class SettingsReader(object):
    """Convenient for reading configuration settings in an app."""

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
