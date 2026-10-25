"""Puzzle type registry.

Each puzzle module exposes NAME, TITLE and a ``Generator`` class with:

    Generator.add_arguments(parser)   # optional CLI options (classmethod/staticmethod)
    Generator(args)                   # one-off setup (load word lists, etc.)
    generator.generate(rng, day)      # -> (puzzle_image, answer_image)

To add a new puzzle type, create a module here and append it to REGISTRY.
The position in REGISTRY sets the order puzzle types appear on the Kindle,
so append new types rather than inserting them.
"""

from . import bridge, wordwheel

REGISTRY = {
    wordwheel.NAME: wordwheel,
    bridge.NAME: bridge,
}
