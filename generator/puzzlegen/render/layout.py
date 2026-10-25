"""Shared page layout: fonts, header, footer and word columns."""

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MARGIN = 30
BLACK, DARK, LIGHT, WHITE = 0, 90, 200, 255
LOGO = Path(__file__).resolve().parents[3] / "branding" / "logo.png"
LOGO_SIZE = 46

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


@lru_cache(maxsize=None)
def logo(size):
    """The logo flattened onto white (e-ink images have no alpha), or None if it's missing."""
    if not LOGO.exists():
        return None
    image = Image.open(LOGO).convert("RGBA")
    flat = Image.new("RGBA", image.size, "white")
    flat.alpha_composite(image)
    return flat.convert("L").resize((size, size), Image.LANCZOS)


class Page:
    """A blank screen for one display profile."""

    def __init__(self, profile):
        self.profile = profile
        self.width, self.height = profile.width, profile.height
        self.image = Image.new("L", (self.width, self.height), WHITE)
        self.draw = ImageDraw.Draw(self.image)

    def header(self, title, day):
        """Draw the title bar and return the y coordinate below it."""
        draw = self.draw
        left = MARGIN
        mark = logo(LOGO_SIZE)
        if mark:
            self.image.paste(mark, (left - 4, 70 - LOGO_SIZE))
            left += LOGO_SIZE + 6
        date_text = day.strftime("%a %d %b %Y")
        room = self.width - left - MARGIN - draw.textlength(date_text, font=font(22)) - 16
        size = 38
        while size > 20 and draw.textlength(title, font=font(size, True)) > room:
            size -= 1
        draw.text((left, 62), title, font=font(size, True), fill=BLACK, anchor="ls")
        draw.text((self.width - MARGIN, 62), date_text, font=font(22), fill=BLACK, anchor="rs")
        draw.line((MARGIN, 78, self.width - MARGIN, 78), fill=BLACK, width=3)
        return 90

    def footer(self, text=None):
        """Draw the controls hint (and optional rules text). Returns the y coordinate above it."""
        draw = self.draw
        draw.text((self.width // 2, self.height - 14), self.profile.controls, font=font(16), fill=DARK, anchor="ms")
        top = self.height - 40
        draw.line((MARGIN, top, self.width - MARGIN, top), fill=LIGHT, width=1)
        if text:
            f = font(19)
            lines = wrap(draw, text, f, self.width - 2 * MARGIN)
            line_h = 25
            top -= 12 + line_h * len(lines)
            for i, line in enumerate(lines):
                draw.text((MARGIN, top + line_h * (i + 1) - 6), line, font=f, fill=BLACK, anchor="ls")
            top -= 8
        return top

    def columns(self, items, box, bold=(), max_size=30, min_size=12):
        """Lay out ``items`` top-to-bottom in as many columns as needed, shrinking the font to fit."""
        draw = self.draw
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
