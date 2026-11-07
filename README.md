<p align="center"><img src="nihongo_srs/static/img/logo.svg" alt="Nihongo SRS" height="72"></p>

# Nihongo SRS

Aplikacja webowa w Django do nauki języka japońskiego metodą **powtórek rozłożonych w czasie** (SRS, *spaced repetition system*). Użytkownik uczy się kart z sylabariuszami kana, słownictwem i kanji na poziomach JLPT N5–N4, ocenia, jak dobrze pamiętał odpowiedź, a algorytm SM-2 sam planuje kolejną powtórkę, osobno dla każdego użytkownika i każdej karty.

> Projekt zaliczeniowy z przedmiotu *Aplikacje internetowe w Django* (mgr inż. Marek Foryś), WSB Merito Chorzów, Informatyka II stopnia, specjalność Programista Python.
> Autor: Cezary Kalinowski

**Status:** 🚧 w budowie. Etapy M1 i M2 gotowe, M3 w toku, patrz [Plan prac](#plan-prac).

---

## Spis treści

1. [Funkcje](#funkcje)
2. [Technologie](#technologie)
3. [Architektura](#architektura)
4. [Model danych](#model-danych)
5. [Algorytm powtórek (SM-2)](#algorytm-powtórek-sm-2)
6. [Dane słownikowe i licencje](#dane-słownikowe-i-licencje)
7. [Identyfikacja wizualna](#identyfikacja-wizualna)
8. [Wzorce projektowe](#wzorce-projektowe)
9. [REST API (Swagger + JWT)](#rest-api-swagger--jwt)
10. [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
11. [Testy](#testy)
12. [Wdrożenie (PythonAnywhere)](#wdrożenie-pythonanywhere)
13. [Workflow Git](#workflow-git)
14. [Plan prac](#plan-prac)
15. [Licencja](#licencja)

---

## Funkcje

### Zakres podstawowy (MVP)

| Moduł | Funkcje |
|---|---|
| **Konta** | rejestracja, logowanie (login bez rozróżniania wielkości liter), wylogowanie; profil z dziennym limitem nowych kart i celem dziennym |
| **Talie i karty** | talie systemowe (tylko do odczytu) i własne talie użytkownika; pełny CRUD talii i kart; wyszukiwanie oraz filtry po typie i poziomie JLPT |
| **Nauka** | sesja powtórek: kolejka (zaległe powtórki + nowe karty do dziennego limitu) → przód karty → odsłonięcie odpowiedzi → ocena **Znów / Trudne / Dobre / Łatwe** → wyliczenie następnego terminu |
| **Kanji** | znaczenie, odczyty on'yomi i kun'yomi, liczba kresek, poziom JLPT, przykładowe słówka |
| **Statystyki** | wykres powtórek z 30 dni (poprawne / „Znów”), heatmapa aktywności z 20 tygodni, rozkład ocen, nadchodzące powtórki na 7 dni, skuteczność i średni czas odpowiedzi w każdej talii |
| **Import i eksport** | wczytywanie kart z pliku CSV (polskie lub angielskie nagłówki, automatyczny separator, raport błędów z numerami wierszy), eksport talii do CSV w tym samym formacie |
| **Panel admina** | zarządzanie taliami systemowymi i kartami, podgląd historii powtórek |
| **Interfejs** | po polsku, responsywny (sprawdzony od 390 px), motyw jasny i ciemny z przełącznikiem, własne strony błędów 400, 403, 404, 405 i 500 (w API odpowiedzi JSON), skróty klawiszowe (nauka, motyw, nawigacja, formularze; lista pod klawiszem `?`, podpowiedzi w dymkach), strona „O aplikacji” z instrukcją i źródłami danych |
| **REST API** | uwierzytelnianie JWT, talie, karty, kolejka nauki, zapis oceny, statystyki; dokumentacja Swagger UI generowana automatycznie |

### Rozszerzenia

| Rozszerzenie | Stan |
|---|---|
| **„Jak pisać?”**: animowana kolejność kresek dla kana i kanji (także słówek, znak po znaku): odtwarzanie, pauza, krok po kroku, tempo, numery kresek; w nauce (przycisk lub `K`) i przy każdej karcie w talii | ✅ |
| tryb „wpisz odpowiedź” z konwersją romaji → kana w trakcie pisania | ⏳ |
| udostępnianie własnych talii innym użytkownikom | ⏳ |
| reset hasła e-mailem | ⏳ |

### Materiał na start

| Zestaw | Zawartość (przybliżona) |
|---|---|
| Hiragana | 46 znaków podstawowych + dakuten / handakuten + połączenia (yōon) |
| Katakana | jak wyżej |
| Kanji N5 | 79 znaków, znaczenia po polsku (+ angielskie), odczyty on/kun, kreski, przykładowe słówka |
| Kanji N4 | 166 znaków, jw. |
| Słownictwo N5 | 709 słów, znaczenia po polsku (+ angielskie) |
| Słownictwo N4 | 666 słów, znaczenia po polsku (+ angielskie) |

Razem: 10 talii systemowych, 1828 kart.

---

## Technologie

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.13, **Django 5.2 LTS** |
| Baza danych | SQLite |
| Frontend | szablony Django, Bootstrap 5.3 (motyw jasny i ciemny przez `data-bs-theme`), Bootstrap Icons |
| REST API | Django REST Framework, drf-spectacular (OpenAPI 3 / Swagger UI), djangorestframework-simplejwt (JWT) |
| Wykresy | Chart.js |
| Wprowadzanie kana | WanaKana (rozszerzenie) |
| Testy | `django.test` (`TestCase`, `SimpleTestCase`, klient testowy), `rest_framework.test.APITestCase` |
| Hosting | PythonAnywhere |

Konwencje: kod, nazwy, komentarze i docstringi są **po angielsku**, interfejs użytkownika **po polsku**.

---

## Architektura

Projekt Django (`config/`) podzielony na aplikacje o jednej odpowiedzialności:

| Aplikacja | Odpowiedzialność |
|---|---|
| `accounts` | rejestracja, logowanie, profil i ustawienia użytkownika |
| `decks` | talie i karty, CRUD, import CSV, komenda ładowania danych |
| `study` | algorytm SM-2 (`srs.py`, czysta logika bez zależności od widoków), budowa kolejki, sesja nauki |
| `api` | REST API: serializery, uprawnienia, widoki DRF, routing, Swagger |
| `core` | strona główna i pulpit, obsługa błędów HTTP (strony HTML i JSON dla API), tag szablonu do formularzy Bootstrap |
| `stats` | statystyki i wykresy na podstawie historii powtórek (agregacje w `stats/services.py`) |

### Planowana struktura repozytorium

```
Django_projects/
├── README.md
├── LICENSE
├── .gitignore
└── nihongo_srs/
    ├── manage.py
    ├── requirements.txt
    ├── config/                 # settings.py, urls.py, wsgi.py
    ├── core/                   # strona główna, pulpit, obsługa błędów, templatetags/
    ├── accounts/               # Profile, rejestracja, profil, signals.py (Observer)
    ├── decks/                  # Deck, Card, CRUD, mixins.py (uprawnienia)
    │   ├── sources.py          # adaptery źródeł kart (Adapter)
    │   ├── factories.py        # tworzenie kart wg typu talii (Metoda wytwórcza)
    │   ├── services.py         # import i eksport CSV
    │   ├── data/               # kana.py, kanji i słownictwo N5–N4, tłumaczenia, SOURCES.md
    │   └── management/commands/load_data.py
    ├── stats/                  # statystyki: services.py, widok, szablon
    ├── study/
    │   ├── srs.py              # algorytmy powtórek (Strategy)
    │   ├── services.py         # kolejka, zapis oceny, statystyki (Service Layer)
    │   └── views.py            # sesja nauki
    ├── api/                    # DRF: serializers, permissions, views, urls
    ├── templates/              # base.html + szablony stron
    └── static/                 # css/theme.css (paleta, motywy), js/, strokes/ (kolejność kresek, KanjiVG)
```

---

## Model danych

| Model | Najważniejsze pola | Uwagi |
|---|---|---|
| `Deck` | `name`, `description`, `kind` (kana / vocabulary / kanji), `jlpt_level`, `owner`, `created_at` | `owner = NULL` → talia systemowa |
| `Card` | `deck`, `front`, `back`, `meaning_en`, `reading`, `example`, `onyomi`, `kunyomi`, `stroke_count`, `order` | pola kanji wypełniane tylko dla kart kanji; `meaning_en` – oryginalne znaczenie ze słownika |
| `ReviewState` | `user`, `card`, `ease_factor`, `interval_days`, `repetitions`, `lapses`, `due_at`, `introduced_at` | unikalna para `user` + `card`; stan nauki konkretnej osoby |
| `ReviewLog` | `user`, `card`, `rating`, `reviewed_at`, `response_ms`, `interval_before`, `interval_after` | pełna historia, źródło statystyk |
| `Profile` | `user` (1:1), `new_cards_per_day`, `daily_goal` | ustawienia nauki |

Karty są wspólne, a postęp jest prywatny: ta sama karta systemowa ma osobny `ReviewState` dla każdego użytkownika.

---

## Algorytm powtórek (SM-2)

Wariant algorytmu SuperMemo SM-2 z czterema ocenami:

| Ocena | 1. odpowiedź | 2. odpowiedź | Kolejne | `ease` |
|---|---|---|---|---|
| **Znów** | karta wraca po 10 min, postęp od zera, `lapses + 1` | jw. | jw. | −0,20 |
| **Trudne** | 1 dzień | 4 dni | interwał × 1,2 | −0,15 |
| **Dobre** | 1 dzień | 6 dni | interwał × `ease` | bez zmian |
| **Łatwe** | 3 dni | 8 dni | interwał × `ease` × 1,3 | +0,15 |

- Początkowy `ease` = 2,5, minimalny = 1,3; poprawna odpowiedź nigdy nie daje interwału krótszego niż 1 dzień.
- Kolejka: najpierw zaległe powtórki (`due_at ≤ teraz`), potem nowe karty do dziennego limitu z profilu.
- Karta jest uznawana za opanowaną przy interwale ≥ 21 dni.
- Alternatywnie dostępny jest system pudełek Leitnera (`SRS_ALGORITHM = "leitner"` w `settings.py`).

Logika znajduje się w module `study/srs.py` jako czyste funkcje, więc da się ją testować jednostkowo, niezależnie od bazy i widoków.

---

## Dane słownikowe i licencje

| Źródło | Wykorzystanie | Licencja |
|---|---|---|
| Kana | generowane w kodzie (`decks/data/kana.py`) | – |
| [davidluzgouveia/kanji-data](https://github.com/davidluzgouveia/kanji-data), na podstawie KANJIDIC (EDRDG) i list JLPT Jonathana Wallera | kanji N5–N4: znaczenia, odczyty, liczba kresek, poziom | MIT; KANJIDIC: CC BY-SA 4.0 |
| [jamsinclair/open-anki-jlpt-decks](https://github.com/jamsinclair/open-anki-jlpt-decks), na podstawie list Jonathana Wallera | słownictwo N5–N4 | MIT |
| [KanjiVG](https://kanjivg.tagaini.net/) (Ulrich Apel) | kolejność kresek kana i kanji (`static/strokes/`, generowane skryptem `decks/data/build_strokes.py`) | CC BY-SA 3.0 |
| Tłumaczenia na polski | 245 kanji oraz 709 słówek N5 i 666 słówek N4, przygotowane na potrzeby projektu | MIT |

Pliki źródłowe leżą w `decks/data/`, a szczegóły opisuje `decks/data/SOURCES.md`. Atrybucja jest wyświetlana w stopce aplikacji.

---

## Identyfikacja wizualna

- **Logo** ✅: znak 日 + napis 日本語 (indygo) i „SRS” (cynober); `static/img/logo.svg` na jasne tło i `logo-light.svg` na ciemne (pasek nawigacji). Napisy zamienione na ścieżki (font Noto Sans CJK JP Bold, licencja SIL OFL), więc logo wygląda tak samo bez względu na zainstalowane fonty.
- **Favicon** ✅: znak 日 (pierwszy znak słowa 日本語) na tle indygo, środkowa kreska w kolorze cynobru; `static/img/favicon.svg` + `favicon.ico` (16/32/48 px) + `apple-touch-icon.png` (180 px). Znak narysowany kształtami, więc nie zależy od fontów systemu.
- **Kolejność prac:** najpierw paleta kolorów aplikacji (zmienne CSS), logo projektowane na końcu w kolorach przewodnich.
- **Motyw jasny i ciemny** z przełącznikiem; wybór zapamiętywany w przeglądarce.
- **Kolory wykresów** (poprawne `#2f6db3` / „Znów” `#d1495b`, w trybie ciemnym `#5285cc` / `#dc5a6c`) sprawdzone walidatorem palety pod kątem daltonizmu i kontrastu. Heatmapa używa jednej barwy (indygo) w pięciu stopniach jasności. Każdy wykres ma legendę i widok tabeli.

Propozycja palety (do zatwierdzenia):

| Rola | Kolor | Nawiązanie |
|---|---|---|
| Główny | indygo `#1f3a5f` | *ai-iro*, tradycyjny japoński błękit indygo |
| Akcent | cynober `#d1495b` | *shu-iro*, kolor bram torii |
| Tło jasne | `#faf7f2` | papier washi |
| Tło ciemne | `#1b1d21` | tusz *sumi* |

---

## Wzorce projektowe

| Wzorzec | Gdzie | Po co |
|---|---|---|
| **Strategia** (Strategy) | `study/srs.py`: interfejs `SchedulingStrategy`, implementacje `SM2Strategy` i `LeitnerStrategy`, wybór przez `get_strategy()` | algorytm powtórek można wymienić jednym ustawieniem, bez zmian w widokach, API i serwisach |
| **Warstwa serwisów** (Service Layer) | `study/services.py` | ta sama logika (kolejka, limity, zapis oceny, statystyki) obsługuje widoki HTML i REST API, bez duplikacji |
| **Obserwator** (Observer) | `accounts/signals.py`: sygnał `post_save` | automatyczne utworzenie profilu dla każdego nowego użytkownika, niezależnie od tego, czy konto powstało przez stronę, API czy panel admina |
| **Metoda szablonowa** (Template Method) | widoki klasowe (`CreateView`, `UpdateView`, `DeleteView`) | szkielet obsługi żądania jest w klasie bazowej Django, a widoki nadpisują tylko wybrane kroki (`get_queryset`, `form_valid`, `get_success_url`) |
| **Domieszki** (Mixins) | `decks/mixins.py`, `LoginRequiredMixin` | wielokrotnego użytku reguły dostępu: edytować można tylko własne talie i karty |
| **Adapter** | `decks/sources.py`: `CsvCardSource`, `KanjiDataSource`, `JlptVocabSource` → wspólny interfejs `CardSource` zwracający `CardData` | trzy różne formaty (plik użytkownika, JSON z KANJIDIC, listy JLPT) trafiają do jednej funkcji importu; nowy format to jedna nowa klasa |
| **Metoda wytwórcza** (Factory Method) | `decks/factories.py`: `CardFactory.for_deck()` → `KanaCardFactory`, `VocabularyCardFactory`, `KanjiCardFactory` | każdy typ talii ma własne reguły pól i walidacji (np. karta kanji to dokładnie jeden znak); import nie musi sprawdzać typu talii |

---

## REST API (Swagger + JWT)

Dokumentacja interaktywna: **`/api/docs/`** (Swagger UI) · alternatywnie `/api/redoc/` · schemat OpenAPI: `/api/schema/`

**Jak zalogować się w Swaggerze:**

1. Otwórz `/api/docs/` → `POST /api/auth/token/` → *Try it out* → podaj `username` i `password` → *Execute*.
2. Skopiuj wartość `access` z odpowiedzi.
3. Kliknij **Authorize** (kłódka u góry), wklej token i zatwierdź. Od teraz wszystkie żądania idą z nagłówkiem `Authorization: Bearer <token>`.
4. Token `access` jest ważny 60 minut; nowy pobierzesz z `refresh` przez `POST /api/auth/token/refresh/` (ważny 7 dni).

Zalogowany w przeglądarce użytkownik może korzystać ze Swaggera także bez tokenu (sesja Django).

| Metoda | Endpoint | Opis |
|---|---|---|
| POST | `/api/auth/register/` | rejestracja (bez uwierzytelnienia) |
| POST | `/api/auth/token/` | logowanie → tokeny `access` i `refresh` |
| POST | `/api/auth/token/refresh/` | nowy token `access` |
| GET, POST | `/api/decks/` | lista talii (systemowe + własne), utworzenie własnej |
| GET, PUT, PATCH, DELETE | `/api/decks/{id}/` | szczegóły; zmiany tylko we własnych taliach |
| GET | `/api/decks/{id}/cards/` | karty w talii |
| POST | `/api/decks/{id}/import/` | import kart z CSV (`multipart/form-data`: `file`, `update_existing`) → raport |
| GET | `/api/decks/{id}/export/` | eksport talii do CSV |
| GET, POST | `/api/cards/` | lista kart, dodanie karty do własnej talii |
| GET, PUT, PATCH, DELETE | `/api/cards/{id}/` | szczegóły; zmiany tylko we własnych taliach |
| GET | `/api/study/queue/?deck=&limit=` | kolejka nauki |
| POST | `/api/study/review/` | zapis oceny `{card, rating (0–3), response_ms}` → nowy stan karty |
| GET | `/api/stats/summary/` | podsumowanie: do powtórki, nowe, seria, skuteczność, cel dzienny |
| GET | `/api/stats/daily/?days=` | powtórki dziennie (poprawne / „Znów”) |

---

## Instalacja i uruchomienie

> Sekcja będzie uzupełniana wraz z postępem prac.

Wymagania: Python 3.10+ (zalecany 3.13), Git.

```powershell
git clone https://github.com/ChuckRipper/Django_projects.git
cd Django_projects
py -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
python -m pip install -r nihongo_srs\requirements.txt
cd nihongo_srs
python manage.py migrate
python manage.py load_data            # 10 talii systemowych: kana, kanji i słownictwo N5–N4
python manage.py createsuperuser
python manage.py runserver
```

Aplikacja: http://127.0.0.1:8000/ · panel admina: http://127.0.0.1:8000/admin/ · API: http://127.0.0.1:8000/api/docs/

Jeśli Windows zgłasza „You don't have permission to access that port”, uruchom serwer na innym porcie, np. `python manage.py runserver 8765`.

---

## Testy

```powershell
cd nihongo_srs
python manage.py test
```

Obecnie **82 testy**:

| Plik | Zakres |
|---|---|
| `study/tests.py` | algorytm SM-2 (wszystkie oceny, granice `ease`, kolejne interwały), Leitner, wybór strategii; kolejka i dzienny limit (także przy powtórkach z datą wsteczną), kolejność zaległe → nowe, powrót karty po „Znów”, zapis stanu i historii, konfigurowalny algorytm, izolacja cudzych talii, seria dni i skuteczność, postęp talii; widok sesji nauki |
| `decks/tests.py` | `load_data` (liczby talii i kart, idempotentność, treść kart kanji, czyszczenie słownictwa), adapter CSV (polskie nagłówki, BOM, błędne wiersze z poprawnymi numerami), polskie znaczenia N4, dane kolejności kresek dla wszystkich znaków talii systemowych (zgodność liczby kresek KanjiVG z KANJIDIC), fabryki kart, import z aktualizacją, eksport ↔ import, widoki importu i eksportu, uprawnienia, unikalne nazwy, filtry |
| `accounts/tests.py` | rejestracja, profil, strony publiczne, „O aplikacji”, favicon, logowanie bez rozróżniania wielkości liter, blokada loginów różniących się tylko wielkością liter, walidacja limitów w profilu |
| `stats/tests.py` | powtórki dziennie, poziomy heatmapy, rozkład ocen, etapy kart, skuteczność i czas w taliach, nadchodzące powtórki, strona statystyk (z danymi i bez) |
| `api/tests.py` | uwierzytelnienie i JWT (także bez rozróżniania wielkości liter), rejestracja, uprawnienia do talii, CRUD, kolejka i ocena, import i eksport CSV, statystyki, Swagger |
| `core/tests.py` | strony błędów 400, 403, 404, 500 (HTML) i ich odpowiedniki JSON w API, nieprawidłowy nagłówek Host, błąd CSRF, 401 w API, przekierowanie do logowania, 405 z nagłówkiem `Allow`; okno skrótów klawiszowych |

---

## Wdrożenie (PythonAnywhere)

| Ustawienie | Wartość |
|---|---|
| Adres | https://czarodziej.pythonanywhere.com/ |
| Source code / Working directory | `/home/Czarodziej/Django_projects/nihongo_srs` |
| Virtualenv | `/home/Czarodziej/venv_django` |
| Static files | `/static/` → `/home/Czarodziej/Django_projects/nihongo_srs/staticfiles` |

Konfiguracja produkcyjna pochodzi ze zmiennych środowiskowych ustawianych w pliku WSGI na PythonAnywhere (poza repozytorium):

| Zmienna | Wartość na produkcji | Znaczenie |
|---|---|---|
| `DJANGO_DEBUG` | `False` | wyłącza tryb deweloperski i włącza ustawienia bezpieczeństwa (HTTPS, bezpieczne ciasteczka, HSTS) |
| `DJANGO_SECRET_KEY` | losowy ciąg (np. `python -c "import secrets; print(secrets.token_urlsafe(50))"`) | wymagany przy `DJANGO_DEBUG=False`; bez niego aplikacja nie wystartuje |
| `DJANGO_HTTPS` | nie ustawiać | tylko lokalnie: `False` pozwala uruchomić konfigurację produkcyjną po zwykłym HTTP (np. żeby obejrzeć strony błędów) |
| `DJANGO_ALLOWED_HOSTS` | opcjonalnie, po przecinku | dodatkowe domeny (`*.pythonanywhere.com` jest dozwolone domyślnie) |

Plik WSGI (`/var/www/czarodziej_pythonanywhere_com_wsgi.py`):

```python
import os
import sys

path = "/home/Czarodziej/Django_projects/nihongo_srs"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_DEBUG"] = "False"
os.environ["DJANGO_SECRET_KEY"] = "<wygenerowany sekret>"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Pierwsze wdrożenie (konsola Bash na PythonAnywhere):

```bash
git clone https://github.com/ChuckRipper/Django_projects.git
source ~/venv_django/bin/activate
pip install -r ~/Django_projects/nihongo_srs/requirements.txt
cd ~/Django_projects/nihongo_srs
python manage.py migrate
python manage.py load_data
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Aktualizacja: `git pull` → `migrate` → `collectstatic --noinput` → przycisk **Reload** w zakładce Web.

`python manage.py check --deploy` (z ustawionymi zmiennymi produkcyjnymi) nie zgłasza ostrzeżeń. Dwa sprawdzenia HSTS (subdomeny, preload) są świadomie wyciszone, bo aplikacja działa we współdzielonej domenie `pythonanywhere.com`.

Darmowe konto obsługuje jedną aplikację webową, więc wdrożenie projektu odbywa się po ocenie zadań, które zajmują ją wcześniej.

---

## Workflow Git

- Gałąź `master` jest chroniona, zmiany trafiają do niej wyłącznie przez Pull Request.
- Praca na gałęziach `feature/<opis>`, np. `feature/srs-algorithm`, `feature/kana-decks`.

```powershell
git switch master
git pull
git switch -c feature/<opis>
# ... zmiany ...
git add .
git commit -m "<opis zmian>"
git push -u origin feature/<opis>
```

Następnie: Pull Request na GitHubie → merge → `git switch master` → `git pull`.

---

## Plan prac

| Kamień milowy | Termin | Zakres | Status |
|---|---|---|---|
| **M0: Specyfikacja** | 05.11 | README, decyzje projektowe | ✅ |
| **M1: Fundament** | 14.11 | szkielet projektu, konta, modele, talie kana, sesja nauki z SM-2, paleta i motyw ciemny, REST API ze Swaggerem i JWT, favicon, 45 testów | ✅ |
| **M2: Treść i statystyki** | 28.11 | kanji i słownictwo N5–N4 (1600+ kart, polskie tłumaczenia N5), import/eksport CSV (Adapter, Metoda wytwórcza), statystyki z wykresami i heatmapą, logowanie bez rozróżniania wielkości liter, 70 testów | ✅ |
| **M3: Dopracowanie** | 12.12 | ✅ logo, ✅ strona „O aplikacji”, ✅ strony błędów 400–500 (HTML i JSON), ✅ ustawienia produkcyjne, ✅ widok mobilny; ✅ polskie znaczenia N4, ✅ scenariusz testów manualnych, ✅ skróty klawiszowe, ✅ kolejność kresek; ⏳ pozostałe rozszerzenia, ⏳ dokumentacja projektu, ⏳ wdrożenie na PythonAnywhere | 🚧 |
| **Oddanie** | ok. 17.12 | Moodle + działająca wersja online | ⏳ |

Otwarte kwestie:

- [x] zatwierdzenie palety kolorów
- [x] potwierdzenie licencji list JLPT (MIT, atrybucja w stopce i `SOURCES.md`)
- [ ] termin wdrożenia na PythonAnywhere (konto współdzielone z zadaniami)

---

## Licencja

Kod udostępniony na licencji [MIT](LICENSE). Dane słownikowe podlegają licencjom swoich źródeł (patrz [Dane słownikowe i licencje](#dane-słownikowe-i-licencje)).
