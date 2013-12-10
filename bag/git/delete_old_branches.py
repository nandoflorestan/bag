#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Removes git branches that have been merged onto the current branch.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import date, timedelta
from nine.decorator import reify
from nine import nine
from argh import ArghParser, arg  # easy_install argh
from bag.command import checked_execute  # , CommandError
from bag.console import bool_input


def merged_branches(even_remote_ones=False):
    '''Yields branches that have been merged onto the current branch.'''
    if even_remote_ones:
        command = 'git branch -a --merged'
    else:
        command = 'git branch --merged'
    for branch in checked_execute(command).split('\n'):
        # The command also lists the current branch, so we get rid of it
        if branch.startswith('* '):
            continue
        yield Branch(branch.strip())


@nine
class Branch(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    @reify
    def merge_date(self):
        '''Returns the date when the specified branch was merged into the
        current git branch. On the console, you can try this command:

            git show --pretty=format:"%Cgreen%ci %Cblue%cr%Creset" BRANCH | head -n 1
        '''
        line = checked_execute(
            'git show --pretty=format:"%ci" {} | head -n 1'
            .format(self.name))
        sdate = line[:10]
        year, month, day = [int(x) for x in sdate.split('-')]
        return date(year, month, day)

    def is_older_than_days(self, age):
        return timedelta(int(age)) < date.today() - self.merge_date

    def delete_locally(self):
        checked_execute('git branch -d {}'.format(self))

    def delete_remotely(self, remote):
        checked_execute('git push {} :{}'.format(remote, self))


@arg('--dry', action='store_true', help='Dry run: only list the branches')
@arg('-l', '--locally', action='store_true',
     help='Delete the branches locally')
@arg('-r', '--remote', metavar='REMOTE',
     help='Delete the branches on the remote REMOTE')
@arg('-y', action='store_true',
     help='Do not interactively confirm before deleting branches')
@arg('-d', '--days', type=int, help='Minimum age in days')
def delete_old_branches(dry, locally, remote, y, days):
    for branch in merged_branches(even_remote_ones=remote):
        if days and not branch.is_older_than_days(days):
            continue

        if y:
            print(branch)
        else:
            if not bool_input('Delete the branch "{}"?'.format(branch),
                              default=False):
                continue

        if dry:
            continue
        if locally:
            branch.delete_locally()
        if remote:
            branch.delete_remotely(remote)


def command():
    # http://argh.readthedocs.org/en/latest/
    parser = ArghParser(description=__doc__)
    parser.set_default_command(delete_old_branches)
    # parser.add_commands([delete_old_branches])
    parser.dispatch()


if __name__ == '__main__':
    command()
