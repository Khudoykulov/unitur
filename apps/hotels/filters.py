"""django-filter FilterSet for Hotel list view."""

import django_filters
from django.utils.translation import gettext_lazy as _

from apps.destinations.models import City, Country

from .models import Hotel


class HotelFilter(django_filters.FilterSet):
    """Filter hotels by country, city, category, stars, and price."""

    country = django_filters.ModelChoiceFilter(
        field_name="city__country",
        queryset=Country.objects.filter(is_active=True),
        label=_("Country"),
        empty_label=_("All countries"),
    )
    city = django_filters.ModelChoiceFilter(
        queryset=City.objects.filter(is_active=True),
        label=_("City"),
        empty_label=_("All cities"),
    )
    stars = django_filters.ChoiceFilter(
        choices=[("", _("Any stars"))] + [(i, str(i)) for i in range(1, 6)],
        label=_("Stars"),
    )
    max_price = django_filters.NumberFilter(field_name="price_from", lookup_expr="lte", label=_("Max price/night"))

    class Meta:
        model = Hotel
        fields = ["country", "city", "stars", "category"]
