from django.contrib.auth.models import User
from rest_framework import serializers

from decks.models import Card, Deck
from study.models import ReviewLog, ReviewState


class DeckSerializer(serializers.ModelSerializer):
    is_system = serializers.BooleanField(read_only=True)
    card_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Deck
        fields = ("id", "name", "description", "kind", "jlpt_level", "is_system", "card_count", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value):
        user = self.context["request"].user
        qs = Deck.objects.filter(owner=user, name__iexact=value.strip())
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Masz już talię o tej nazwie.")
        return value.strip()


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ("id", "deck", "front", "back", "reading", "example", "onyomi", "kunyomi", "stroke_count", "order")
        read_only_fields = ("id",)

    def validate_deck(self, deck):
        if deck.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("Karty można dodawać tylko do własnych talii.")
        return deck

    def validate(self, attrs):
        deck = attrs.get("deck") or getattr(self.instance, "deck", None)
        front = attrs.get("front") or getattr(self.instance, "front", None)
        duplicates = Card.objects.filter(deck=deck, front=front)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError({"front": "Ta karta już jest w talii."})
        return attrs


class StudyCardSerializer(serializers.ModelSerializer):
    deck_name = serializers.CharField(source="deck.name", read_only=True)

    class Meta:
        model = Card
        fields = ("id", "deck", "deck_name", "front", "back", "reading", "example", "onyomi", "kunyomi", "stroke_count")


class ReviewRequestSerializer(serializers.Serializer):
    card = serializers.IntegerField(help_text="ID karty")
    rating = serializers.ChoiceField(
        choices=ReviewLog.Rating.choices, help_text="0 = Znów, 1 = Trudne, 2 = Dobre, 3 = Łatwe"
    )
    response_ms = serializers.IntegerField(required=False, min_value=0, help_text="Czas odpowiedzi w ms")


class ReviewStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewState
        fields = ("card", "ease_factor", "interval_days", "repetitions", "lapses", "due_at", "last_reviewed_at")


class StudySummarySerializer(serializers.Serializer):
    due_now = serializers.IntegerField()
    new_available = serializers.IntegerField()
    reviews_today = serializers.IntegerField()
    daily_goal = serializers.IntegerField()
    goal_percent = serializers.IntegerField()
    streak_days = serializers.IntegerField()
    accuracy_percent = serializers.IntegerField(allow_null=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        read_only_fields = ("id",)
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Konto z tym adresem e-mail już istnieje.")
        return value.lower()

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
