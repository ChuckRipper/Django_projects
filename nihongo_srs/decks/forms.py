from django import forms

from .models import Card, Deck


class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ("name", "description", "kind", "jlpt_level")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        duplicates = Deck.objects.filter(owner=self.owner, name__iexact=name).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Masz już talię o tej nazwie.")
        return name


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ("front", "back", "reading", "example", "onyomi", "kunyomi", "stroke_count")

    def __init__(self, *args, deck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.deck = deck or getattr(self.instance, "deck", None)
        if self.deck is not None and self.deck.kind != Deck.Kind.KANJI:
            for name in ("onyomi", "kunyomi", "stroke_count"):
                self.fields.pop(name)

    def clean_front(self):
        front = self.cleaned_data["front"].strip()
        if Card.objects.filter(deck=self.deck, front=front).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ta karta już jest w talii.")
        return front


class CardImportForm(forms.Form):
    file = forms.FileField(
        label="Plik CSV",
        help_text=(
            "Pierwszy wiersz to nagłówki. Wymagane kolumny: <code>front</code> (lub <code>przod</code>) "
            "i <code>back</code> (lub <code>tyl</code>); opcjonalne: <code>reading</code>, <code>example</code>, "
            "<code>onyomi</code>, <code>kunyomi</code>, <code>stroke_count</code>. Separator: przecinek, średnik "
            "lub tabulator. Maks. 1 MB."
        ),
    )
    update_existing = forms.BooleanField(
        label="Aktualizuj istniejące karty (o tym samym przodzie)", required=False, initial=True,
    )

    MAX_SIZE = 1024 * 1024

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.size > self.MAX_SIZE:
            raise forms.ValidationError("Plik jest za duży (maks. 1 MB).")
        if not uploaded.name.lower().endswith((".csv", ".txt", ".tsv")):
            raise forms.ValidationError("Dozwolone są pliki .csv, .tsv lub .txt.")
        return uploaded
