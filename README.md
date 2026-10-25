# puzzler

A daily puzzle tool for e-readers, starting with a jailbroken Kindle 4 (non-touch).

Puzzles are pre-computed on your computer as 600x800 grayscale PNGs (one puzzle
image and one answer image per day). A KUAL extension on the Kindle shows them
and lets you move between them with the hardware buttons.

Puzzle types:

- **Word Wheel**: nine letters with one in the centre. Make words of 4+ letters
  that always use the centre letter, and find the nine-letter word.
- **Bridge** (the card game): a double-dummy ending with all four hands shown.
  South leads, in no trumps or a trump suit: how many tricks can North-South
  take? A built-in solver plays out every line. Only deals with exactly one
  winning opening lead are kept, and the answer page shows the full line of
  play. Use `--bridge-cards` to set the hand size (3–7, default 5).

## Generate puzzles

```sh
pip install -r generator/requirements.txt
python generator/tools/fetch_wordlist.py      # one-off: downloads the ENABLE word list
python generator/generate.py --days 60        # 60 days from today
```

The PNGs are written to `kindle/extensions/puzzler/puzzles/<NN_type>/`. Each
puzzle is seeded from its type and date, so rerunning gives the same puzzles.
Existing files are skipped unless you pass `--force`. See
`python generator/generate.py --help` for all options: start date, types,
grid size, word count limits and so on.

Words in `generator/data/exclude.txt` are never used in the word wheel.

## Install on the Kindle

1. Jailbreak the Kindle and install [KUAL](https://www.mobileread.com/forums/showthread.php?t=203326).
2. Connect it over USB and copy `kindle/extensions/puzzler` to the Kindle's
   `extensions/` folder, so you end up with `extensions/puzzler/config.xml`.
3. Eject, open KUAL and choose **Puzzler → Today's puzzles**.

To add more puzzles by hand, regenerate and copy the `puzzles` folder over
again. Or let the Kindle download them itself (see below).

## Hosting puzzles online

[`.github/workflows/publish.yml`](.github/workflows/publish.yml) runs every day
at 01:00 UTC, and on every push to `main`. It generates the last 7 days plus the
next 14 and publishes them, with an `index.txt` manifest, to GitHub Pages.
Because generation is seeded by date, a given day's puzzle never changes between
runs. To turn it on, go to **Settings → Pages → Source: GitHub Actions**.

On the Kindle, set `BASE_URL` in `extensions/puzzler/puzzler.conf` to the
folder containing `index.txt`. The Kindle downloads new or changed files and
deletes ones that are no longer listed. Use **Puzzler → Download puzzles now**
to test it.

**HTTPS caveat:** the Kindle 4's built-in `curl` is too old to connect to
modern HTTPS sites, including `*.github.io`. Ways around it:

- Point a custom domain at GitHub Pages (Settings → Pages → Custom domain) and
  leave **Enforce HTTPS** unticked. Then `BASE_URL="http://puzzles.yourdomain.com"`
  works.
- Copy the published files to any host that still serves plain `http://`.
- Install a newer static `curl` build on the Kindle. The script uses whichever
  `curl` comes first on `PATH`.

## Sleep and daily wake-up

While Puzzler is open, the Kindle goes to sleep after `IDLE_MINUTES` without a
button press (default 5). The puzzle
stays on the e-ink screen, which uses no power. It wakes when:

- you press the **power button**: carry on playing;
- it reaches `SYNC_TIME` (default 05:00, Kindle clock): it switches Wi-Fi on,
  downloads new puzzles, switches Wi-Fi off, shows today's puzzle and goes back
  to sleep.

Run **Puzzler → Sleep test** once to check that timed wake-up works on your
Kindle. It sleeps for two minutes and reports how long it was asleep. If
suspending doesn't work, the viewer logs it and stays awake.

## Controls

| Button                          | Action                       |
| ------------------------------- | ---------------------------- |
| Page forward / 5-way right      | Next puzzle                  |
| Page back / 5-way left          | Previous puzzle              |
| 5-way down / up                 | Next / previous puzzle type  |
| 5-way centre                    | Show / hide the answer       |
| Power (while asleep)            | Wake up                      |
| Back / Home                     | Exit Puzzler                 |

The viewer opens on today's puzzle. You can go back through earlier puzzles but
not ahead to future ones. The Kindle's own UI is paused while Puzzler is
running; exit with Back, and it restarts (this takes about 30 seconds).

If a button does nothing, run **Puzzler → Button test** from KUAL to see the key
codes your Kindle sends, then edit the `KEYS_*` lines at the top of
`kindle/extensions/puzzler/bin/puzzler.sh`. The puzzler writes a log to
`extensions/puzzler/puzzler.log`.

## Adding a puzzle type

1. Create `generator/puzzlegen/<type>.py` with `NAME`, `TITLE` and a
   `Generator` class:
   - `add_arguments(parser)`: optional command-line options
   - `__init__(args)`: one-off setup
   - `generate(rng, day)`: returns `(puzzle_image, answer_image)`

   `puzzlegen/common.py` has helpers for the page header, footer and fonts.
2. Append it to `REGISTRY` in `generator/puzzlegen/__init__.py`.

The Kindle side needs no changes, because every folder in `puzzles/` is treated
as a puzzle type.
