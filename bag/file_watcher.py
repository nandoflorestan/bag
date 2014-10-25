# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from time import sleep
import os
import sys


class PausingLooper(object):
    '''Has a loop() method that goes on calling an iterate() method,
    optionally pausing every so many seconds,
    until a "stop" instance variable is set to True.
    You should subclass this to create the necessary iterate() method.
    *pause_duration* can be a float (in seconds).
    '''
    stop = False
    pause_duration = None

    def loop(self):
        while not self.stop:
            self.iterate()
            if self.pause_duration:
                sleep(self.pause_duration)


class FileWatcher(PausingLooper):
    '''When you call the loop() method, watches a sequence of *files*
    for alterations and calls a function when any of them changes.
    That *callback* function gets, as an argument, the changed file path.
    '''

    def __init__(self, files, callback, seconds=1.3):
        self.callback = callback
        self.pause_duration = seconds
        self.mtimes = {}
        self.files = set(self.filter(files))

    def filter(self, files):
        '''Massages the sequence of file paths received in the constructor.
        (Useful for subclassing.) This implementation just discards
        empty strings and returns a generator.
        '''
        return (f for f in files if f)

    def iterate(self):
        '''Runs every so often to check if any files have changed.'''
        for path in self.files:
            # 1) Get and validate old modification time
            oldtime = self.mtimes.get(path, 0)  # First time it will be 0.
            if oldtime is None:
                continue  # File must have been deleted. Skip it.
            # 2) Obtain and validate current modification time
            try:
                mtime = os.stat(path).st_mtime
            except OSError:  # File's not there.
                mtime = None
            # 3) Compare the times; update if necessary
            if path not in self.mtimes:
                # This must be the first check() run, so
                # just add the path to the dictionary.
                self.mtimes[path] = mtime
            else:
                if mtime is None or mtime > oldtime:
                    self.mtimes[path] = mtime
                    self.callback(path)


class ModuleWatcher(FileWatcher):
    '''A file watcher that is good for watching Python programs.
    If your purpose is to reload Python modules when they change,
    it is probably better to use the FoundModuleWatcher class.
    '''

    def filter(self, files):
        '''Filters .pyc files, but keeps them as .py. Returns a generator.'''
        files = super(ModuleWatcher, self).filter(files)
        return (f[:-1] if f.endswith('.pyc') else f for f in files)


class LoadedModulesWatcher(ModuleWatcher):
    '''A file watcher that finds all loaded python modules.
    It automatically watches all python modules that were already loaded
    when this object was instantiated.
    You may use the static reload_module_by_path(path) method.
    '''

    @staticmethod
    def get_loaded_modules_paths():
        '''Returns a generator of the paths of currently loaded modules.'''
        # The builtin modules don't have a __file__ attribute.
        return (m.__file__ for m in sys.modules.values()
                if m and hasattr(m, '__file__'))

    @staticmethod
    def reload_module_by_path(path):
        '''Given a Python module path, tries to find the corresponding loaded
        Python module and reloads it. Returns True if successful, or
        False if not found.

        Beware: reloading a module does NOT update instances if they are names
        external to the module -- the old objects remain running the old code.
        This is just how reload() works.
        See http://docs.python.org/library/functions.html#reload
        '''
        for m in sys.modules.values():
            if not hasattr(m, '__file__'):
                continue
            p = m.__file__
            if p.endswith('.pyc'):
                p = p[:-1]
            if path == p:
                reload(m)
                return True
        return False

    def filter(self, files):
        '''Adds currently loaded modules to the *files* list.'''
        from itertools import chain
        return super(LoadedModulesWatcher, self) \
            .filter(chain(files, self.get_loaded_modules_paths()))
