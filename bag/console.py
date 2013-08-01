# -*- coding: utf-8 -*-

'''Functions for interaction at the console.'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nine import str, input


def ask(prompt='', default=None):
    if prompt:
        if default:
            prompt = prompt + ' [' + default + ']'
        prompt = prompt + ' '
    answer = None
    while not answer:
        answer = input(prompt)
        if default and not answer:
            return default
    return answer


def bool_input(prompt, default=None):
    '''Returns True or False based on the user's choice.'''
    if default is None:
        choices = ' (y/n) '
    elif default:
        choices = ' (Y/n) '
    else:
        choices = ' (y/N) '
    opt = input(prompt + choices).lower()
    if opt == 'y':
        return True
    elif opt == "n":
        return False
    elif not opt and default is not None:
        return default
    else:  # Invalid answer, let's ask again
        return bool_input(prompt)


def pick_one_of(alist, prompt='Pick one: '):
    '''Lets the user pick an item by number.'''
    c = 0
    for o in alist:
        c += 1
        print(str(c).rjust(2) + ". " + str(o))
    while True:
        try:
            opt = int(input(prompt))
        except ValueError:
            continue
        return alist[opt - 1]
