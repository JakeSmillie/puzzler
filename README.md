# puzzler

Daily puzzles for e-ink devices. A generator makes each day's puzzles as
images and publishes them as a static website. Client devices download them,
show the day's puzzle, and sleep in between.

```
generator/    makes the puzzles and builds the site       (Python)
clients/      one folder per client device, each with its own case
docs/         protocol.md: the site layout clients rely on
.github/      daily build and publish to GitHub Pages
```

| Part | Docs | Status |
| --- | --- | --- |
| Generator and hosting | [generator/README.md](generator/README.md) | Working |
| Kindle 4 (non-touch) client | [clients/kindle4/README.md](clients/kindle4/README.md) | Working |
| Newer Kindles (`clients/kindle-touch`) | | Planned |
| ESP32 + e-ink panel (`clients/esp32-epaper`) | | Planned |
| Site protocol | [docs/protocol.md](docs/protocol.md) | |

## Puzzle types

- **Word Wheel**: nine letters with one in the centre. Make words of 4+ letters
  that always use the centre letter, and find the nine-letter word.
- **Bridge** (the card game): a double-dummy ending with all four hands shown.
  South leads, in no trumps or a trump suit: how many tricks can North-South
  take? A built-in solver plays out every line. Only deals with exactly one
  winning opening lead are kept, and the answer page shows the full line of
  play.

## Quick start

```sh
pip install -r generator/requirements.txt
python generator/tools/fetch_wordlist.py
python generator/generate.py --past 7 --days 30
```

The puzzles are now in `site/kindle4/`. To put them on a Kindle, or to test
downloading from your PC, see
[clients/kindle4/README.md](clients/kindle4/README.md#testing-locally).

## Adding a client

Create `clients/<name>/` with the device code, a README, and a `case/` folder for
its 3D-printed case. If the device's screen differs from the existing profiles,
add a display profile as described in [docs/protocol.md](docs/protocol.md#adding-a-profile).
