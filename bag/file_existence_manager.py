"""Tools for finding duplicate files."""

from hashlib import sha1
from bag.pathlib_complement import Path
from subprocess import check_call


class GdbmStorageStrategy:
    """Stores file hashes and file paths in a GNU DBM file."""

    def __init__(self, path='./file_hashes.gdbm', mode='c', sync='s'):
        from dbm.gnu import open
        self.d = open(path, mode + sync)

    def close(self):
        self.d.sync()


class TransientStrategy:
    """Stores file hashes and paths in memory only."""

    def __init__(self):
        self.d = {}

    def close(self):
        pass


def file_as_block_iter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


def hash_bytestr_iter(bytes_iter, hasher, as_hex_str=False):
    for block in bytes_iter:
        hasher.update(block)
    return hasher.hexdigest() if as_hex_str else hasher.digest()


class FileExistenceManager:
    """Manages existing files through their hashcodes.

    User code can:

    - ``add_or_replace_file()``
    - check whether a ``file_exists()``
    - combine the 2 previous operations with ``try_add_file()``

    When checking for existence, only file content is considered;
    file names are irrelevant.
    """

    def __init__(self, store, consider_bytes=0):
        """Constructor.

        If ``consider_bytes`` is a truish integer (e. g. 4096),
        only that many bytes will be read and the remainder of each file
        will be ignored. ``store`` must be a storage strategy instance.
        """
        self.db = store
        self.consider_bytes = consider_bytes

    def close(self):
        """Release resources, especially the database file."""
        self.db.close()

    def _calculate_hash(self, byts):
        return sha1(byts).digest()  # hexdigest()

    def _get_file_hash(self, f):
        """Read a number of bytes from file ``f`` and return a hash."""
        if self.consider_bytes:
            content = f.read(self.consider_bytes)
            return self._calculate_hash(content)
        else:
            # Instead of calling f.read(), conserve memory:
            return hash_bytestr_iter(file_as_block_iter(f), sha1())

    def _hash_exists(self, byts):
        """Look up the passed hash. Return the stored value or None.

        Return None if the provided hash does not yet exist,
        or the dictionary value if it does exist.
        """
        return self.db.d.get(byts)

    def file_exists(self, f):
        """Return the stored value if the hash for file object ``f`` exists.

        Otherwise return None.
        """
        file_hash = self._get_file_hash(f)
        return self._hash_exists(file_hash)

    def _add_or_replace_hash(self, byts, value):
        self.db.d[byts] = value

    def add_or_replace_file(self, f, value):
        """Whether the hash already exists does not matter.

        Put the hash for file ``f`` in the store, associated with ``value``,
        which is tipically the path of ``f``.
        """
        file_hash = self._get_file_hash(f)
        self._add_or_replace_hash(file_hash, value)

    def try_add_file(self, f, value):
        """Return existing value or add hash with passed ``value``.

        If the hash for file ``f`` already exists, just return the
        associated value. If not, add the hash with the provided ``value``.
        """
        file_hash = self._get_file_hash(f)
        val = self._hash_exists(file_hash)
        if val:
            return val
        else:
            self._add_or_replace_hash(file_hash, value)


def print_dup(original, duplicate, m):
    """A callback that just prints the duplicate pair."""
    print('\n- ORIG:  {}\n  DUPL:  {}'.format(str(original), str(duplicate)))


def trash_dup(original, duplicate, m):
    """Callback that puts the duplicate file in the trash.

    You need to install the Ubuntu package ``trash-cli``.
    """
    check_call(["trash", str(duplicate)])


def trash_dup_unless_empty(original, duplicate, m):
    """Callback that puts the duplicate file in the trash, unless it is empty.

    (Sometimes I use zero-length files to present information in their names.)
    """
    if duplicate.stat().st_size:
        trash_dup(original, duplicate, m)


def print_dup_unless_empty(original, duplicate, m):
    """Print the duplicate pair unless the files are empty."""
    if duplicate.stat().st_size:
        print_dup(original, duplicate, m)


def populate_db(path='./file_hashes.gdbm', directory=".",
                callbacks=[print_dup], filter=lambda path: True):
    """Create/update database at ``path`` by hashing files in ``directory``."""
    store = GdbmStorageStrategy(path=path)
    m = FileExistenceManager(store)
    for p in Path(directory).walk():
        if not p.is_file():
            continue
        with open(str(p), 'rb') as stream:
            original = m.try_add_file(stream, str(p))
        if original:
            original = original.decode('utf-8')
            for function in callbacks:
                function(Path(original), p, m)
    m.close()


def check_dups(path='./file_hashes.gdbm', directory=".",
               callbacks=[print_dup], filter=lambda path: True):
    """Check files in ``directory`` against the database ``path``.

    Example usage::

        check_dups(directory='some/directory',
                   callbacks=[print_dup, trash_dup])
    """
    store = GdbmStorageStrategy(path=path)
    m = FileExistenceManager(store)
    for p in Path(directory).walk():
        if not p.is_file():
            continue
        with open(str(p), 'rb') as stream:
            original = m.file_exists(stream)
        if original:
            original = original.decode('utf-8')
            for function in callbacks:
                function(Path(original), p, m)
    m.close()


def find_dups(path='./file_hashes.gdbm', directory='.',
              callbacks=[print_dup], filter=lambda path: True):
    """Like ``check_dups()``, but also updates the database as it goes.

    Given a ``directory``, goes through all files that pass through the
    predicate ``filter``, and for each one that is a duplicate, calls the
    of ``callbacks``. Returns a dictionary containing the duplicates found.

    Example usage::

        d = find_dups(directory='some/directory',
                      callbacks=[print_dup, KeepLarger()])

    The signature for writing callbacks is ``(original, dup, m)``, where
    ``original`` and ``dup`` are Path instances and ``m`` is the
    FileExistenceManager instance.
    """
    store = GdbmStorageStrategy(path=path)
    m = FileExistenceManager(store)
    dups = {}
    for p in Path(directory).walk():
        if not p.is_file():
            continue
        with open(str(p), 'rb') as stream:
            original = m.try_add_file(stream, str(p))
        if original:
            original = original.decode('utf-8')
            dups[str(p)] = original
            for function in callbacks:
                function(Path(original), p, m)
    m.close()
    return dups


class KeepLarger:
    """Move the smaller file to a "dups" subdirectory.

    A callback that keeps the larger file. The smaller file is
    moved to a "dups" subdirectory.
    """

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
