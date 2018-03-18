"""Simplifying usage of the **subprocess** module of the standard library."""

import subprocess
from sys import platform


class CommandError(Exception):

    def __init__(self, error_message, code, out=''):
        self.error_message = error_message
        self.code = code
        self.out = out

    def __str__(self):
        return self.error_message + ' (exit code: {})'.format(self.code)


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


def checked_execute(command, input='', shell=True, encoding='utf-8',
                    accept_codes=[0]):
    ret, out, err = execute(
        command, input=input, shell=shell, encoding=encoding)
    if ret in accept_codes:
        return out
    else:
        raise CommandError(err, ret, out)
