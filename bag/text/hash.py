import string  # noqa
from random import choice
from hashlib import sha256


def random_hash(length: int = 12) -> str:
    """Generate a random generic hash key."""
    assert length > 0
    alist = []
    for i in range(length):
        alist.append(choice(string.ascii_letters))
    ahash = sha256(''.join(alist).encode('ascii'))
    return ahash.hexdigest()[:length]
