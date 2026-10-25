"""Sudoku at two difficulty levels, each registered as its own puzzle type.

A random full grid is made, then clues are removed in symmetric pairs while
the solution stays unique. Each puzzle is graded by the hardest technique a
logical solver needs:

    1  singles only (naked and hidden)
    2  also locked candidates (pointing/claiming) and naked/hidden pairs
    3  more than that

Easy puzzles need level 1 with plenty of clues, and medium need level 2.
Level 3 puzzles are rejected.
"""

from dataclasses import dataclass
from types import SimpleNamespace

ALL = 0x1FF  # candidate bitmask: bit d-1 set means digit d is possible
ROWS = [[r * 9 + c for c in range(9)] for r in range(9)]
COLS = [[r * 9 + c for r in range(9)] for c in range(9)]
BOXES = [[(br * 3 + r) * 9 + bc * 3 + c for r in range(3) for c in range(3)] for br in range(3) for bc in range(3)]
UNITS = ROWS + COLS + BOXES
PEERS = [sorted({p for unit in UNITS if i in unit for p in unit} - {i}) for i in range(81)]
ROW_OF, COL_OF, BOX_OF = [i // 9 for i in range(81)], [i % 9 for i in range(81)], [(i // 27) * 3 + (i % 9) // 3 for i in range(81)]


@dataclass
class Sudoku:
    level: str
    givens: list     # 81 digits, row by row; 0 = blank
    solution: list   # 81 digits


def digits(mask):
    return [d for d in range(1, 10) if mask >> (d - 1) & 1]


def count_solutions(grid, limit=2):
    """Number of solutions of ``grid`` (list of 81 digits, 0 = blank), up to ``limit``."""
    cand = [ALL] * 81
    for i, d in enumerate(grid):
        if d and not _place(cand, i, d):
            return 0
    found = 0

    def search(cand):
        nonlocal found
        best, best_n = -1, 10
        for i in range(81):
            n = bin(cand[i]).count("1")
            if n == 0:
                return
            if 1 < n < best_n:
                best, best_n = i, n
        if best < 0:
            found += 1
            return
        for d in digits(cand[best]):
            trial = cand[:]
            if _place(trial, best, d):
                search(trial)
                if found >= limit:
                    return

    search(cand)
    return found


def _place(cand, i, d):
    """Fix cell ``i`` to ``d`` and propagate naked singles. False on contradiction."""
    stack = [(i, d)]
    while stack:
        i, d = stack.pop()
        bit = 1 << (d - 1)
        if not cand[i] & bit:
            return False
        cand[i] = bit
        for p in PEERS[i]:
            if cand[p] & bit:
                cand[p] &= ~bit
                if not cand[p]:
                    return False
                if cand[p] & (cand[p] - 1) == 0:
                    stack.append((p, cand[p].bit_length()))
    return True


def full_grid(rng):
    grid = [0] * 81

    def fill(i):
        if i == 81:
            return True
        used = {grid[p] for p in PEERS[i]}
        options = [d for d in range(1, 10) if d not in used]
        rng.shuffle(options)
        for d in options:
            grid[i] = d
            if fill(i + 1):
                return True
        grid[i] = 0
        return False

    fill(0)
    return grid


def grade(grid):
    """Hardest technique level (1-3) a logical solver needs for ``grid``."""
    cand = [ALL] * 81
    for i, d in enumerate(grid):
        if d:
            _place(cand, i, d)
    level = 1
    while True:
        if all(c & (c - 1) == 0 for c in cand):
            return level
        if _singles(cand):
            continue
        if _locked_candidates(cand) or _pairs(cand):
            level = 2
            continue
        return 3


def _singles(cand):
    """Place one hidden single (naked singles are already propagated). True if progress."""
    for unit in UNITS:
        for d in range(1, 10):
            bit = 1 << (d - 1)
            spots = [i for i in unit if cand[i] & bit]
            if len(spots) == 1 and cand[spots[0]] != bit:
                _place(cand, spots[0], d)
                return True
    return False


def _eliminate(cand, cells, bits):
    changed = False
    for i in cells:
        if cand[i] & bits and cand[i] & ~bits:
            cand[i] &= ~bits
            changed = True
            if cand[i] & (cand[i] - 1) == 0:
                _place(cand, i, cand[i].bit_length())
    return changed


def _locked_candidates(cand):
    for d in range(1, 10):
        bit = 1 << (d - 1)
        for b, box in enumerate(BOXES):   # pointing: a box's d all in one row/column
            spots = [i for i in box if cand[i] & bit and cand[i] != bit]
            for line_of, lines in ((ROW_OF, ROWS), (COL_OF, COLS)):
                if spots and len({line_of[i] for i in spots}) == 1:
                    rest = [i for i in lines[line_of[spots[0]]] if BOX_OF[i] != b]
                    if _eliminate(cand, rest, bit):
                        return True
        for lines in (ROWS, COLS):   # claiming: a line's d all in one box
            for line in lines:
                spots = [i for i in line if cand[i] & bit and cand[i] != bit]
                if spots and len({BOX_OF[i] for i in spots}) == 1:
                    rest = [i for i in BOXES[BOX_OF[spots[0]]] if i not in line]
                    if _eliminate(cand, rest, bit):
                        return True
    return False


def _pairs(cand):
    for unit in UNITS:
        open_cells = [i for i in unit if cand[i] & (cand[i] - 1)]
        # naked pair: two cells with the same two candidates
        for a in range(len(open_cells)):
            for b in range(a + 1, len(open_cells)):
                ca = cand[open_cells[a]]
                if ca == cand[open_cells[b]] and bin(ca).count("1") == 2:
                    rest = [i for i in open_cells if i not in (open_cells[a], open_cells[b])]
                    if _eliminate(cand, rest, ca):
                        return True
        # hidden pair: two digits that only fit in the same two cells
        where = {d: [i for i in open_cells if cand[i] >> (d - 1) & 1] for d in range(1, 10)}
        twos = [d for d, cells in where.items() if len(cells) == 2]
        for x in range(len(twos)):
            for y in range(x + 1, len(twos)):
                if where[twos[x]] == where[twos[y]]:
                    keep = (1 << (twos[x] - 1)) | (1 << (twos[y] - 1))
                    changed = False
                    for i in where[twos[x]]:
                        if cand[i] & ~keep:
                            cand[i] &= keep
                            changed = True
                    if changed:
                        return True
    return False


class _Generator:
    LEVEL = None
    TARGET = None   # (wanted grade, stop removing at this many clues or None for as few as possible)

    @staticmethod
    def add_arguments(parser):
        pass

    def __init__(self, args):
        pass

    def generate(self, rng, day):
        wanted, stop_at = self.TARGET
        for _ in range(500):
            solution = full_grid(rng)
            grid = solution[:]
            cells = list(range(41))   # 40 symmetric pairs plus the centre
            rng.shuffle(cells)
            for i in cells:
                if stop_at and sum(1 for d in grid if d) <= stop_at:
                    break
                pair = {i, 80 - i}
                saved = [grid[j] for j in pair]
                for j in pair:
                    grid[j] = 0
                if count_solutions(grid) != 1:
                    for j, d in zip(pair, saved):
                        grid[j] = d
            if grade(grid) == wanted:
                return Sudoku(self.LEVEL, grid, solution)
        raise RuntimeError(f"could not make a {self.LEVEL} sudoku")


def _variant(level, target):
    generator = type(f"{level.title()}Generator", (_Generator,), {"LEVEL": level, "TARGET": target})
    return SimpleNamespace(NAME=f"sudoku_{level}", TITLE=f"{level.title()} Sudoku", Generator=generator)


VARIANTS = [
    _variant("easy", (1, 36)),
    _variant("medium", (2, None)),
]
