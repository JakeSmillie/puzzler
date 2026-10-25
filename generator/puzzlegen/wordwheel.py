"""Word wheel: nine letters, make words that always include the centre letter."""

import math
from collections import Counter
from pathlib import Path

from .common import BLACK, MARGIN, WHITE, WIDTH, columns, font, footer, header, new_page

NAME = "wordwheel"
TITLE = "Word Wheel"
MIN_LEN = 4

DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_WORDLIST = DATA / "words.txt"
DEFAULT_EXCLUDE = DATA / "exclude.txt"
RULES = (f"Make words of {MIN_LEN} or more letters. Every word must use the centre letter, "
         "and each letter can be used only once. Can you find the nine-letter word?")


def _read_words(path):
    with open(path, encoding="utf-8") as fh:
        return [line.strip().lower() for line in fh if line.strip() and not line.startswith("#")]


class Generator:
    @staticmethod
    def add_arguments(parser):
        group = parser.add_argument_group("word wheel")
        group.add_argument("--wordlist", type=Path, default=DEFAULT_WORDLIST,
                           help="one word per line (default: generator/data/words.txt)")
        group.add_argument("--ww-exclude", type=Path, default=DEFAULT_EXCLUDE,
                           help="words never to use (default: generator/data/exclude.txt)")
        group.add_argument("--ww-min-words", type=int, default=20, help="fewest answers allowed")
        group.add_argument("--ww-max-words", type=int, default=70, help="most answers allowed")

    def __init__(self, args):
        if not args.wordlist.exists():
            raise SystemExit(f"Word list not found at {args.wordlist}.\n"
                             "Run: python generator/tools/fetch_wordlist.py")
        words = {w for w in _read_words(args.wordlist)
                 if MIN_LEN <= len(w) <= 9 and w.isascii() and w.isalpha()}
        if args.ww_exclude.exists():
            words -= set(_read_words(args.ww_exclude))
        self.words = [(w, Counter(w), frozenset(w)) for w in sorted(words)]
        self.nines = sorted(w for w in words if len(w) == 9)
        self.min_words = args.ww_min_words
        self.max_words = args.ww_max_words

    def generate(self, rng, day):
        for _ in range(1000):
            nine = rng.choice(self.nines)
            letters, letter_set = Counter(nine), frozenset(nine)
            pool = [(w, s) for w, c, s in self.words if s <= letter_set and not c - letters]
            centres = sorted(letter_set)
            rng.shuffle(centres)
            for centre in centres:
                found = sorted((w for w, s in pool if centre in s), key=lambda w: (len(w), w))
                if self.min_words <= len(found) <= self.max_words:
                    outer = list(nine)
                    outer.remove(centre)
                    rng.shuffle(outer)
                    return self._puzzle(day, centre, outer, len(found)), self._answer(day, found)
        raise RuntimeError("could not find a word wheel within the word count limits")

    def _puzzle(self, day, centre, outer, count):
        img, draw = new_page()
        header(draw, TITLE, day)
        cx, cy, r_out, r_in = WIDTH // 2, 330, 215, 72

        draw.ellipse((cx - r_out, cy - r_out, cx + r_out, cy + r_out), outline=BLACK, width=5)
        for k in range(8):
            a = math.radians(-90 + 22.5 + 45 * k)
            draw.line((cx + r_in * math.cos(a), cy + r_in * math.sin(a),
                       cx + r_out * math.cos(a), cy + r_out * math.sin(a)), fill=BLACK, width=3)
        r_mid = (r_out + r_in) / 2 + 4
        for k, letter in enumerate(outer):
            a = math.radians(-90 + 45 * k)
            draw.text((cx + r_mid * math.cos(a), cy + r_mid * math.sin(a)), letter.upper(),
                      font=font(64, True), fill=BLACK, anchor="mm")
        draw.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), fill=BLACK)
        draw.text((cx, cy), centre.upper(), font=font(78, True), fill=WHITE, anchor="mm")

        targets = f"Good {round(count * 0.4)}    Very good {round(count * 0.6)}    Excellent {round(count * 0.8)}"
        draw.text((WIDTH // 2, 600), "Targets", font=font(24, True), fill=BLACK, anchor="ms")
        draw.text((WIDTH // 2, 636), targets, font=font(24), fill=BLACK, anchor="ms")
        footer(draw, RULES)
        return img

    def _answer(self, day, found):
        img, draw = new_page()
        top = header(draw, f"{TITLE} answers", day)
        nines = [w.upper() for w in found if len(w) == 9]
        draw.text((WIDTH // 2, top + 44), " / ".join(nines), font=font(40, True), fill=BLACK, anchor="ms")
        draw.text((WIDTH // 2, top + 76), f"{len(found)} words", font=font(20), fill=BLACK, anchor="ms")
        bottom = footer(draw)
        items = [w.upper() if len(w) == 9 else w for w in found]
        columns(draw, items, (MARGIN, top + 96, WIDTH - MARGIN, bottom - 6), bold=set(nines))
        return img
