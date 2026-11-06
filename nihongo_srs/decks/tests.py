from io import StringIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .factories import CardFactory, KanjiCardFactory
from .models import Card, Deck
from .services import export_csv, import_cards
from .sources import CardData, CsvCardSource


class LoadDataTests(TestCase):
    def test_loads_system_decks_and_is_idempotent(self):
        call_command("load_data", stdout=StringIO())
        counts = {deck.name: deck.cards.count() for deck in Deck.objects.filter(owner=None)}
        call_command("load_data", stdout=StringIO())
        self.assertEqual({d.name: d.cards.count() for d in Deck.objects.filter(owner=None)}, counts)
        self.assertEqual(len(counts), 10)
        self.assertEqual(Card.objects.filter(deck__kind=Deck.Kind.KANA).count(), 2 * (46 + 25 + 33))
        self.assertEqual(counts["Kanji N5"], 79)
        self.assertEqual(counts["Kanji N4"], 166)
        self.assertGreater(counts["Słownictwo N5"], 650)
        self.assertGreater(counts["Słownictwo N4"], 600)

    def test_kanji_card_content(self):
        call_command("load_data", stdout=StringIO())
        card = Card.objects.get(deck__name="Kanji N5", front="日")
        self.assertEqual(card.back, "dzień, słońce, Japonia")
        self.assertIn("ニチ", card.onyomi)  # on'yomi converted to katakana
        self.assertEqual(card.stroke_count, 4)
        self.assertTrue(card.example)

    def test_vocabulary_cleanup(self):
        call_command("load_data", stdout=StringIO())
        n5 = Deck.objects.get(name="Słownictwo N5")
        nine = n5.cards.get(front="九")  # two readings merged into one card
        self.assertEqual(nine.reading, "きゅう; く")
        good = n5.cards.get(front="いい")  # kana-only word: alternative form kept as a note
        self.assertEqual((good.reading, good.example), ("", "Inny zapis: よい"))
        self.assertEqual(n5.cards.get(front="猫").back, "kot")


class DeckPermissionTests(TestCase):
    def setUp(self):
        self.ania = User.objects.create_user("ania", password="Haslo-12345")
        self.bartek = User.objects.create_user("bartek", password="Haslo-12345")
        self.system = Deck.objects.create(name="Systemowa")
        self.own = Deck.objects.create(name="Moja", owner=self.ania)
        self.foreign = Deck.objects.create(name="Bartka", owner=self.bartek)
        self.client.login(username="ania", password="Haslo-12345")

    def test_list_shows_system_and_own_decks_only(self):
        response = self.client.get(reverse("deck_list"))
        names = {d.name for d in response.context["decks"]}
        self.assertEqual(names, {"Systemowa", "Moja"})

    def test_foreign_deck_is_404(self):
        self.assertEqual(self.client.get(reverse("deck_detail", args=[self.foreign.pk])).status_code, 404)

    def test_system_deck_cannot_be_edited(self):
        self.assertEqual(self.client.get(reverse("deck_update", args=[self.system.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("card_create", args=[self.system.pk])).status_code, 404)

    def test_create_deck_and_card(self):
        data = {"name": "Słówka", "kind": "vocabulary", "jlpt_level": "N5"}
        response = self.client.post(reverse("deck_create"), data)
        deck = Deck.objects.get(name="Słówka")
        self.assertEqual(deck.owner, self.ania)
        self.assertRedirects(response, reverse("deck_detail", args=[deck.pk]))
        self.client.post(reverse("card_create", args=[deck.pk]), {"front": "猫", "back": "kot", "reading": "ねこ"})
        self.assertTrue(deck.cards.filter(front="猫").exists())

    def test_duplicate_deck_name_rejected(self):
        response = self.client.post(reverse("deck_create"), {"name": "moja", "kind": "vocabulary"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["name"])

    def test_filter_by_kind(self):
        Deck.objects.create(name="Kanji N5", kind=Deck.Kind.KANJI)
        response = self.client.get(reverse("deck_list"), {"kind": "kanji"})
        self.assertEqual([d.name for d in response.context["decks"]], ["Kanji N5"])


class CsvSourceTests(SimpleTestCase):
    def test_polish_headers_semicolon_and_errors(self):
        source = CsvCardSource("przod;tyl;odczyt\n猫;kot;ねこ\n;pusty;\n犬;pies;いぬ\n")
        cards = list(source)
        self.assertEqual([c.front for c in cards], ["猫", "犬"])
        self.assertEqual(cards[0].reading, "ねこ")
        self.assertEqual(source.errors[0].line, 3)

    def test_missing_required_columns(self):
        source = CsvCardSource("slowo_x,cos\n猫,kot\n")
        self.assertEqual(list(source), [])
        self.assertIn("Brak wymaganych kolumn", source.errors[0].message)

    def test_bom_and_invalid_stroke_count(self):
        source = CsvCardSource("\ufefffront,back,stroke_count\n日,dzień,4\n月,miesiąc,abc\n")
        cards = list(source)
        self.assertEqual((cards[0].front, cards[0].stroke_count), ("日", 4))
        self.assertEqual(len(source.errors), 1)


class FactoryAndImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ania", password="Haslo-12345")
        self.deck = Deck.objects.create(name="Moje kanji", kind=Deck.Kind.KANJI, owner=self.user)

    def test_factory_is_chosen_by_deck_kind(self):
        self.assertIsInstance(CardFactory.for_deck(self.deck), KanjiCardFactory)

    def test_kanji_factory_rejects_words(self):
        report = import_cards(self.deck, [CardData("日本", "Japonia"), CardData("山", "góra")])
        self.assertEqual(report.created, 1)
        self.assertEqual(len(report.errors), 1)

    def test_import_updates_existing_and_export_roundtrip(self):
        import_cards(self.deck, [CardData("山", "góra")])
        report = import_cards(self.deck, [CardData("山", "góra, szczyt", onyomi="サン")])
        self.assertEqual((report.created, report.updated), (0, 1))
        exported = export_csv(self.deck)
        self.assertIn("山,\"góra, szczyt\",,,サン", exported)
        other = Deck.objects.create(name="Kopia", kind=Deck.Kind.KANJI, owner=self.user)
        import_cards(other, CsvCardSource(exported))
        self.assertEqual(other.cards.get().onyomi, "サン")

    def test_import_view(self):
        self.client.login(username="ania", password="Haslo-12345")
        upload = SimpleUploadedFile("karty.csv", "front,back\n川,rzeka\n".encode())
        url = reverse("card_import", args=[self.deck.pk])
        response = self.client.post(url, {"file": upload, "update_existing": "on"})
        self.assertRedirects(response, reverse("deck_detail", args=[self.deck.pk]))
        self.assertTrue(self.deck.cards.filter(front="川").exists())

    def test_import_view_shows_errors(self):
        self.client.login(username="ania", password="Haslo-12345")
        upload = SimpleUploadedFile("karty.csv", "front,back\n川,rzeka\n日本,Japonia\n".encode())
        response = self.client.post(reverse("card_import", args=[self.deck.pk]), {"file": upload})
        self.assertContains(response, "Wiersz 2")

    def test_cannot_import_into_system_deck(self):
        self.client.login(username="ania", password="Haslo-12345")
        system = Deck.objects.create(name="Systemowa", kind=Deck.Kind.KANJI)
        self.assertEqual(self.client.get(reverse("card_import", args=[system.pk])).status_code, 404)

    def test_export_view(self):
        self.client.login(username="ania", password="Haslo-12345")
        import_cards(self.deck, [CardData("山", "góra")])
        response = self.client.get(reverse("deck_export", args=[self.deck.pk]))
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("山,góra", response.content.decode())
