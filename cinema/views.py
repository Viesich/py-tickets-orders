from django.db.models import F, Count
from django.utils.dateparse import parse_date
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderListSerializer,
    OrderSerializer,
    MovieGetDetailSerializer,
    MovieSessionListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        genres_data = response.data.get("results", response.data)
        return Response(genres_data, status=status.HTTP_200_OK)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        actors_data = response.data.get("results", response.data)
        return Response(actors_data, status=status.HTTP_200_OK)


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        cinema_halls_data = response.data.get("results", response.data)
        return Response(cinema_halls_data, status=status.HTTP_200_OK)


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()

    @staticmethod
    def _params_to_ints(query_string):
        return [
            int(str_id) for str_id in query_string.split(",")
        ]

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")
        if actors:
            actors = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors)
        if genres:
            genres = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres)
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        movies_data = response.data.get("results", response.data)
        return Response(movies_data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieGetDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)
        queryset = queryset.select_related("cinema_hall").annotate(
            tickets_available=(
                    F("cinema_hall__rows") *
                    F("cinema_hall__seats_in_row") -
                    Count("tickets")
            )
        ).order_by("id")
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        movie_sessions_data = response.data.get("results", response.data)
        return Response(movie_sessions_data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        elif self.action == "retrieve":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()

    def get_queryset(self):
        return Order.objects.all().filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer
