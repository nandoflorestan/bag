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


def merged_branches(remote=None):
    '''Sequence of branches that have been merged onto the current branch.'''
    if remote:
        command = 'git branch -a --merged'
        remote = 'remotes/{}/'.format(remote)
    else:
        command = 'git branch --merged'
    adict = {}
    for name in checked_execute(command).split('\n'):
        # The command also lists the current branch, so we get rid of it
        if name.startswith('* ') or ' -> ' in name:
            continue
        name = name.strip()

        if remote and name.startswith(remote):
            name = name[len(remote):]
            is_remote = True
            is_local = False
        else:
            is_remote = False
            is_local = True

        branch = adict.get(name)
        if branch is None:
            adict[name] = Branch(
                name, prefix=remote, is_local=is_local, is_remote=is_remote)
        else:
            branch.is_local = branch.is_local or is_local
            branch.is_remote = branch.is_remote or is_remote

    return sorted(adict.values(), key=lambda x: x.name)


@nine
class Branch(object):
    def __init__(self, name, prefix='', is_local=False, is_remote=False):
        assert is_local or is_remote
        self.name = name
        self.prefix = prefix or ''
        self.is_local = is_local
        self.is_remote = is_remote

    def __repr__(self):
        return self.name

    @reify
    def merge_date(self):
        '''Returns the date when the specified branch was merged into the
        current git branch. On the console, you can try this command:

            git show --pretty=format:"%Cgreen%ci %Cblue%cr%Creset" BRANCH | head -n 1
        '''
        branch_name = self.name if self.is_local else self.prefix + self.name
        line = checked_execute(
            'git show --pretty=format:"%ci" {} | head -n 1'
            .format(branch_name))
        sdate = line[:10]
        year, month, day = [int(x) for x in sdate.split('-')]
        return date(year, month, day)

    def is_older_than_days(self, age):
        return timedelta(int(age)) < date.today() - self.merge_date

    def delete_locally(self):
        if self.is_local:
            checked_execute('git branch -d {}'.format(self))

    def delete_remotely(self, remote):
        if self.is_remote:
            checked_execute('git push {} :{}'.format(remote, self),
                            accept_codes=[0, 1])


@arg('--dry', action='store_true', help='Dry run: only list the branches')
@arg('-l', '--locally', action='store_true',
     help='Delete the branches locally')
@arg('-r', '--remote', metavar='REMOTE',
     help='Delete the branches on the remote REMOTE')
@arg('-y', action='store_true',
     help='Do not interactively confirm before deleting branches')
@arg('days', type=int, help='Minimum age in days')
def delete_old_branches(days, dry=False, locally=False, remote=None, y=False):
    for branch in merged_branches(remote):
        if branch.name in ('master', 'develop') or (
                days and not branch.is_older_than_days(days)):
            continue

        if y:
            print(branch)
        else:
            if not bool_input('Delete the branch "{}"?'.format(branch),
                              default=False):
                continue

        if dry:
            continue
        if remote:
            branch.delete_remotely(remote)
        if locally:
            branch.delete_locally()


def command():
    # http://argh.readthedocs.org/en/latest/
    parser = ArghParser(description=__doc__)
    parser.set_default_command(delete_old_branches)
    # parser.add_commands([delete_old_branches])
    parser.dispatch()


if __name__ == '__main__':
    command()
