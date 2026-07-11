"""django-filter FilterSet for Tour list view."""

import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.destinations.models import Country

from .models import Tour, TourCategory


class TourFilter(django_filters.FilterSet):
    """Filter tours by free-text search, category, destination, duration, price, and difficulty."""

    q = django_filters.CharFilter(method="filter_search", label=_("Search"))
    category = django_filters.ModelChoiceFilter(
        field_name="category",
        queryset=TourCategory.objects.all(),
        # The whole site links categories by slug (navbar, footer,
        # TourCategory.get_absolute_url, the filter <select>), so resolve the
        # incoming value against the slug rather than the default pk.
        to_field_name="slug",
        label=_("Category"),
        empty_label=_("All categories"),
    )
    destination = django_filters.ModelMultipleChoiceFilter(
        field_name="destinations",
        queryset=Country.objects.filter(is_active=True),
        label=_("Destination"),
        widget=forms.CheckboxSelectMultiple,
    )
    min_price = django_filters.NumberFilter(field_name="price_per_person", lookup_expr="gte", label=_("Min price"))
    max_price = django_filters.NumberFilter(field_name="price_per_person", lookup_expr="lte", label=_("Max price"))
    min_duration = django_filters.NumberFilter(field_name="duration_days", lookup_expr="gte", label=_("Min days"))
    max_duration = django_filters.NumberFilter(field_name="duration_days", lookup_expr="lte", label=_("Max days"))
    difficulty = django_filters.ChoiceFilter(
        choices=[("", _("Any difficulty"))] + Tour.DIFFICULTY_CHOICES,
        label=_("Difficulty"),
    )

    class Meta:
        model = Tour
        fields = ["category", "destination", "difficulty"]

    def filter_search(self, queryset, name, value):
        """Free-text search across title, overview, category and destinations.

        Powers the navbar and home-page "Where to?" search boxes, which submit
        ``?q=`` to the tour list.
        """
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value)
            | Q(overview__icontains=value)
            | Q(category__name__icontains=value)
            | Q(destinations__name__icontains=value)
            | Q(destinations__cities__name__icontains=value)
        ).distinct()
