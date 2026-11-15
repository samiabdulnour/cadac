"""Office standards for Archicad, kept as data, and the checks that hold a
template and a model to them.

``standards`` and ``brief`` read the files a person writes; ``audit`` compares
what a template holds with what the standards list. Those three are pure and
are what the tests cover. ``archicad`` and ``snapshot`` talk to a running
Archicad, which no test can do: see ``docs/archicad.md`` for where each
command's shape was read from and which have been run against a live one.
"""

__version__ = "0.0.1"
