# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import stat
import urllib2
from io import StringIO


def isdir(s):
    """Return true if the pathname refers to an existing directory."""
    try:
        st = os.stat(s)
    except os.error:
        return False
    return stat.S_ISDIR(st.st_mode)


def mkdir(s):
    '''Make directories (if they don't exist already).'''
    if not isdir(s):
        os.makedirs(s)


class BytesBox(object):
    def __init__(self, path=None, url=None, byts=None):
        self.url = url
        self.path = path
        self._byts = byts

    @property
    def byts(self):
        '''Returns the memoized bytes, or reads from path, or reads URL.
        '''
        if self._byts:
            return self._byts  # memoized
        if self.path:
            with open(self.path, 'rb') as f:
                self._byts = f.read()
            return self._byts
        if self.url:
            stream = urllib2.urlopen(self.url)
            self._byts = stream.read()
            return self._byts

    @byts.setter
    def byts(self, val):
        self._byts = val

    def write_file(self, path=None, byts=None):
        '''Writes *byts* to *path* and returns a corresponding BytesBox,
        which might simply be, self.
        '''
        mkdir(os.path.dirname(path))
        with open(path or self.path, 'wb') as f:
            f.write(byts or self.byts)
        if path or byts:
            return BytesBox(path=path or self.path,
                            byts=byts or self._byts)
        else:
            return self


import Image
import ImageFile
# To prevent this exception:
# IOError: encoder error -2 when writing image file
ImageFile.MAXBLOCK = 256 * 1024
del ImageFile


class ImageBox(BytesBox):
    def __init__(self, image=None, stream=None, **k):
        super(ImageBox, self).__init__(**k)
        if image:
            self._stream = None
            self._image = image
        else:
            self._stream = stream or StringIO(self._byts)
            self._image = Image.open(self._stream)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, val):
        self._image = val

    @property
    def byts(self):
        b = super(ImageBox, self).byts
        if b:
            return b
        else:
            self._stream.seek(0)
            self._byts = self._stream.read()
            return self._byts

    def copy_or_write_jpeg(self, path=None, quality=90):
        '''Copies image if it is a jpeg, else converts and saves.
        Returns a new ImageBox.
        '''
        if self.image.format == 'JPEG' and self.byts:
            other = ImageBox(image=self.image, path=path or self.path)
            other.byts = self.byts
            other.write_file()
            return other
        else:
            return self.write_jpeg(path=path, quality=quality)

    def write_jpeg(self, path=None, quality=90):
        other = ImageBox(image=self.image, path=path or self.path)
        if self.image.mode != 'RGB':
            other.image = self.image.convert('RGB')
        mkdir(os.path.dirname(path))
        other.image.save(other.path, format='JPEG',
                         quality=quality, optimize=1)
        return other

    def resize_if_larger_than(self, max_size):
        """Taking a tuple (maxWidth, maxHeight),
        if necessary, resizes the image and returns a new ImageBox.
        Returns self if resizing is not necessary.
        """
        max_size = (int(max_size[0]), int(max_size[1]))
        if self.image.size[0] <= max_size[0] and \
                self.image.size[1] <= max_size[1]:
            return self
        ratioOriginal = float(self.image.size[0]) / self.image.size[1]
        ratioMax = float(max_size[0]) / max_size[1]
        if ratioOriginal > ratioMax:  # if width is the determinant
            image = self.image.resize(
                (max_size[0],
                 self.image.size[1] * max_size[0] / self.image.size[0]),
                Image.ANTIALIAS)
        else:                        # if height is the determinant
            image = self.image.resize(
                (self.image.size[0] * max_size[1] / self.image.size[1],
                 max_size[1]), Image.ANTIALIAS)
        return ImageBox(image=image)
