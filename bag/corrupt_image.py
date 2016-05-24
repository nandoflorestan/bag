# -*- coding: utf-8 -*-

"""Read image files and do something if they are corrupt."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


def is_valid_image(pth):
    from PIL import Image  # https://pypi.python.org/pypi/Pillow
    try:
        img = Image.open(str(pth))
    except IOError:
        return False
    try:
        img.load()
    except IOError:
        return False
    finally:
        if img.fp:
            img.fp.close()
    return True


def corrupt_images(directory='.', files='*.jpg'):
    """Generator that, given a ``directory``, goes through all files that
        pass through the filter ``files``, reads them onto Pillow and
        yields each corrupt image path.

        Example usage::

            target = Path('./images/corrupt/')
            target.mkdir()
            for img in corrupt_images('./images/', files='*.png'):
                # Do something with *img*, which is a Path object:
                img.rename(target / img.name)  # move it
        """
    from pathlib import Path
    directory = Path(directory)
    for p in directory.glob(files):
        if not is_valid_image(p):
            yield p
