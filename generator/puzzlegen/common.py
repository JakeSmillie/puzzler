"""Shared page layout helpers for 600x800 Kindle 4 screens."""

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 600, 800
MARGIN = 30
BLACK, DARK, LIGHT, WHITE = 0, 90, 200, 255

CONTROLS = "< >  puzzle day      ^ v  puzzle type      OK  answer"

_FONTS = {
    False: ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf"],
    True: ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
}


@lru_cache(maxsize=None)
def font(size, bold=False):
    for name in _FONTS[bold]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def new_page():
    img = Image.new("L", (WIDTH, HEIGHT), WHITE)
    return img, ImageDraw.Draw(img)


def header(draw, title, day):
    """Draw the title bar and return the y coordinate below it."""
    date_text = day.strftime("%a %d %b %Y")
    room = WIDTH - 2 * MARGIN - draw.textlength(date_text, font=font(22)) - 16
    size = 38
    while size > 20 and draw.textlength(title, font=font(size, True)) > room:
        size -= 1
    draw.text((MARGIN, 62), title, font=font(size, True), fill=BLACK, anchor="ls")
    draw.text((WIDTH - MARGIN, 62), date_text, font=font(22), fill=BLACK, anchor="rs")
    draw.line((MARGIN, 78, WIDTH - MARGIN, 78), fill=BLACK, width=3)
    return 90


def footer(draw, text=None):
    """Draw the controls hint (and optional rules text). Returns the y coordinate above it."""
    draw.text((WIDTH // 2, HEIGHT - 14), CONTROLS, font=font(16), fill=DARK, anchor="ms")
    top = HEIGHT - 40
    draw.line((MARGIN, top, WIDTH - MARGIN, top), fill=LIGHT, width=1)
    if text:
        f = font(19)
        lines = wrap(draw, text, f, WIDTH - 2 * MARGIN)
        line_h = 25
        top -= 12 + line_h * len(lines)
        for i, line in enumerate(lines):
            draw.text((MARGIN, top + line_h * (i + 1) - 6), line, font=f, fill=BLACK, anchor="ls")
        top -= 8
    return top


def wrap(draw, text, f, width):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=f) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def columns(draw, items, box, bold=(), max_size=30, min_size=12):
    """Lay out ``items`` top-to-bottom in as many columns as needed, shrinking the font to fit."""
    x0, y0, x1, y1 = box
    gap = 18
    for size in range(max_size, min_size - 1, -1):
        f, fb = font(size), font(size, True)
        line_h = int(size * 1.3)
        rows = max(1, (y1 - y0) // line_h)
        ncols = math.ceil(len(items) / rows)
        col_w = max(draw.textlength(item, font=fb) for item in items) + gap
        if ncols * col_w - gap <= x1 - x0:
            break
    rows = math.ceil(len(items) / ncols)
    left = x0 + ((x1 - x0) - (ncols * col_w - gap)) / 2
    for i, item in enumerate(items):
        col, row = divmod(i, rows)
        draw.text((left + col * col_w, y0 + row * line_h), item,
                  font=fb if item in bold else f, fill=BLACK)
