# -*- coding: utf-8 -*-

'''Functions for interaction at the console.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import str, input


def bool_input(prompt, default=None):
    '''Returns True or False based on the user's choice.'''
    opt = input(prompt + " (Y/N) ").lower()
    if opt == 'y':
        return True
    elif opt == "n":
        return False
    elif default is None:  # Invalid answer, let's ask again
        return bool_input(prompt)
    else:
        return default


def pick_one_of(alist, prompt='Pick one: '):
    '''Lets the user pick an item by number.'''
    c = 0
    for o in alist:
        c += 1
        print(str(c).rjust(2) + ". " + str(o))
    opt = int(input(prompt))
    return alist[opt - 1]
