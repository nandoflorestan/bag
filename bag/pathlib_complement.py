# -*- coding: utf-8 -*-

"""This Python-3-only module complements pathlib by defining a subclass."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import pathlib  # We need Python 3.4 or later
import shutil
# https://docs.python.org/3/distutils/apiref.html#distutils.dir_util.copy_tree
from distutils.dir_util import copy_tree


# pathlib's class hierarchy is poorly designed, but here's how to subclass it.
# http://stackoverflow.com/questions/29850801/subclass-pathlib-path-fails
class Path(type(pathlib.Path())):
    """pathlib.Path subclass -- has more methods."""

    def ensure_directory(self, parents=True):
        if not self.is_dir():
            self.mkdir(parents=parents)

    def chgrp(self, gid):
        """Changes the group of this path."""
        uid = self.stat().st_uid
        os.chown(str(self), uid, gid)

    def walk(self, filter=None, this=False):
        for path in self.iterdir():
            if path.is_dir():
                yield from path.walk(filter=filter)
            if (filter(path) if filter else True):
                yield path
        if this and (filter(self) if filter else True):
            yield self

    '''def recursively(self, do, this=False):
        """Applies the ``do`` callback to all the contents of this directory.

            If ``this``, applies the callback to the directory itself, too.
            """
        for path in self.iterdir():
            if path.is_dir():
                path.recursively(do)
            do(path)
        if this:
            do(self)'''

    def remove(self):
        """Deletes self, irrespective of whether it's symlink, file or dir."""
        if self.is_symlink():  # is_symlink() must be evaluated before
            self.unlink()      # is_dir() because is_dir() is true for a
        elif self.is_dir():    # symbolic link pointing to a directory.
            shutil.rmtree(str(self))
        else:
            self.unlink()

    def empty(self):
        """Removes directory contents without removing the directory itself."""
        for path in self.iterdir():
            path.remove()

    def recursive_chgrp(self, group, this=False):
        """Changes the group of the directory contents.

            If ``this``, changes the directory itself, too.
            """
        for path in self.walk(this=this):
            path.chgrp(group)

    def recursive_chmod(self, file_perms, dir_perms=None):
        if not self.is_dir():
            self.chmod(oct2int(file_perms))
            return

        # This is a directory, so we have to chmod its contents too.
        dir_perms = dir_perms or default_directory_perms(file_perms)
        oct_dir_perms = oct2int(dir_perms)
        oct_file_perms = oct2int(file_perms)

        for path in self.walk(this=True):
            path.chmod(oct_dir_perms if path.is_dir() else oct_file_perms)

    def copy(self, dest):
        if self.is_file():
            shutil.copy(str(self), str(dest))
        elif self.is_dir():
            copy_tree(str(self), str(dest),
                      preserve_mode=0, preserve_times=0, verbose=0)
        else:
            raise RuntimeError(
                '"{}" is not a file or directory!'.format(self.src))

del pathlib


def oct2int(number):
    """Given a (string or int) representation of a file mode, such as "777"
        -- you have to realize that is actually an octal number --,
        returns the corresponding integer to be able to chmod.
        """
    return eval('0o' + str(number))


def corresponding_directory_perm(perm):
    """Given 4, returns 5. Given 6, returns 7."""
    perm = int(perm)
    return perm + 1 if perm % 2 == 0 and perm > 3 else perm


def default_directory_perms(file_perms):
    """Most people understand UNIX permissions for files, but not for
        directories -- if a file has 644 then usually its parent should be 754.
        We automate this here.
        """
    file_perms = str(file_perms)
    assert len(file_perms) == 3
    user_perm = corresponding_directory_perm(file_perms[0])
    group_perm = corresponding_directory_perm(file_perms[1])
    other_perm = corresponding_directory_perm(file_perms[2])
    return int('{}{}{}'.format(user_perm, group_perm, other_perm))
