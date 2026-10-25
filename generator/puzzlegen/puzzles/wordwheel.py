"""Word wheel: nine letters, make words that always include the centre letter."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

NAME = "wordwheel"
TITLE = "Word Wheel"
MIN_LEN = 4

DATA = Path(__file__).resolve().parents[2] / "data"
DEFAULT_WORDLIST = DATA / "words.txt"
DEFAULT_EXCLUDE = DATA / "exclude.txt"


@dataclass
class WordWheel:
    centre: str
    outer: list   # the eight outer letters, clockwise from the top
    words: list   # every answer, shortest first


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
                    return WordWheel(centre, outer, found)
        raise RuntimeError("could not find a word wheel within the word count limits")
