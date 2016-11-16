import string
from random import choice
from hashlib import sha256


def random_hash(length=12):
    """Generate a random generic hash key."""
    alist = []
    for i in range(length):
        alist.append(choice(string.ascii_letters))
    ahash = sha256(''.join(alist).encode('ascii'))
    return ahash.hexdigest()[:length]
