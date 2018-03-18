"""The bag.web module contains code that helps web development generically.

Then there's a :py:mod:`bag.web.pyramid` module that integrates the
generic code into the Pyramid web framework (as can be done with other
frameworks).
"""

import hashlib
from urllib.parse import urlencode


def gravatar_image(
    email: str, default: str='mm', size: int=80, cacheable: bool=True,
) -> str:
    """Return a Gravatar image URL for this ``email``."""
    base = "http://www.gravatar.com/avatar/" if cacheable else \
        "https://secure.gravatar.com/avatar/"
    return base + \
        hashlib.md5(email.encode('utf8').lower()).hexdigest() + \
        "?" + urlencode({'d': default, 's': str(size)})
