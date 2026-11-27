# Źródła danych i licencje

| Plik | Źródło | Licencja |
|---|---|---|
| `kanji_n5_n4.json` | wycinek pliku `kanji.json` z repozytorium [davidluzgouveia/kanji-data](https://github.com/davidluzgouveia/kanji-data) (dane pochodzą z KANJIDIC – Electronic Dictionary Research and Development Group – oraz z list JLPT Jonathana Wallera, tanos.co.uk) | MIT (repozytorium); KANJIDIC: CC BY-SA 4.0 |
| `kanji_n3_n1.json` | wycinek tego samego pliku `kanji.json` (stan repozytorium z 27.11.2026): kanji z `jlpt_new` 3–1, bez znaków N5–N4 | jw. |
| `jlpt_vocab_n5.csv` … `jlpt_vocab_n1.csv` | [jamsinclair/open-anki-jlpt-decks](https://github.com/jamsinclair/open-anki-jlpt-decks) (`src/n5.csv` … `src/n1.csv`), na podstawie list Jonathana Wallera (tanos.co.uk) | MIT (repozytorium) |
| `kanji_pl.tsv`, `vocab_n5_pl.tsv` … `vocab_n1_pl.tsv` | polskie tłumaczenia przygotowane na potrzeby projektu Nihongo SRS | MIT (jak projekt) |
| `phrasebook.py`, `themes.py` | rozmówki i słownictwo tematyczne napisane na potrzeby projektu Nihongo SRS | MIT (jak projekt) |
| `kana.py` | tablice kany wygenerowane w kodzie | MIT (jak projekt) |
| `static/strokes/*.json` | kolejność kresek z [KanjiVG](https://kanjivg.tagaini.net/) © Ulrich Apel (wydanie r20250816, plik `kanjivg-20250816-main.zip`), przekonwertowana skryptem `build_strokes.py`: tylko znaki talii systemowych i wszystkie znaki kana | CC BY-SA 3.0 |

Atrybucja jest wyświetlana w aplikacji (stopka, strona „O aplikacji” i okno „Jak pisać?”).
