# -*- coding: utf-8 -*-

'''Easily set up logging.'''

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import os
import logging
from logging.handlers import RotatingFileHandler
from .six import basestring


def setup_log(name='main', directory='logs', backups=3,
    level=logging.DEBUG, screen_level=logging.INFO):
    # If strings are passed in as levels, "decode" them first
    levels = dict(debug=logging.DEBUG, critical=logging.CRITICAL,
        error=logging.ERROR, fatal=logging.FATAL, info=logging.INFO,
        warn=logging.WARN, warning=logging.WARNING)
    if isinstance(level, basestring):
        level = levels[level]
    if isinstance(screen_level, basestring):
        screen_level = levels[screen_level]
    # Set up logging
    log = logging.getLogger(name)
    if len(log.handlers) == 0:
        try:
            os.mkdir(directory)
        except OSError:
            pass
        h1 = RotatingFileHandler(os.path.join(directory, name + ".log.txt"),
            maxBytes=2 ** 22, backupCount=backups)
        h1.setLevel(level)
        log.setLevel(level)
        log.addHandler(h1)
        if screen_level:
            h2 = logging.StreamHandler()
            h2.setLevel(screen_level)
            log.addHandler(h2)
    return log
