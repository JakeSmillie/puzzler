"""Draw the Puzzler logo: an isometric 2x2 puzzle cube with a smiley face.

Writes logo.svg (the master, plain filled shapes) and logo.png (1024 px,
black on transparent) next to this script. Tweak the constants and rerun:

    python branding/make_logo.py
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent

GAP = 0.035     # gap between tiles, as a fraction of a cube edge
ROUND = 0.045   # corner radius of the tiles
EYE_X, EYE_Y, EYE_R = 0.2, 0.06, 0.085
SMILE_Y, SMILE_R, SMILE_W, SMILE_ANGLE = 0.115, 0.25, 0.085, 26  # arc centre, radius, stroke, end angle
VIEW = 1.12     # the drawing spans -VIEW..VIEW in both directions
PNG_SIZE = 1024

# Isometric cube with unit edges, centred on the origin, y pointing down
S = math.cos(math.radians(30))
TOP, UR, LR, BOTTOM, LL, UL, CENTRE = (0, -1), (S, -0.5), (S, 0.5), (0, 1), (-S, 0.5), (-S, -0.5), (0, 0)

# Each face as (corner, u edge end, v edge end): points are corner + u*(U - corner) + v*(V - corner)
FACES = {
    "top": (UL, TOP, CENTRE),
    "left": (UL, CENTRE, LL),
    "right": (CENTRE, UR, BOTTOM),
}
# Tiles left out to make room for the face: (face, u index, v index)
MISSING = {("left", 1, 0), ("right", 0, 0)}


def tiles():
    for face, (p, pu, pv) in FACES.items():
        for i in range(2):
            for j in range(2):
                if (face, i, j) in MISSING:
                    continue
                u0, u1 = i / 2 + GAP / 2, (i + 1) / 2 - GAP / 2
                v0, v1 = j / 2 + GAP / 2, (j + 1) / 2 - GAP / 2
                corners = []
                for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                    corners.append((p[0] + u * (pu[0] - p[0]) + v * (pv[0] - p[0]),
                                    p[1] + u * (pu[1] - p[1]) + v * (pv[1] - p[1])))
                yield corners


def inset(poly, r):
    """Shrink a convex polygon by ``r``; adding back a radius-r disk gives rounded corners."""
    n = len(poly)
    area = sum(poly[k][0] * poly[(k + 1) % n][1] - poly[(k + 1) % n][0] * poly[k][1] for k in range(n))
    sign = 1 if area > 0 else -1
    lines = []
    for k in range(n):
        (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        nx, ny = -dy / length * sign, dx / length * sign   # inward normal
        lines.append(((x1 + nx * r, y1 + ny * r), (dx, dy)))
    out = []
    for k in range(n):
        (p1, d1), (p2, d2) = lines[k - 1], lines[k]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
        out.append((p1[0] + t * d1[0], p1[1] + t * d1[1]))
    return out


def rounded(poly, r, steps=10):
    """Outline of a convex polygon with corners rounded to radius ``r``, as points."""
    core = inset(poly, r)
    n = len(core)
    area = sum(core[k][0] * core[(k + 1) % n][1] - core[(k + 1) % n][0] * core[k][1] for k in range(n))
    sign = 1 if area > 0 else -1

    def outward(p, q):   # angle of the outward normal of edge p->q
        return math.atan2(-(q[0] - p[0]) * sign, (q[1] - p[1]) * sign)

    points = []
    for k in range(n):
        corner = core[k]
        a0, a1 = outward(core[k - 1], corner), outward(corner, core[(k + 1) % n])
        sweep = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        points += [(corner[0] + r * math.cos(a0 + sweep * t / steps), corner[1] + r * math.sin(a0 + sweep * t / steps))
                   for t in range(steps + 1)]
    return points


def arc(cx, cy, r, a0, a1, steps):
    return [(cx + r * math.cos(a0 + (a1 - a0) * t / steps), cy + r * math.sin(a0 + (a1 - a0) * t / steps))
            for t in range(steps + 1)]


def smile():
    """The smile as a filled band with round ends, as points."""
    a0, a1 = math.radians(SMILE_ANGLE), math.radians(180 - SMILE_ANGLE)
    w = SMILE_W / 2
    ends = [(SMILE_R * math.cos(a), SMILE_Y + SMILE_R * math.sin(a)) for a in (a0, a1)]
    return (arc(0, SMILE_Y, SMILE_R + w, a0, a1, 120)
            + arc(*ends[1], w, a1, a1 + math.pi, 24)
            + arc(0, SMILE_Y, SMILE_R - w, a1, a0, 120)
            + arc(*ends[0], w, a0 + math.pi, a0 + 2 * math.pi, 24))


def shapes():
    """Everything in the logo: ("polygon", points) and ("circle", (x, y), r)."""
    for tile in tiles():
        yield "polygon", rounded(tile, ROUND)
    for x in (-EYE_X, EYE_X):
        yield "circle", (x, EYE_Y), EYE_R
    yield "polygon", smile()


def write_svg(path):
    f = lambda v: f"{v:.4f}".rstrip("0").rstrip(".")
    parts = []
    for kind, *data in shapes():
        if kind == "polygon":
            parts.append(f'  <polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in data[0])}"/>')
        else:
            (x, y), r = data
            parts.append(f'  <circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')
    # Filled shapes only (no strokes), so it also imports cleanly into CAD tools such as OpenSCAD
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(-VIEW)} {f(-VIEW)} {f(2 * VIEW)} {f(2 * VIEW)}">\n'
        f'<title>Puzzler</title>\n<g fill="#000">\n' + "\n".join(parts) + "\n</g>\n</svg>\n",
        encoding="utf-8")


def write_png(path, size=PNG_SIZE, oversample=4):
    big = size * oversample
    scale = big / (2 * VIEW)
    xy = lambda p: ((p[0] + VIEW) * scale, (p[1] + VIEW) * scale)
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)
    for kind, *data in shapes():
        if kind == "polygon":
            draw.polygon([xy(p) for p in data[0]], fill=255)
        else:
            (x, y), r = data
            (px, py), pr = xy((x, y)), r * scale
            draw.ellipse((px - pr, py - pr, px + pr, py + pr), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    logo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    logo.putalpha(mask)
    logo.save(path, optimize=True)


if __name__ == "__main__":
    write_svg(HERE / "logo.svg")
    write_png(HERE / "logo.png")
    print("Wrote", HERE / "logo.svg", "and", HERE / "logo.png")
