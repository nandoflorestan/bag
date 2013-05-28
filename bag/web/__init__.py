# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
try:
    from urllib.parse import urlencode  # Python 3
except ImportError:
    from urllib import urlencode        # Python 2
import hashlib


def gravatar_image(email, default='mm', size=80, cacheable=True):
    '''Returns a Gravatar image URL for this email.'''
    base = "http://www.gravatar.com/avatar/" if cacheable else \
        "https://secure.gravatar.com/avatar/"
    return base + \
        hashlib.md5(email.encode('utf8').lower()).hexdigest() + \
        "?" + urlencode({'d': default, 's': str(size)})
