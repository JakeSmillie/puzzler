"""Pre-compute daily puzzles for every client display profile.

Writes, for each profile (see docs/protocol.md):
    <out>/<profile>/<NN>_<type>/<YYYY-MM-DD>.png  and  <YYYY-MM-DD>_answer.png
    <out>/<profile>/index.txt   listing every PNG, which clients use to download them
Each puzzle is seeded from its type and date, so reruns are reproducible.

    python generator/generate.py --past 7 --days 30
"""

import argparse
import datetime as dt
import hashlib
import random
from pathlib import Path

from puzzlegen import REGISTRY
from puzzlegen.render.profiles import PROFILES

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "site"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date.today(),
                        help="first date, YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, default=30,
                        help="number of days to generate from --start onwards (default: 30)")
    parser.add_argument("--past", type=int, default=0,
                        help="also generate this many days before --start (default: 0)")
    parser.add_argument("--types", default=",".join(REGISTRY),
                        help=f"comma-separated puzzle types (default: {','.join(REGISTRY)})")
    parser.add_argument("--profiles", default=",".join(PROFILES),
                        help=f"comma-separated display profiles (default: {','.join(PROFILES)})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default: site/)")
    parser.add_argument("--force", action="store_true", help="overwrite puzzles that already exist")
    # Types that share a module (e.g. the sudoku levels) share their options, so add each set once
    for add_arguments in dict.fromkeys(module.Generator.add_arguments for module, _ in REGISTRY.values()):
        add_arguments(parser)
    args = parser.parse_args()

    types = _pick(parser, args.types, REGISTRY, "puzzle type")
    profiles = [PROFILES[p] for p in _pick(parser, args.profiles, PROFILES, "profile")]

    for order, (name, (module, renderer)) in enumerate(REGISTRY.items(), 1):
        if name not in types:
            continue
        generator = module.Generator(args)
        for offset in range(-args.past, args.days):
            day = args.start + dt.timedelta(days=offset)
            todo = []
            for profile in profiles:
                folder = args.out / profile.name / f"{order:02d}_{name}"
                paths = folder / f"{day}.png", folder / f"{day}_answer.png"
                if args.force or not all(p.exists() for p in paths):
                    todo.append((profile, paths))
            if not todo:
                continue
            puzzle = generator.generate(random.Random(f"{name}:{day}"), day)
            for profile, paths in todo:
                paths[0].parent.mkdir(parents=True, exist_ok=True)
                for image, path in zip(renderer.render(puzzle, day, profile), paths):
                    profile.save(image, path)
            print(f"{module.TITLE}: {day}")

    for profile in profiles:
        write_index(args.out / profile.name)


def _pick(parser, value, known, label):
    chosen = [v.strip() for v in value.split(",") if v.strip()]
    unknown = set(chosen) - set(known)
    if unknown:
        parser.error(f"unknown {label}(s): {', '.join(sorted(unknown))}")
    return chosen


def write_index(out):
    """List every puzzle as "<hash> <type>/<file>.png" so clients can fetch new and changed files."""
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"{hashlib.sha1(path.read_bytes()).hexdigest()[:12]} {path.relative_to(out).as_posix()}"
             for path in sorted(out.glob("*/*.png"))]
    with open(out / "index.txt", "w", newline="") as fh:
        fh.writelines(f"{line}\n" for line in lines)


if __name__ == "__main__":
    main()
