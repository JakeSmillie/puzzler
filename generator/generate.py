"""Pre-compute daily puzzle PNGs for the Kindle Puzzler extension.

Writes  <out>/<NN>_<type>/<YYYY-MM-DD>.png  and  <YYYY-MM-DD>_answer.png,
plus <out>/index.txt listing every PNG, which the Kindle uses to download them.
Each puzzle is seeded from its type and date, so reruns are reproducible.

    python generator/generate.py --days 60
"""

import argparse
import datetime as dt
import hashlib
import random
from pathlib import Path

from puzzlegen import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "kindle" / "extensions" / "puzzler" / "puzzles"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date.today(),
                        help="first date, YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, default=30, help="number of days to generate (default: 30)")
    parser.add_argument("--types", default=",".join(REGISTRY),
                        help=f"comma-separated puzzle types (default: {','.join(REGISTRY)})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder")
    parser.add_argument("--force", action="store_true", help="overwrite puzzles that already exist")
    for module in REGISTRY.values():
        module.Generator.add_arguments(parser)
    args = parser.parse_args()

    selected = [t.strip() for t in args.types.split(",") if t.strip()]
    unknown = set(selected) - set(REGISTRY)
    if unknown:
        parser.error(f"unknown puzzle type(s): {', '.join(sorted(unknown))}")

    for order, (name, module) in enumerate(REGISTRY.items(), 1):
        if name not in selected:
            continue
        generator = module.Generator(args)
        folder = args.out / f"{order:02d}_{name}"
        folder.mkdir(parents=True, exist_ok=True)
        for offset in range(args.days):
            day = args.start + dt.timedelta(days=offset)
            puzzle_path, answer_path = folder / f"{day}.png", folder / f"{day}_answer.png"
            if puzzle_path.exists() and answer_path.exists() and not args.force:
                continue
            puzzle, answer = generator.generate(random.Random(f"{name}:{day}"), day)
            # eips wants 8-bit grayscale PNGs with no alpha channel
            puzzle.convert("L").save(puzzle_path, optimize=True)
            answer.convert("L").save(answer_path, optimize=True)
            print(f"{module.TITLE}: {day}")
    write_index(args.out)


def write_index(out):
    """List every puzzle as "<hash> <type>/<file>.png" so the Kindle can fetch new and changed files."""
    lines = [f"{hashlib.sha1(path.read_bytes()).hexdigest()[:12]} {path.relative_to(out).as_posix()}"
             for path in sorted(out.glob("*/*.png"))]
    with open(out / "index.txt", "w", newline="") as fh:
        fh.writelines(f"{line}\n" for line in lines)


if __name__ == "__main__":
    main()
