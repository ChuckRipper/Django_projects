# Nihongo SRS

Aplikacja webowa w Django do nauki języka japońskiego metodą **powtórek rozłożonych w czasie** (SRS, *spaced repetition system*). Użytkownik uczy się kart z sylabariuszami kana, słownictwem i kanji na poziomach JLPT N5–N4, ocenia, jak dobrze pamiętał odpowiedź, a algorytm SM-2 sam planuje kolejną powtórkę, osobno dla każdego użytkownika i każdej karty.

> Projekt zaliczeniowy z przedmiotu *Aplikacje internetowe w Django* (mgr inż. Marek Foryś), WSB Merito Chorzów, Informatyka II stopnia, specjalność Programista Python.
> Autor: Cezary Kalinowski

**Status:** 🚧 w budowie, patrz [Plan prac](#plan-prac).

---

## Spis treści

1. [Funkcje](#funkcje)
2. [Technologie](#technologie)
3. [Architektura](#architektura)
4. [Model danych](#model-danych)
5. [Algorytm powtórek (SM-2)](#algorytm-powtórek-sm-2)
6. [Dane słownikowe i licencje](#dane-słownikowe-i-licencje)
7. [Identyfikacja wizualna](#identyfikacja-wizualna)
8. [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
9. [Testy](#testy)
10. [Wdrożenie (PythonAnywhere)](#wdrożenie-pythonanywhere)
11. [Workflow Git](#workflow-git)
12. [Plan prac](#plan-prac)
13. [Licencja](#licencja)

---

## Funkcje

### Zakres podstawowy (MVP)

| Moduł | Funkcje |
|---|---|
| **Konta** | rejestracja, logowanie, wylogowanie; profil z dziennym limitem nowych kart i celem dziennym |
| **Talie i karty** | talie systemowe (tylko do odczytu) i własne talie użytkownika; pełny CRUD talii i kart; wyszukiwanie oraz filtry po typie i poziomie JLPT |
| **Nauka** | sesja powtórek: kolejka (zaległe powtórki + nowe karty do dziennego limitu) → przód karty → odsłonięcie odpowiedzi → ocena **Znów / Trudne / Dobre / Łatwe** → wyliczenie następnego terminu |
| **Kanji** | znaczenie, odczyty on'yomi i kun'yomi, liczba kresek, poziom JLPT, przykładowe słówka |
| **Statystyki** | karty do powtórki dziś, seria dni nauki, skuteczność, karty wg etapu (nowe / w nauce / opanowane), wykres powtórek z ostatnich 30 dni |
| **Import** | wczytywanie talii z pliku CSV z walidacją i raportem błędów |
| **Panel admina** | zarządzanie taliami systemowymi i kartami, podgląd historii powtórek |
| **Interfejs** | po polsku, responsywny, motyw jasny i ciemny z przełącznikiem, własna strona 404 |

### Rozszerzenia (planowane, jeśli starczy czasu)

- tryb „wpisz odpowiedź” z konwersją romaji → kana w trakcie pisania
- animowana kolejność kresek kanji
- heatmapa aktywności w stylu GitHuba
- eksport talii do CSV i udostępnianie własnych talii innym użytkownikom
- reset hasła e-mailem
- REST API (Django REST Framework)

### Materiał na start

| Zestaw | Zawartość (przybliżona) |
|---|---|
| Hiragana | 46 znaków podstawowych + dakuten / handakuten + połączenia (yōon) |
| Katakana | jak wyżej |
| JLPT N5 | ok. 80 kanji, ok. 700 słówek |
| JLPT N4 | ok. 170 kanji, ok. 650 słówek |

---

## Technologie

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.13, **Django 5.2 LTS** |
| Baza danych | SQLite |
| Frontend | szablony Django, Bootstrap 5.3 (motyw jasny i ciemny przez `data-bs-theme`), Bootstrap Icons |
| Wykresy | Chart.js |
| Wprowadzanie kana | WanaKana (rozszerzenie) |
| Testy | `django.test` (`TestCase`, klient testowy) |
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
| `stats` | agregacje i wykresy na podstawie historii powtórek |
| `core` | wspólny szablon bazowy, strona główna, strony błędów, przełącznik motywu |

### Planowana struktura repozytorium

```
Django_projects/
├── README.md
├── LICENSE
├── .gitignore
└── nihongo_srs/
    ├── manage.py
    ├── requirements.txt
    ├── config/              # ustawienia projektu, główne urls.py, wsgi.py
    ├── accounts/
    ├── decks/
    │   ├── data/            # pliki z kana i słownictwem/kanji N5–N4
    │   └── management/commands/load_data.py
    ├── study/
    │   └── srs.py           # algorytm SM-2
    ├── stats/
    ├── core/
    ├── templates/
    └── static/              # CSS (paleta, motywy), JS, logo
```

---

## Model danych

| Model | Najważniejsze pola | Uwagi |
|---|---|---|
| `Deck` | `name`, `description`, `kind` (kana / vocabulary / kanji), `jlpt_level`, `owner`, `created_at` | `owner = NULL` → talia systemowa |
| `Card` | `deck`, `front`, `back`, `reading`, `example`, `onyomi`, `kunyomi`, `stroke_count`, `order` | pola kanji wypełniane tylko dla kart kanji |
| `ReviewState` | `user`, `card`, `ease_factor`, `interval_days`, `repetitions`, `lapses`, `due_at`, `introduced_at` | unikalna para `user` + `card`; stan nauki konkretnej osoby |
| `ReviewLog` | `user`, `card`, `rating`, `reviewed_at`, `response_ms`, `interval_before`, `interval_after` | pełna historia, źródło statystyk |
| `Profile` | `user` (1:1), `new_cards_per_day`, `daily_goal` | ustawienia nauki |

Karty są wspólne, a postęp jest prywatny: ta sama karta systemowa ma osobny `ReviewState` dla każdego użytkownika.

---

## Algorytm powtórek (SM-2)

Wariant algorytmu SuperMemo SM-2 z czterema ocenami:

| Ocena | Efekt |
|---|---|
| **Znów** | `repetitions = 0`, karta wraca w tej samej sesji, `lapses + 1`, `ease − 0,20` |
| **Trudne** | interwał × 1,2, `ease − 0,15` |
| **Dobre** | interwał × `ease` |
| **Łatwe** | interwał × `ease` × 1,3, `ease + 0,15` |

- Pierwsze poprawne odpowiedzi: 1 dzień → 6 dni → dalej mnożenie przez `ease`.
- Początkowy `ease` = 2,5, minimalny = 1,3.
- Kolejka dnia: najpierw zaległe powtórki (`due_at ≤ teraz`), potem nowe karty do dziennego limitu z profilu.

Logika znajduje się w module `study/srs.py` jako czyste funkcje, więc da się ją testować jednostkowo, niezależnie od bazy i widoków.

---

## Dane słownikowe i licencje

| Źródło | Wykorzystanie | Licencja |
|---|---|---|
| Kana | generowane w kodzie | – |
| JMdict / KANJIDIC2 (Electronic Dictionary Research and Development Group) | znaczenia, odczyty, liczba kresek | CC BY-SA 4.0, atrybucja wyświetlana w aplikacji |
| Listy JLPT N5/N4 | przypisanie poziomów | listy społecznościowe (oficjalne listy nie istnieją); licencja do potwierdzenia przed użyciem |

Znaczenia w źródłach są po angielsku. Dla kart N5 planowane są polskie tłumaczenia.

---

## Identyfikacja wizualna

- **Logo:** 日本語 (*nihongo*) + „SRS” w kolorze akcentu; wersja pozioma (pasek nawigacji) i kwadratowa (favicon), format SVG.
- **Kolejność prac:** najpierw paleta kolorów aplikacji (zmienne CSS), logo projektowane na końcu w kolorach przewodnich.
- **Motyw jasny i ciemny** z przełącznikiem; wybór zapamiętywany w przeglądarce.

Propozycja palety (do zatwierdzenia):

| Rola | Kolor | Nawiązanie |
|---|---|---|
| Główny | indygo `#1f3a5f` | *ai-iro*, tradycyjny japoński błękit indygo |
| Akcent | cynober `#d1495b` | *shu-iro*, kolor bram torii |
| Tło jasne | `#faf7f2` | papier washi |
| Tło ciemne | `#1b1d21` | tusz *sumi* |

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
python manage.py load_data            # kana + słownictwo i kanji N5–N4
python manage.py createsuperuser
python manage.py runserver
```

Aplikacja: http://127.0.0.1:8000/ · panel admina: http://127.0.0.1:8000/admin/

Jeśli Windows zgłasza „You don't have permission to access that port”, uruchom serwer na innym porcie, np. `python manage.py runserver 8765`.

---

## Testy

```powershell
cd nihongo_srs
python manage.py test
```

Planowane obszary testów:

- algorytm SM-2: wszystkie oceny, granice `ease`, kolejne interwały
- budowa kolejki: zaległe karty, dzienny limit nowych kart
- sesja nauki: zapis oceny, aktualizacja `ReviewState` i `ReviewLog`
- uprawnienia: brak dostępu do cudzych talii, talie systemowe tylko do odczytu
- import CSV: poprawne dane i raport błędów

---

## Wdrożenie (PythonAnywhere)

| Ustawienie | Wartość |
|---|---|
| Adres | https://czarodziej.pythonanywhere.com/ |
| Source code / Working directory | `/home/Czarodziej/Django_projects/nihongo_srs` |
| Virtualenv | `/home/Czarodziej/venv_django` |
| Static files | `/static/` → `/home/Czarodziej/Django_projects/nihongo_srs/staticfiles` |
| `DJANGO_SETTINGS_MODULE` | `config.settings` |

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
| **M1: Fundament** | 14.11 | szkielet projektu, konta, modele, talie kana, działająca sesja SM-2, paleta i motyw ciemny | ⏳ |
| **M2: Treść i statystyki** | 28.11 | słownictwo i kanji N5–N4, własne talie, import CSV, statystyki | ⏳ |
| **M3: Dopracowanie** | 12.12 | UI, logo, testy, dokumentacja projektu, wdrożenie na PythonAnywhere | ⏳ |
| **Oddanie** | ok. 17.12 | Moodle + działająca wersja online | ⏳ |

Otwarte kwestie:

- [ ] zatwierdzenie palety kolorów
- [ ] potwierdzenie licencji list JLPT
- [ ] termin wdrożenia na PythonAnywhere (konto współdzielone z zadaniami)

---

## Licencja

Kod udostępniony na licencji [MIT](LICENSE). Dane słownikowe podlegają licencjom swoich źródeł (patrz [Dane słownikowe i licencje](#dane-słownikowe-i-licencje)).
