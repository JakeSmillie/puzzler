"""Draw a word wheel puzzle and its answers."""

import math

from ..puzzles.wordwheel import MIN_LEN, TITLE
from .layout import BLACK, MARGIN, WHITE, Page, font

RULES = (f"Make words of {MIN_LEN} or more letters. Every word must use the centre letter, "
         "and each letter can be used only once. Can you find the nine-letter word?")


def render(puzzle, day, profile):
    return _puzzle(puzzle, day, profile), _answer(puzzle, day, profile)


def _puzzle(puzzle, day, profile):
    page = Page(profile)
    draw = page.draw
    page.header(TITLE, day)
    cx, cy, r_out, r_in = page.width // 2, 330, 215, 72

    draw.ellipse((cx - r_out, cy - r_out, cx + r_out, cy + r_out), outline=BLACK, width=5)
    for k in range(8):
        a = math.radians(-90 + 22.5 + 45 * k)
        draw.line((cx + r_in * math.cos(a), cy + r_in * math.sin(a),
                   cx + r_out * math.cos(a), cy + r_out * math.sin(a)), fill=BLACK, width=3)
    r_mid = (r_out + r_in) / 2 + 4
    for k, letter in enumerate(puzzle.outer):
        a = math.radians(-90 + 45 * k)
        draw.text((cx + r_mid * math.cos(a), cy + r_mid * math.sin(a)), letter.upper(),
                  font=font(64, True), fill=BLACK, anchor="mm")
    draw.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), fill=BLACK)
    draw.text((cx, cy), puzzle.centre.upper(), font=font(78, True), fill=WHITE, anchor="mm")

    count = len(puzzle.words)
    targets = f"Good {round(count * 0.4)}    Very good {round(count * 0.6)}    Excellent {round(count * 0.8)}"
    draw.text((page.width // 2, 600), "Targets", font=font(24, True), fill=BLACK, anchor="ms")
    draw.text((page.width // 2, 636), targets, font=font(24), fill=BLACK, anchor="ms")
    page.footer(RULES)
    return page.image


def _answer(puzzle, day, profile):
    page = Page(profile)
    draw = page.draw
    top = page.header(f"{TITLE} answers", day)
    found = puzzle.words
    nines = [w.upper() for w in found if len(w) == 9]
    draw.text((page.width // 2, top + 44), " / ".join(nines), font=font(40, True), fill=BLACK, anchor="ms")
    draw.text((page.width // 2, top + 76), f"{len(found)} words", font=font(20), fill=BLACK, anchor="ms")
    bottom = page.footer()
    items = [w.upper() if len(w) == 9 else w for w in found]
    page.columns(items, (MARGIN, top + 96, page.width - MARGIN, bottom - 6), bold=set(nines))
    return page.image
