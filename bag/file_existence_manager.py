# -*- coding: utf-8 -*-

'''Tools for finding duplicate files.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from hashlib import sha1
from nine import str


class GdbmStorageStrategy(object):
    '''Stores file hashes and file paths in a GNU DBM file.'''

    def __init__(self, path='./file_hashes.gdbm', mode='c', sync='s'):
        from dbm.gnu import open
        self.d = open(path, mode + sync)

    def close(self):
        self.d.sync()


class TransientStrategy(object):
    '''Stores file hashes and paths in memory only.'''

    def __init__(self):
        self.d = {}

    def close(self):
        pass


class FileExistenceManager(object):
    '''Manages a persistent dictionary of 'file IDs' (hashcodes for
        file contents). User code can:

        - ``add_or_replace_file()``
        - check whether a ``file_exists()``
        - combine the 2 previous operations with ``try_add_file()``

        When checking for existence, only file content is considered;
        file names are irrelevant.
        '''

    def __init__(self, store, consider_bytes=4096):
        '''If ``consider_bytes`` is a truish integer, configures the system
        to ignore the remainder of each file. ``store`` must be a storage
        strategy instance.
        '''
        self.db = store
        self.consider_bytes = consider_bytes

    def close(self):
        self.db.close()

    def _calculate_hash(self, byts):
        return sha1(byts).digest()  # hexdigest()

    def _get_file_hash(self, f):
        '''Gets a file object, reads a number of bytes from it
        and returns a hash.
        '''
        if self.consider_bytes:
            content = f.read(self.consider_bytes)
        else:
            content = f.read()  # the entire contents of the file
        return self._calculate_hash(content)

    def _hash_exists(self, byts):
        '''Looks up the file dictionary. Returns None if the provided hash
        does not yet exist, or the dictionary value if it does exist.
        '''
        return self.db.d.get(byts)

    def file_exists(self, f):
        '''Returns the stored value if the hash for file object ``f`` exists;
            otherwise, returns None.
            '''
        file_hash = self._get_file_hash(f)
        return self._hash_exists(file_hash)

    def _add_or_replace_hash(self, byts, value):
        self.db.d[byts] = value

    def add_or_replace_file(self, f, value):
        '''Puts the hash for file ``f`` (associated with ``value``) in the
        dictionary, irrespective of whether the hash already exists.

        ``value`` is tipically the path of ``f``.
        '''
        file_hash = self._get_file_hash(f)
        self._add_or_replace_hash(file_hash, value)

    def try_add_file(self, f, value):
        '''If the hash for file ``f`` already exists, just returns the
        associated value. If not, adds the hash with the provided ``value``.
        '''
        file_hash = self._get_file_hash(f)
        val = self._hash_exists(file_hash)
        if val:
            return val
        else:
            self._add_or_replace_hash(file_hash, value)


def find_dups(directory='.', files='*.jpg', callbacks=[]):
    '''Given a ``directory``, goes through all files that pass through the
        filter ``files``, and for each one that is a duplicate, calls a number
        of ``callbacks``. Returns a dictionary containing the duplicates found.

        Example usage::

            d = find_dups('some/directory',
                          callbacks=[print_dups, KeepLarger()])

        The signature for writing callbacks is (existing, dup, m), where
        ``existing`` and ``dup`` are paths and ``m`` is the
        FileExistenceManager instance.
        '''
    from pathlib import Path
    store = GdbmStorageStrategy()
    m = FileExistenceManager(store)
    dups = {}
    for p in Path(directory).glob(files):
        with open(str(p), 'rb') as stream:
            existing = m.try_add_file(stream, str(p))
        if existing:
            existing = existing.decode('utf-8')
            dups[str(p)] = existing
            for function in callbacks:
                function(Path(existing), p, m)
    m.close()
    return dups


def print_dups(existing, dup, m):
    '''A callback that just prints the duplicate pair.'''
    print('- Duplicate found:\n  {}\n  {}'.format(str(dup), str(existing)))


class KeepLarger(object):
    '''A callback that keeps the larger file. The smaller file is
    moved to a "dups" subdirectory.
    '''

    def __init__(self, dups_dir=None):
        self.dups_dir = dups_dir

    def __call__(self, existing, dup, m):
        if self.dups_dir is None:
            self.dups_dir = dup.parent / 'dups'
        if dup.stat().st_size > existing.stat().st_size:
            # Keep *dup* since it is the larger file
            existing.rename(self.dups_dir / dup.name)  # Move the old file
            with open(dup, 'rb') as stream:  # Update the database
                m.add_or_replace_file(stream, str(dup))
        else:
            # Move *dup* since it is the shorter file
            dup.rename(self.dups_dir / dup.name)

    @property
    def dups_dir(self):
        return self._dups_dir

    @dups_dir.setter
    def dups_dir(self, directory):
        self._dups_dir = directory
        if directory:
            try:
                directory.mkdir(parents=True)
            except OSError:
                pass
