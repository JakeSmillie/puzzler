"""Display profiles: one for each kind of client screen.

Each profile becomes a folder on the published site (see docs/protocol.md), so
a client only downloads images made for its own screen.

The current layouts are designed for 600x800 portrait. A profile with a
different size or orientation (e.g. an 800x480 ESP32 panel) will need its own
layout work in the renderers.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    name: str       # folder name on the published site
    width: int
    height: int
    controls: str   # button hints shown in the footer
    mode: str = "L"  # Pillow image mode saved to disk ("L" = 8-bit grayscale)

    def save(self, image, path):
        image.convert(self.mode).save(path, optimize=True)


PROFILES = {
    # eips wants 8-bit grayscale PNGs with no alpha channel
    "kindle4": Profile("kindle4", 600, 800, "< >  puzzle day      ^ v  puzzle type      OK  answer"),
}
