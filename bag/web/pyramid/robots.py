"""Easily serve a robots.txt file using Pyramid."""

from typing import List, Tuple
from bag.settings import asbool
# http://en.wikipedia.org/wiki/Robots_exclusion_standard


def includeme(config):
    """Integrate. The easiest, but not the only, way to use this module."""
    is_production = asbool(config.registry.settings.get('production', 'false'))
    robot = RobotFile()
    robot.add_rule(user_agent='*',
                   disallow='' if is_production else '/')
    init(config, robot)


def init(config, robot):
    config.add_route('robots', 'robots.txt')

    def robots_view(context, request):
        return str(robot)

    config.add_view(robots_view, route_name='robots', renderer='string')


class RobotFile:

    rules = []  # type: List[Rule]

    def add_rule(self, user_agent, disallow=[], allow=[]):
        self.rules.append(Rule(user_agent, disallow, allow))

    def __str__(self):
        return "\n".join(map(lambda x: str(x), self.rules))


class Rule:

    items = []  # type: List[Tuple[str, str]]

    def __init__(self, user_agent, disallow, allow):
        assert user_agent
        self.items.append(("User-agent", user_agent))
        self._append_string_or_list("Allow", allow)
        self._append_string_or_list("Disallow", disallow)

    def _append_string_or_list(self, keyword, item):
        if isinstance(item, str):
            self.items.append((keyword, item))
        else:
            for i in item:
                self.items.append((keyword, i))

    def __str__(self):
        return "\n".join(map(lambda t: ": ".join(t), self.items))
