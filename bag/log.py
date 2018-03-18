"""Easily set up logging."""

import os
import logging
from logging.handlers import (RotatingFileHandler, TimedRotatingFileHandler,
                              WatchedFileHandler)

FORMAT = '%(asctime)s %(levelname)s %(message)s'


def setup_log(name=None, path='logs', rotating=True, backups=3, file_mode='a',
              disk_level=logging.DEBUG, screen_level=logging.INFO,
              encoding='utf-8'):
    """This logs to screen if ``screen_level`` is not None, and logs to
    disk if ``disk_level`` is not None.

    If you do not pass a log ``name``, the root log is configured and
    returned.

    If ``rotating`` is True, a RotatingFileHandler is configured on the
    directory passed as ``path``.

    If ``rotating`` is False, a single log file will be created at ``path``.
    Its ``file_mode`` defaults to `a` (append), but you can set it to `w`.
    """
    # If strings are passed in as levels, "decode" them first
    levels = dict(
        debug=logging.DEBUG,                         # 10
        info=logging.INFO,                            # 20
        warn=logging.WARN, warning=logging.WARNING,    # 30
        error=logging.ERROR,                            # 40
        critical=logging.CRITICAL, fatal=logging.FATAL,  # 50
    )
    if isinstance(disk_level, str):
        disk_level = levels[disk_level.lower()]
    if isinstance(screen_level, str):
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
            h2 = RotatingFileHandler(os.path.join(
                path, name or 'root' + ".log.txt"), encoding=encoding,
                maxBytes=2 ** 22, backupCount=backups)
        else:
            h2 = WatchedFileHandler(path, mode=file_mode, encoding=encoding)
        h2.setLevel(disk_level)
        log.setLevel(disk_level)
        log.addHandler(h2)
    return log


def setup_rotating_logger(logger=None, backups=4, size=250000000,
                          level=logging.DEBUG, encoding='utf-8',
                          format=FORMAT, directory='.'):
    """You may pass either a name or an existing logger as the first argument.
    This attaches a RotatingFileHandler to the specified logger.
    Returns the logger object.
    """
    if isinstance(logger, str):
        filename = '.'.join((logger, encoding, 'log'))
        logger = logging.getLogger(logger)
    else:
        filename = '.'.join((logger.name, encoding, 'log'))
    hr = RotatingFileHandler(os.path.join(directory, filename), maxBytes=size,
                             backupCount=backups, encoding=encoding)
    if format:
        hr.setFormatter(logging.Formatter(format))
    logger.addHandler(hr)
    logger.setLevel(level)
    return logger


def setup_timed_rotating_logger(logger=None, level=logging.DEBUG, backups=14,
                                when='D', interval=1, utc=True, delay=False,
                                encoding='utf-8', format=FORMAT,
                                directory='.'):
    """You may pass either a name or an existing logger as the first argument.
    This attaches a TimedRotatingFileHandler to the specified logger.
    Returns the logger object.
    """
    if isinstance(logger, str):
        filename = '.'.join((logger, encoding, 'log'))
        logger = logging.getLogger(logger)
    else:
        filename = '.'.join((logger.name, encoding, 'log'))
    hr = TimedRotatingFileHandler(
        os.path.join(directory, filename), utc=utc, encoding=encoding,
        when=when, interval=interval, backupCount=backups, delay=delay)
    if format:
        hr.setFormatter(logging.Formatter(format))
    logger.addHandler(hr)
    logger.setLevel(level)
    return logger


def setup_watched_file_handler(logger=None, level=logging.DEBUG, format=FORMAT,
                               encoding='utf-8', delay=False, directory='.'):
    """You may pass either a name or an existing logger as the first argument.
    This attaches a WatchedFileHandler to the specified logger.
    Returns the logger object.

    The WatchedFileHandler detects when the log file is moved, so it is
    compatible with the logrotate daemon.
    """
    if isinstance(logger, str):
        filename = '.'.join((logger, encoding, 'log'))
        logger = logging.getLogger(logger)
    else:
        filename = '.'.join((logger.name, encoding, 'log'))
    hr = WatchedFileHandler(os.path.join(directory, filename), delay=delay,
                            encoding=encoding)
    if format:
        hr.setFormatter(logging.Formatter(format))
    logger.addHandler(hr)
    logger.setLevel(level)
    return logger
