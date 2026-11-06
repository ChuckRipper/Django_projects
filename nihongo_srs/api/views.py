from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from decks import services as deck_services
from decks.models import Card, Deck
from decks.sources import CsvCardSource
from stats import services as stats_services
from study import services

from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CardImportSerializer,
    CardSerializer,
    DailyReviewsSerializer,
    DeckSerializer,
    ImportReportSerializer,
    RegisterSerializer,
    ReviewRequestSerializer,
    ReviewStateSerializer,
    StudyCardSerializer,
    StudySummarySerializer,
)


@extend_schema(tags=["Auth"], summary="Rejestracja nowego użytkownika")
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


@extend_schema_view(
    list=extend_schema(summary="Lista talii (systemowe + własne)"),
    retrieve=extend_schema(summary="Szczegóły talii"),
    create=extend_schema(summary="Utworzenie własnej talii"),
    update=extend_schema(summary="Edycja własnej talii"),
    partial_update=extend_schema(summary="Częściowa edycja własnej talii"),
    destroy=extend_schema(summary="Usunięcie własnej talii"),
)
@extend_schema(tags=["Talie"])
class DeckViewSet(viewsets.ModelViewSet):
    serializer_class = DeckSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return (
            Deck.objects.visible_to(self.request.user)
            .annotate(card_count=Count("cards"))
            .order_by("owner_id", "order", "name")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(summary="Karty w talii", responses=CardSerializer(many=True))
    @action(detail=True, methods=["get"])
    def cards(self, request, pk=None):
        deck = self.get_object()
        page = self.paginate_queryset(deck.cards.all())
        return self.get_paginated_response(CardSerializer(page, many=True).data)

    @extend_schema(
        summary="Import kart z pliku CSV",
        description="Kolumny: front/przod, back/tyl (wymagane) oraz opcjonalnie reading, example, "
        "onyomi, kunyomi, stroke_count. Tylko do własnych talii.",
        request={"multipart/form-data": CardImportSerializer},
        responses={200: ImportReportSerializer},
    )
    @action(detail=True, methods=["post"], url_path="import", parser_classes=[MultiPartParser, FormParser])
    def import_cards(self, request, pk=None):
        deck = self.get_object()
        if deck.owner_id != request.user.id:
            raise PermissionDenied("Karty można importować tylko do własnych talii.")
        serializer = CardImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = CsvCardSource.from_upload(serializer.validated_data["file"])
        report = deck_services.import_cards(deck, source, serializer.validated_data["update_existing"])
        return Response(ImportReportSerializer(report).data)

    @extend_schema(summary="Eksport talii do CSV", responses={(200, "text/csv"): OpenApiTypes.STR})
    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        deck = self.get_object()
        response = HttpResponse(deck_services.export_csv(deck), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="talia-{deck.pk}.csv"'
        return response


@extend_schema_view(
    list=extend_schema(summary="Lista kart z widocznych talii"),
    retrieve=extend_schema(summary="Szczegóły karty"),
    create=extend_schema(summary="Dodanie karty do własnej talii"),
    update=extend_schema(summary="Edycja karty we własnej talii"),
    partial_update=extend_schema(summary="Częściowa edycja karty"),
    destroy=extend_schema(summary="Usunięcie karty z własnej talii"),
)
@extend_schema(tags=["Karty"])
class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Card.objects.filter(deck__in=Deck.objects.visible_to(self.request.user)).select_related("deck")


@extend_schema(
    tags=["Nauka"],
    summary="Kolejka nauki",
    description="Zaległe powtórki, a po nich nowe karty do dziennego limitu z profilu.",
    parameters=[
        OpenApiParameter("deck", int, description="Ogranicz do jednej talii"),
        OpenApiParameter("limit", int, description="Maksymalna liczba kart (domyślnie 20)"),
    ],
    responses=StudyCardSerializer(many=True),
)
class StudyQueueView(APIView):
    def get(self, request):
        deck = None
        if request.query_params.get("deck"):
            deck = get_object_or_404(Deck.objects.visible_to(request.user), pk=request.query_params["deck"])
        try:
            limit = max(1, min(int(request.query_params.get("limit", 20)), 200))
        except ValueError:
            limit = 20
        queue = services.build_queue(request.user, deck, limit=limit)
        return Response(StudyCardSerializer(queue, many=True).data)


@extend_schema(
    tags=["Nauka"],
    summary="Zapis oceny karty",
    description="Przelicza termin następnej powtórki wybranym algorytmem (domyślnie SM-2).",
    request=ReviewRequestSerializer,
    responses={201: ReviewStateSerializer},
)
class ReviewView(APIView):
    def post(self, request):
        serializer = ReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = get_object_or_404(
            Card.objects.filter(deck__in=Deck.objects.visible_to(request.user)),
            pk=serializer.validated_data["card"],
        )
        state = services.submit_review(
            request.user, card, serializer.validated_data["rating"],
            serializer.validated_data.get("response_ms"),
        )
        return Response(ReviewStateSerializer(state).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Statystyki"], summary="Podsumowanie nauki", responses=StudySummarySerializer)
class SummaryView(APIView):
    def get(self, request):
        summary = services.study_summary(request.user)
        data = {**summary.__dict__, "goal_percent": summary.goal_percent}
        return Response(StudySummarySerializer(data).data)


@extend_schema(
    tags=["Statystyki"],
    summary="Powtórki dziennie",
    parameters=[OpenApiParameter("days", int, description="Liczba dni wstecz (1–365, domyślnie 30)")],
    responses=DailyReviewsSerializer(many=True),
)
class DailyReviewsView(APIView):
    def get(self, request):
        try:
            days = max(1, min(int(request.query_params.get("days", 30)), 365))
        except ValueError:
            days = 30
        return Response(DailyReviewsSerializer(stats_services.daily_reviews(request.user, days), many=True).data)
