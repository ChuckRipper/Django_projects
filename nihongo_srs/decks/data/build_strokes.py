"""Convert KanjiVG SVG files into small JSON files used by the stroke-order player.

Development tool, not run by the application. Usage (from the nihongo_srs folder):

    python decks/data/build_strokes.py <path to extracted kanjivg "kanji" folder>

Writes static/strokes/<code point hex>.json for every character used by the system
decks and every hiragana/katakana character. Each file holds the stroke paths in
drawing order and the positions of the stroke numbers (KanjiVG 109x109 coordinates).
KanjiVG © Ulrich Apel, CC BY-SA 3.0 — see decks/data/SOURCES.md.
"""

import json
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUTPUT = BASE / "static" / "strokes"
PATH_RE = re.compile(r'<path id="kvg:[0-9a-f]+-s(\d+)"[^>]*?\sd="([^"]+)"')
NUMBER_RE = re.compile(r'<text transform="matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)">(\d+)</text>')


def wanted_characters() -> set[str]:
    sys.path.insert(0, str(BASE))
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    from decks.models import Card

    chars = {chr(cp) for cp in range(0x3041, 0x3097)} | {chr(cp) for cp in range(0x30A1, 0x30FB)} | {"ー"}
    for front in Card.objects.filter(deck__owner__isnull=True).values_list("front", flat=True):
        chars.update(front)
    return {c for c in chars if not c.isascii() and not c.isspace()}


def convert(svg: str) -> dict:
    strokes = sorted((int(n), d) for n, d in PATH_RE.findall(svg))
    numbers = sorted((int(n), float(x), float(y)) for x, y, n in NUMBER_RE.findall(svg))
    return {"s": [d for _, d in strokes], "n": [[x, y] for _, x, y in numbers]}


def main(source: Path) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    missing = []
    for char in sorted(wanted_characters()):
        svg_file = source / f"{ord(char):05x}.svg"
        if not svg_file.exists():
            missing.append(char)
            continue
        data = convert(svg_file.read_text(encoding="utf-8"))
        (OUTPUT / f"{ord(char):05x}.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    written = len(list(OUTPUT.glob("*.json")))
    print(f"Zapisano {written} plików. Brak w KanjiVG: {''.join(missing) or '—'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
