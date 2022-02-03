# noqa

import subprocess
from pyramid.config import Configurator
from pyramid.static import QueryStringCacheBuster

# https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html
# There are bugs in that example -- solved below.


class GitCacheBuster(QueryStringCacheBuster):
    """A cache buster that uses the hash of the current git commit.

    Assuming your code is installed as a Git checkout, as opposed to an egg
    from an egg repository like PYPI, you can use this cache buster to get
    the current commit's SHA1 to use as the cache bust token.
    """

    def __init__(self, repo_path, param="x"):  # noqa
        super(GitCacheBuster, self).__init__(param=param)
        self.token: str = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path)
            .decode("ascii")
            .strip()[:5]
        )

    def tokenize(self, request, pathspec, kw):  # noqa
        return self.token


class CacheBustedStaticDirectories:
    """DRY. Conveniently declare static views with cache busting."""

    _24hours = 60 * 60 * 24

    def __init__(self, config: Configurator, cache_buster) -> None:  # noqa
        self.config = config
        self.cache_buster = cache_buster

    def add_static_view(
        self, name: str, spec: str, cache_max_age: int = _24hours
    ) -> None:  # noqa
        self.config.add_static_view(name, spec, cache_max_age=cache_max_age)
        self.config.add_cache_buster(spec, self.cache_buster)
