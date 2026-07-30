"""
Tour views: list (with filtering/sorting), detail, and booking entry.
"""

import json

from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView

from apps.destinations.models import Country
from apps.reviews.models import Review

from .filters import TourFilter
from .models import Tour, TourCategory, TourDeparture


class TourListView(ListView):
    """
    Filterable, sortable tour listing.

    Supports 12-per-page pagination and URL-persistent GET filters.
    Provides map data as JSON for the Leaflet map toggle.
    """

    model = Tour
    template_name = "tours/list.html"
    context_object_name = "tours"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Tour.objects.filter(is_active=True)
            .exclude(stops__order__gte=2)
            .select_related("category")
            .prefetch_related("destinations")
            .annotate(
                num_stops=Count("stops", distinct=True),
                avg_rating=Avg("reviews__rating", filter=Q(reviews__status="approved")),
            )
        )
        self.filterset = TourFilter(self.request.GET, queryset=qs)
        filtered_qs = self.filterset.qs

        sort = self.request.GET.get("sort", "chronological")
        sort_map = {
            "price_asc": "price_per_person",
            "price_desc": "-price_per_person",
            "duration": "duration_days",
            "newest": "-created_at",
            "most_viewed": "-views_count",
            "chronological": "id",  # in the order they were added (first added first)
        }
        return filtered_qs.order_by(sort_map.get(sort, "id"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = self.filterset
        ctx["categories"] = TourCategory.objects.all().order_by("order")
        ctx["destinations"] = Country.objects.filter(is_active=True).order_by("name")
        ctx["sort"] = self.request.GET.get("sort", "chronological")

        from apps.core.models import HeroSlide
        ctx["hero_slides"] = HeroSlide.objects.filter(
            page="tours", is_active=True
        ).order_by("order")

        # Serialize tour coords for map view
        map_tours = []
        for t in self.filterset.qs.prefetch_related("destinations")[:100]:
            for dest in t.destinations.all():
                cities = dest.cities.filter(latitude__isnull=False)[:1]
                if cities:
                    map_tours.append({
                        "id": t.pk,
                        "title": t.title,
                        "url": t.get_absolute_url(),
                        "price": str(t.discounted_price),
                        "lat": float(cities[0].latitude),
                        "lng": float(cities[0].longitude),
                    })
        ctx["map_tours_json"] = json.dumps(map_tours)
        return ctx


@method_decorator(cache_page(60 * 5), name="dispatch")
class IchkiTurlarListView(ListView):
    """
    "Ichki Turlar" — multi-city tours (those with more than one itinerary stop).

    Reuses regular Tour objects; the only distinction is having >1 TourStop.
    """

    model = Tour
    template_name = "tours/ichki_turlar_list.html"
    context_object_name = "tours"
    paginate_by = 12

    def get_queryset(self):
        return (
            Tour.objects.filter(is_active=True)
            .annotate(num_stops=Count("stops"))
            .filter(num_stops__gt=1)
            .select_related("category")
            .prefetch_related("stops__city")
            .order_by("order", "-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Ichki Turlar"
        from apps.core.models import HeroSlide
        ctx["hero_slides"] = HeroSlide.objects.filter(
            page="ichki_turlar", is_active=True
        )
        return ctx


class TourDetailView(DetailView):
    """
    Full tour detail page.

    Increments view counter, adds structured data, shows departures
    and related tours.
    """

    model = Tour
    template_name = "tours/detail.html"
    context_object_name = "tour"
    slug_field = "slug"

    def get_queryset(self):
        return (
            Tour.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                "destinations",
                "hotels__city",
                "days__attractions__city",
                "images",
                "departures",
                "reviews",
                "stops__city",
            )
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tour = self.object

        ctx["departures"] = tour.departures.filter(
            status="open"
        ).order_by("departure_date")

        ctx["approved_reviews"] = tour.reviews.filter(status="approved").order_by("-created_at")
        ctx["avg_rating"] = tour.average_rating
        ctx["review_count"] = ctx["approved_reviews"].count()

        # Rating breakdown
        breakdown = {i: 0 for i in range(1, 6)}
        for r in ctx["approved_reviews"]:
            breakdown[r.rating] = breakdown.get(r.rating, 0) + 1
        ctx["rating_breakdown"] = breakdown

        ctx["related_tours"] = (
            Tour.objects.filter(category=tour.category, is_active=True)
            .exclude(pk=tour.pk)
            .order_by("?")[:4]
        )

        ctx["breadcrumbs"] = [
            {"name": str(tour.category.name) if tour.category else "Tours", "url": "/tours/"},
            {"name": tour.title, "url": None},
        ]

        # Schema.org JSON-LD
        ctx["schema_json"] = self._build_schema(tour)
        return ctx

    def _build_schema(self, tour: Tour) -> str:
        schema = {
            "@context": "https://schema.org",
            "@type": "TouristTrip",
            "name": tour.title,
            "description": tour.seo_description or tour.overview[:160],
            "url": self.request.build_absolute_uri(tour.get_absolute_url()),
            "offers": {
                "@type": "Offer",
                "price": str(tour.discounted_price),
                "priceCurrency": tour.price_currency,
            },
        }
        if tour.cover_image:
            schema["image"] = str(tour.cover_image.url) if hasattr(tour.cover_image, "url") else ""
        return json.dumps(schema, ensure_ascii=False)
