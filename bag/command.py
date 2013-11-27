# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import subprocess
from sys import platform


class CommandError(Exception):
    pass


def execute(command, input='', shell=True, encoding='utf-8'):
    p = subprocess.Popen(command, shell=shell,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=not platform.startswith('win'))
    i, o, e = (p.stdin, p.stdout, p.stderr)
    if input:
        i.write(input)
    i.close()
    return_code = p.wait()
    normal_output = o.read().strip().decode(encoding)
    error_output = e.read().strip().decode(encoding)
    o.close()
    e.close()
    return return_code, normal_output, error_output


def checked_execute(command, input='', shell=True, encoding='utf-8'):
    ret, out, err = execute(
        command, input=input, shell=shell, encoding=encoding)
    if ret == 0:
        return out
    else:
        raise CommandError(err)
