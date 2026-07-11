"""Destination views: continent/country listing, country detail, city detail."""

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView

from apps.tours.models import Tour

from .models import City, Continent, Country


class DestinationListView(ListView):
    """
    List all countries grouped by continent.

    Annotates each country with its active tour count.
    """

    model = Country
    template_name = "destinations/list.html"
    context_object_name = "countries"

    def get_queryset(self):
        return (
            Country.objects.filter(is_active=True)
            .select_related("continent")
            .annotate(num_tours=Count("tours", filter=Q(tours__is_active=True)))
            .order_by("continent__order", "order", "name")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["continents"] = Continent.objects.all().order_by("order")
        return ctx


class CountryDetailView(DetailView):
    """Country page showing cities, tours, and overview."""

    model = Country
    template_name = "destinations/country.html"
    context_object_name = "country"
    slug_field = "slug"

    def get_queryset(self):
        return Country.objects.filter(is_active=True).select_related("continent").prefetch_related("cities")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        country = self.object
        ctx["cities"] = country.cities.filter(is_active=True).order_by("order", "name")
        ctx["tours"] = (
            Tour.objects.filter(destinations=country, is_active=True)
            .select_related("category")
            .order_by("order")[:8]
        )
        ctx["breadcrumbs"] = [
            {"name": "Destinations", "url": "/destinations/"},
            {"name": country.name, "url": None},
        ]
        return ctx


class CityDetailView(DetailView):
    """City page with attractions, hotels, and local tours."""

    model = City
    template_name = "destinations/city.html"
    context_object_name = "city"

    def get_object(self, queryset=None):
        country_slug = self.kwargs["country_slug"]
        city_slug = self.kwargs["city_slug"]
        return get_object_or_404(
            City.objects.select_related("country").prefetch_related(
                "attractions", "hotels", "images"
            ),
            slug=city_slug,
            country__slug=country_slug,
            is_active=True,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        city = self.object
        ctx["attractions"] = city.attractions.filter(is_active=True)
        ctx["hotels"] = city.hotels.filter(is_active=True).order_by("order")[:6]
        return ctx


class CityInfoAPIView(View):
    """
    JSON endpoint feeding the interactive route line on multi-city tours.

    Returns the city's name, overview, cover image, a small gallery (cover +
    attraction photos) and its attractions. City slugs are unique per country,
    so on the rare cross-country collision we return the first published match.
    """

    def get(self, request, slug, *args, **kwargs):
        city = (
            City.objects.filter(slug=slug, is_active=True)
            .select_related("country")
            .prefetch_related("attractions")
            .first()
        )
        if city is None:
            return JsonResponse({"error": "not_found"}, status=404)

        cover_url = city.cover_image.url if city.cover_image else ""
        gallery = [cover_url] if cover_url else []
        attractions = []
        for attraction in city.attractions.filter(is_active=True):
            img_url = attraction.image.url if attraction.image else ""
            if img_url:
                gallery.append(img_url)
            attractions.append({"name": attraction.name, "image_url": img_url})

        return JsonResponse(
            {
                "name": city.name,
                "description": city.overview,
                "cover_image_url": cover_url,
                "gallery": gallery,
                "attractions": attractions,
            }
        )
