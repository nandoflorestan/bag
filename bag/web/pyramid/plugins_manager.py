"""Manage plugins for your Python software."""

import os
from pyramid.decorator import reify


def find_subclasses(cls, path):
    """Find subclasses of `cls` in .py files located below `path`.

    (This does look in subdirectories).

    Usage::

        classes = find_subclasses(BasePlugin, "pluginsfolder")

    @param cls: the base class that all subclasses should inherit from
    @type cls: class
    @param path: the path to the top level directory to walk
    @type path: str
    @rtype: list
    @return: a list if classes that are subclasses of cls

    Stolen from
    http://www.luckydonkey.com/2008/01/02/python-style-plugins-made-easy/

    This could be improved by using cls.__subclasses__(), however this only
    returns the immediate subclasses.
    """
    def look_for_subclass(modulename):
        # log.debug("searching %s" % (modulename))
        module = __import__(modulename)
        # walk the dictionaries to get to the last one
        d = module.__dict__
        for m in modulename.split('.')[1:]:
            d = d[m].__dict__
        # Look through this dictionary for things that are subclasses of cls
        # but are not cls itself.
        for key, entry in d.items():
            if key == cls.__name__:
                continue
            try:
                if issubclass(entry, cls):
                    # log.debug("Found subclass: "+key)
                    subclasses.append(entry)
            except TypeError:
                # This happens when a non-type is passed in to issubclass. We
                # don't care as it can't be a subclass of cls if it isn't a
                # type.
                continue
    subclasses = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".py"):  # and not name.startswith("__"):
                path = os.path.join(root, name)
                modulename = path.rsplit('.', 1)[0].replace('/', '.')
                if modulename.endswith('.__init__'):
                    modulename = modulename[:-9]
                look_for_subclass(modulename)
    return set(subclasses)


class BasePlugin(object):
    """Marker class for plugins."""


class PluginsManager(object):

    def __init__(self, settings):
        self.settings = settings
        self.all = {}

    def find_directory_plugins(self, directory, plugin_class=BasePlugin):
        self.plugin_class = plugin_class
        for cls in find_subclasses(plugin_class, directory):
            self.add_plugin(callable=cls, module_name=cls.__name__)

    def find_egg_plugins(self, entry_point_groups):
        from pkg_resources import iter_entry_points
        for group in entry_point_groups:
            for ep in iter_entry_points(group=group, name=None):
                self.add_plugin(callable=ep.load(),
                                module_name=ep.module_name)

    def add_plugin(self, callable, module_name):
        """Instantiates a plugin and stores it if its name is new."""
        plugin = callable(self)  # get a plugin instance
        name = getattr(plugin, 'plugin_name', module_name)
        # print(name, plugin)
        self.all.setdefault(name, plugin)

    @reify
    def enabled(self):
        # settings = self.settings
        # for name, plugin in iteritems(self.config.registry.all_plugins):
            # if settings['plugins.' + name].lower() != 'disabled':
                # yield name, plugin
        return {name: plugin for name, plugin in self.all.items()
                if self.is_enabled(name)}

    def is_enabled(self, name):
        return self.settings.get('plugins.' + name, '').lower() != 'disabled'

    def call(self, method, args=[], kwargs={}, only_enabled_plugins=True):
        """Generic method that calls some method in the plugins."""
        nigulps = self.enabled if only_enabled_plugins else self.all
        for p in nigulps.values():
            if not hasattr(p, method):
                continue
            getattr(p, method)(*args, **kwargs)

    def link_static_dirs(self, destination_dir):
        from inspect import getsourcefile
        from .pyramid_starter import makedirs
        destination_dir = os.path.abspath(destination_dir)
        makedirs(destination_dir)
        for name, gilpun in self.all.items():
            source = getattr(gilpun, 'static_dir', None)
            if source is None:
                # Calculate the static dir if not provided
                package_dir = os.path.dirname(getsourcefile(gilpun.__class__))
                source = os.path.join(package_dir, 'static')
                if not os.path.isdir(source):
                    continue
            # print('symlinking', source)
            dest = os.path.join(destination_dir, name.replace(' ', '_'))
            if os.path.exists(dest):
                os.remove(dest)
            os.symlink(source, dest)
