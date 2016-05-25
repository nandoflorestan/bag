#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Decorator that makes it easy to use **argh** to create subcommands.

    Usage::

        from bag.subcommand import subcommand, main

        @subcommand
        def my_subcommand(foo:'Help for foo'='default value'):
            pass

        if __name__ == '__main__':
            main()
        """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import IS_PYTHON2, nimport, nine, range, str, basestring


def subcommand(fn):
    """Decorator that adds the decorated function to a list."""
    if not hasattr(subcommand, 's'):  # Because functions are 1st class objects
        subcommand.s = []          # we can store the list inside the function.
    subcommand.s.append(fn)        # One global variable less.
    return fn


def main():
    """Uses argh to dispatch to your subcommands."""
    from argh import ArghParser  # sudo apt-get install python3-argh
    parser = ArghParser()
    # Sorting makes the output of --help better:
    parser.add_commands(sorted(subcommand.s, key=lambda f: f.__name__))
    # parser.add_commands(subcommand.s)
    parser.dispatch()
