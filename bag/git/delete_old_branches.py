#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Removes git branches that have been merged onto the current branch.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from argh import ArghParser, arg  # easy_install argh
from bag.command import checked_execute  # , CommandError


def merged_branches():
    '''Yields the names of the branches that have been merged onto the
    current branch.
    '''
    for branch in checked_execute('git branch --merged').split('\n'):
        # The command also lists the current branch, so we get rid of it
        if branch.startswith('* '):
            continue
        yield branch.strip()


@arg('-v', help='List the branches to be deleted')
@arg('-y', default=False,
     help='Do not interactively confirm before deleting branches')
@arg('--age', help='Minimum age in days')
def delete_old_branches(v, y, age, bruhaha):
    if age:
        # For each branch, find its merge date:
        # git show --pretty=format:"%Cgreen%ci %Cblue%cr%Creset" BRANCH | head -n 1
        pass


def main():
    # http://argh.readthedocs.org/en/latest/
    parser = ArghParser(description=__doc__)
    parser.set_default_command(delete_old_branches)
    # parser.add_commands([delete_old_branches])
    parser.dispatch()

if __name__ == '__main__':
    main()
