# -*- coding: utf-8 -*-

'''Easily set up logging.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import logging
from logging.handlers import RotatingFileHandler
from nine import basestring


def setup_log(name=None, path='logs', rotating=True, backups=3, file_mode='a',
              disk_level=logging.DEBUG, screen_level=logging.INFO,
              encoding='utf-8'):
    '''This logs to screen if ``screen_level`` is not None, and logs to
    disk if ``disk_level`` is not None.

    If you do not pass a log ``name``, the root log is configured and
    returned.

    If ``rotating`` is True, a RotatingFileHandler is configured on the
    directory passed as ``path``.

    If ``rotating`` is False, a single log file will be created at ``path``.
    Its ``file_mode`` defaults to `a` (append), but you can set it to `w`.
    '''
    # If strings are passed in as levels, "decode" them first
    levels = dict(
        debug=logging.DEBUG,                         # 10
        info=logging.INFO,                            # 20
        warn=logging.WARN, warning=logging.WARNING,    # 30
        error=logging.ERROR,                            # 40
        critical=logging.CRITICAL, fatal=logging.FATAL,  # 50
    )
    if isinstance(disk_level, basestring):
        disk_level = levels[disk_level.lower()]
    if isinstance(screen_level, basestring):
        screen_level = levels[screen_level.lower()]
    # Set up logging
    log = logging.getLogger(name)
    if screen_level:
        h1 = logging.StreamHandler()
        h1.setLevel(screen_level)
        log.addHandler(h1)
    if disk_level:
        if rotating:
            try:
                os.mkdir(path)
            except OSError:
                pass
            h2 = RotatingFileHandler(os.path.join(path,
                name or 'root' + ".log.txt"), encoding=encoding,
                maxBytes=2 ** 22, backupCount=backups)
        else:
            h2 = logging.FileHandler(path, mode=file_mode, encoding=encoding)
        h2.setLevel(disk_level)
        log.setLevel(disk_level)
        log.addHandler(h2)
    return log
