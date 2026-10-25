"""Puzzle type registry.

Each puzzle type is two modules:

    puzzles/<type>.py   NAME, TITLE and a Generator class:
                          Generator.add_arguments(parser)   optional CLI options
                          Generator(args)                   one-off setup (load word lists, etc.)
                          generator.generate(rng, day)      -> puzzle data, no drawing
    render/<type>.py    render(puzzle, day, profile)        -> (puzzle_image, answer_image)

To add a type, write both modules and append them to REGISTRY. The position in
REGISTRY sets the order types appear on clients, so append new types rather
than inserting them.
"""

from .puzzles import bridge, wordwheel
from .render import bridge as bridge_render, wordwheel as wordwheel_render

REGISTRY = {
    wordwheel.NAME: (wordwheel, wordwheel_render),
    bridge.NAME: (bridge, bridge_render),
}
