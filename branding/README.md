# Branding

The Puzzler logo: an isometric 2×2 puzzle cube with a smiley face where the
two top tiles of the front edge would be.

| File | Use |
| --- | --- |
| `logo.svg` | Master vector. Filled shapes only (no strokes), so it also imports into CAD, e.g. OpenSCAD `import("logo.svg")` for embossing a case. |
| `logo.png` | 1024×1024, black on transparent. For the generator (Pillow can't read SVG) and the README. |
| `make_logo.py` | Draws both files from the same geometry. |

## Editing

Don't edit the SVG or PNG by hand. Change the constants at the top of
`make_logo.py`, such as tile gap, corner rounding, eye and smile size, and
regenerate both files from the repo root:

```sh
python branding/make_logo.py
```

## Using it

- **Colours:** black only, so it works on 1-bit e-ink panels as well as
  grayscale. Put it on a white background.
- **Size:** it reads clearly down to about 40 px. Below that, the tile gaps
  close up.
- **E-ink images:** when compositing the PNG onto a puzzle image, flatten it
  onto white first. The Kindle's `eips` doesn't support PNGs with an alpha
  channel.
