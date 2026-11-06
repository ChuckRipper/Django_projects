"""Card sources (Adapter pattern).

Every external format - an uploaded CSV, the KANJIDIC-based kanji file, the JLPT
vocabulary lists - is adapted to one common interface: an iterable of
``CardData``. Import logic (decks.services.import_cards) and the ``load_data``
command only ever talk to ``CardSource``, so adding a new format means writing
one new adapter class and nothing else.
"""

import csv
import io
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .data.kana import to_katakana

KANJI_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclass
class CardData:
    front: str
    back: str
    reading: str = ""
    example: str = ""
    onyomi: str = ""
    kunyomi: str = ""
    stroke_count: int | None = None
    meaning_en: str = ""


@dataclass
class SourceError:
    line: int
    message: str


class CardSource(ABC):
    """Common interface of all card sources."""

    def __init__(self):
        self.errors: list[SourceError] = []

    @abstractmethod
    def __iter__(self) -> Iterator[CardData]:
        """Yield cards; problems with single rows are collected in ``self.errors``."""


# --- user upload ------------------------------------------------------------------

class CsvCardSource(CardSource):
    """CSV uploaded by a user. Header row required; Polish or English column names.

    Required columns: ``front``/``przod`` and ``back``/``tyl``. Optional: reading,
    example, onyomi, kunyomi, stroke_count (or their Polish names). Delimiter
    (comma, semicolon or tab) is detected automatically.
    """

    COLUMN_ALIASES = {
        "front": {"front", "przod", "przód", "slowo", "słowo", "kanji", "znak"},
        "back": {"back", "tyl", "tył", "znaczenie", "meaning", "tlumaczenie", "tłumaczenie"},
        "reading": {"reading", "odczyt", "czytanie", "kana"},
        "example": {"example", "przyklad", "przykład"},
        "onyomi": {"onyomi", "on"},
        "kunyomi": {"kunyomi", "kun"},
        "stroke_count": {"stroke_count", "strokes", "kreski", "liczba_kresek"},
        "meaning_en": {"meaning_en", "english", "angielski"},
    }
    MAX_ROWS = 2000

    def __init__(self, text: str):
        super().__init__()
        self.text = text.lstrip("﻿")  # Excel adds a BOM to UTF-8 CSV files

    @classmethod
    def from_upload(cls, uploaded_file):
        raw = uploaded_file.read()
        for encoding in ("utf-8-sig", "cp1250"):
            try:
                return cls(raw.decode(encoding))
            except UnicodeDecodeError:
                continue
        source = cls("")
        source.errors.append(SourceError(0, "Nie udało się odczytać pliku: zapisz go jako CSV w kodowaniu UTF-8."))
        return source

    def _column_map(self, header):
        mapping = {}
        for index, name in enumerate(header):
            key = name.strip().lower()
            for target, aliases in self.COLUMN_ALIASES.items():
                if key in aliases and target not in mapping:
                    mapping[target] = index
        return mapping

    def __iter__(self):
        if not self.text.strip():
            if not self.errors:
                self.errors.append(SourceError(0, "Plik jest pusty."))
            return
        try:
            dialect = csv.Sniffer().sniff(self.text[:2048], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(io.StringIO(self.text), dialect)
        header = next(reader, [])
        columns = self._column_map(header)
        missing = [name for name in ("front", "back") if name not in columns]
        if missing:
            self.errors.append(SourceError(
                1, "Brak wymaganych kolumn: front/przod i back/tyl (pierwszy wiersz musi zawierać nagłówki).",
            ))
            return

        for line_no, row in enumerate(reader, start=2):
            if line_no - 1 > self.MAX_ROWS:
                self.errors.append(SourceError(line_no, f"Przekroczono limit {self.MAX_ROWS} wierszy."))
                return
            if not any(cell.strip() for cell in row):
                continue

            def cell(name, current_row=row):
                index = columns.get(name)
                return current_row[index].strip() if index is not None and index < len(current_row) else ""

            front, back = cell("front"), cell("back")
            if not front or not back:
                self.errors.append(SourceError(line_no, "Puste pole przodu lub tyłu karty."))
                continue
            strokes = cell("stroke_count")
            if strokes and not strokes.isdigit():
                self.errors.append(SourceError(line_no, f"Liczba kresek musi być liczbą („{strokes}”)."))
                continue
            yield CardData(
                front=front, back=back, reading=cell("reading"), example=cell("example"),
                onyomi=cell("onyomi"), kunyomi=cell("kunyomi"),
                stroke_count=int(strokes) if strokes else None, meaning_en=cell("meaning_en"),
            )


# --- bundled dictionaries ------------------------------------------------------------

def _read_tsv(path: Path, key_columns: int = 1):
    """Return {key: last column} from a TSV file with a header row."""
    result = {}
    with open(path, encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > key_columns:
                result[tuple(parts[:key_columns]) if key_columns > 1 else parts[0]] = parts[-1]
    return result


@dataclass
class KanjiDataSource(CardSource):
    """Adapter for the KANJIDIC-based JSON (davidluzgouveia/kanji-data format)."""

    path: Path
    jlpt_level: int
    translations_path: Path | None = None
    examples: dict = field(default_factory=dict)

    def __post_init__(self):
        super().__init__()

    def __iter__(self):
        with open(self.path, encoding="utf-8") as handle:
            data = json.load(handle)
        polish = _read_tsv(self.translations_path) if self.translations_path else {}
        entries = [(kanji, info) for kanji, info in data.items() if info.get("jlpt_new") == self.jlpt_level]
        entries.sort(key=lambda item: (item[1].get("freq") or 99999, item[0]))  # most frequent first
        for kanji, info in entries:
            meaning_en = ", ".join(info.get("meanings") or [])
            yield CardData(
                front=kanji,
                back=polish.get(kanji) or meaning_en,
                meaning_en=meaning_en,
                onyomi="、".join(to_katakana(r) for r in info.get("readings_on") or []),
                kunyomi="、".join(info.get("readings_kun") or []),
                stroke_count=info.get("strokes"),
                example=self.examples.get(kanji, ""),
            )


@dataclass
class JlptVocabSource(CardSource):
    """Adapter for the JLPT vocabulary CSV (open-anki-jlpt-decks format).

    Cleans up the source notation: alternative spellings (``足; 脚``), the ``～``
    affix marker in readings and notes such as ``(する)``. Entries that share the
    same written form are merged into one card.
    """

    path: Path
    translations_path: Path | None = None

    def __post_init__(self):
        super().__init__()

    @staticmethod
    def _clean_reading(reading: str) -> str:
        reading = reading.replace("(〜を)", "").strip()
        return reading

    def __iter__(self):
        polish = _read_tsv(self.translations_path, key_columns=2) if self.translations_path else {}
        merged: dict[str, CardData] = {}
        with open(self.path, encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                expression, reading = row["expression"].strip(), row["reading"].strip()
                meaning_en = row["meaning"].strip()
                meaning = polish.get((expression, reading)) or meaning_en
                forms = [form.strip() for form in expression.split(";") if form.strip()]
                front = forms[0]
                alternatives = "、".join(forms[1:])
                reading = self._clean_reading(reading)
                if not KANJI_RE.search(front):
                    reading = ""  # a kana-only word needs no separate reading
                if front in merged:
                    card = merged[front]
                    if reading and reading not in card.reading:
                        card.reading = f"{card.reading}; {reading}" if card.reading else reading
                    if meaning not in card.back:
                        card.back = f"{card.back} / {meaning}"[:255]
                        card.meaning_en = f"{card.meaning_en} / {meaning_en}"[:255]
                    continue
                merged[front] = CardData(
                    front=front, back=meaning[:255], reading=reading, meaning_en=meaning_en[:255],
                    example=f"Inny zapis: {alternatives}" if alternatives else "",
                )
        yield from merged.values()
