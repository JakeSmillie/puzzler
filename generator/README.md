# Generator

Makes each day's puzzles, draws them for every display profile, and builds the
static site that clients download from (see [docs/protocol.md](../docs/protocol.md)).

All commands below are run from the repo root.

## Setup

Needs Python 3.10 or later.

```sh
pip install -r generator/requirements.txt
python generator/tools/fetch_wordlist.py      # one-off: downloads the ENABLE word list to generator/data/words.txt
```

## Generate puzzles

```sh
python generator/generate.py --past 7 --days 30
```

This writes the last 7 days, today and the next 29 days to `site/<profile>/`.
Useful options:

| Option | Meaning |
| --- | --- |
| `--start YYYY-MM-DD` | First day (default: today) |
| `--days N` | Days from `--start` onwards, including `--start` (default: 30) |
| `--past N` | Also generate N days before `--start` (default: 0) |
| `--types wordwheel,bridge,sudoku_easy` | Only these puzzle types (also `sudoku_medium`) |
| `--profiles kindle4` | Only these display profiles |
| `--out DIR` | Output folder (default: `site/`) |
| `--force` | Regenerate files that already exist |
| `--bridge-cards N` | Bridge hand size, 3–7 (default: 5) |
| `--ww-min-words N`, `--ww-max-words N` | Word wheel answer count limits (default: 20–70) |

Run `python generator/generate.py --help` for the full list.

Each puzzle is seeded from its type and date, so rerunning gives the same
puzzles. Existing files are skipped unless you pass `--force`, so it's quick to
top up. Words in `generator/data/exclude.txt` are never used in the word wheel.

## Look at the output

The images are ordinary PNGs. Open them in any image viewer, for example:

```sh
start site/kindle4/01_wordwheel          # Windows: open the folder in Explorer
```

## Serve the site locally

To let a client download from your PC on your home network:

```sh
python -m http.server 8000 --directory site
```

The site is then at `http://<your PC's IP>:8000/`, with each profile in its own
folder, for example `http://192.168.86.74:8000/kindle4/index.txt`. To find your
IP address, run `ipconfig` on Windows (the **IPv4 Address** of your Wi-Fi
adapter) or `ip addr` on Linux. Press Ctrl+C to stop the server.

## Publishing

[`.github/workflows/publish.yml`](../.github/workflows/publish.yml) runs every
day at 01:00 UTC, on every push to `main`, and on demand from the Actions tab.
It generates the last 7 days plus the next 14 for every profile and publishes
`site/` to GitHub Pages.

To set it up, go to **Settings → Pages → Source: GitHub Actions** on GitHub,
then **Actions → Publish puzzles → Run workflow**. Clients point at their
profile's folder, for example `https://<user>.github.io/puzzler/kindle4`.

## Structure

```
generate.py              command line: generates every type for every profile
puzzlegen/
  __init__.py            REGISTRY of puzzle types
  puzzles/<type>.py      puzzle logic: makes and solves puzzles, no drawing
  render/<type>.py       draws a puzzle and its answer for a display profile
  render/layout.py       shared header, footer, fonts
  render/profiles.py     display profiles (screen size, format, button hints)
data/exclude.txt         words never used in the word wheel
tools/fetch_wordlist.py  downloads the word list
```

### Adding a puzzle type

1. Create `puzzlegen/puzzles/<type>.py` with `NAME`, `TITLE` and a `Generator`
   class:
   - `add_arguments(parser)`: optional command-line options
   - `__init__(args)`: one-off setup
   - `generate(rng, day)`: returns the puzzle as data, for example a dataclass
2. Create `puzzlegen/render/<type>.py` with `render(puzzle, day, profile)`,
   returning `(puzzle_image, answer_image)`. Use `layout.Page` for the shared
   header and footer.
3. Append both to `REGISTRY` in `puzzlegen/__init__.py`.

One module can provide several types. `puzzles/sudoku.py` registers
`sudoku_easy` and `sudoku_medium` from a list of `VARIANTS`, each
with its own `NAME`, `TITLE` and `Generator`. Each variant gets its own folder on
the site, so clients show them as separate puzzle types.

Clients need no changes, because every type folder on the site is treated as a
puzzle type.

### Adding a display profile

See [docs/protocol.md](../docs/protocol.md#adding-a-profile).
