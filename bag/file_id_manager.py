# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import struct
from hashlib import sha1
from nine import basestring, str

from warnings import warn
warn('Use bag.file_existence_manager instead of FileIdManager.',
     DeprecationWarning)


class FileIdManager(object):
    """Creates 'file IDs' (hashcodes for file contents), stores these
    IDs in a binary file, allows user code to add_file_id(), and
    can answer whether is_id_known (whether a certain file ID
    has already been recorded).

    Only file content and length are considered; file names are
    irrelevant.
    """
    recordlength = 24  # bytes

    def __init__(self, path):
        # Open the dictionary file for updates
        self.f = open(path, b"ab+")

    def close(self):
        self.f.close()

    def get_id_for(self, content, closefile=True):
        if not isinstance(content, basestring):
            fc = content
            content = fc.read()
            if closefile:
                fc.close()
        if len(content) == 0:
            return b"\0" * self.recordlength
        else:
            h = sha1(content).digest()          # 20 bytes for the hash
            s = struct.pack("i", len(content))  # 04 bytes for the length
            return s + h                        # 24 bytes total

    def is_id_known(self, file_id):
        self.validate_id(file_id)
        self.f.seek(0)
        s = self.f.read(self.recordlength)
        while s != "":
            if file_id == s:
                return True
            s = self.f.read(self.recordlength)
        return False

    def validate_id(self, file_id):
        length = len(file_id)
        if length != self.recordlength:
            raise RuntimeError("file_id size incorrect: " + str(length))

    def add_file_id(self, file_id):
        self.validate_id(file_id)
        self.f.seek(0, 2)  # move to end of file
        self.f.write(file_id)
        self.f.flush()

    def process(self, content, closefile=True):
        """Example implementation (see source code of this method)."""
        id = self.get_id_for(content, closefile)
        b = self.is_id_known(id)
        if not b:
            self.add_file_id(id)
        return b
