"""Download the public-domain ENABLE word list used by the word wheel."""

import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/dolph/dictionary/master/enable1.txt"
DEST = Path(__file__).resolve().parent.parent / "data" / "words.txt"


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL) as response:
        DEST.write_bytes(response.read())
    print(f"Saved {sum(1 for _ in DEST.open())} words to {DEST}")


if __name__ == "__main__":
    main()
