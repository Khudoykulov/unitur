"""
Destination models: Continent → Country → City → Attraction.

All models use TranslatableMixin pattern (modeltranslation registers
translated fields in translation.py).
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import OrderedMixin, PublishableMixin, SEOMixin, TimeStampedModel


class Continent(TimeStampedModel, SEOMixin, OrderedMixin):
    """A continent grouping countries."""

    name = models.CharField(_("Name"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    image = models.ImageField(_("Image"), upload_to="continents/", blank=True, null=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Continent")
        verbose_name_plural = _("Continents")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("destinations:list") + f"?continent={self.slug}"


class Country(TimeStampedModel, SEOMixin, PublishableMixin, OrderedMixin):
    """A country destination with visa, currency, and travel information."""

    continent = models.ForeignKey(
        Continent,
        on_delete=models.SET_NULL,
        null=True,
        related_name="countries",
        verbose_name=_("Continent"),
    )
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    flag_image = models.ImageField(_("Flag image"), upload_to="countries/flags/", blank=True, null=True)
    cover_image = models.ImageField(_("Cover image"), upload_to="countries/covers/", blank=True, null=True)
    overview = models.TextField(_("Overview"), blank=True)
    visa_info = models.TextField(_("Visa information"), blank=True)
    best_time_to_visit = models.CharField(_("Best time to visit"), max_length=200, blank=True)
    currency = models.CharField(_("Currency"), max_length=50, blank=True)
    language = models.CharField(_("Official language"), max_length=100, blank=True)
    timezone = models.CharField(_("Timezone"), max_length=60, blank=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("destinations:country", kwargs={"slug": self.slug})

    @property
    def tour_count(self) -> int:
        """Number of active tours covering this country."""
        return self.tours.filter(is_active=True).count()


class Attraction(TimeStampedModel, PublishableMixin):
    """A point of interest within a city."""

    CATEGORY_CHOICES = [
        ("nature", _("Nature")),
        ("culture", _("Culture & Heritage")),
        ("adventure", _("Adventure")),
        ("beach", _("Beach")),
        ("city", _("City Sightseeing")),
        ("museum", _("Museum")),
        ("food", _("Food & Drink")),
        ("shopping", _("Shopping")),
        ("entertainment", _("Entertainment")),
        ("religious", _("Religious Site")),
    ]

    city = models.ForeignKey(
        "City",
        on_delete=models.CASCADE,
        related_name="attractions",
        verbose_name=_("City"),
    )
    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=170, blank=True)
    category = models.CharField(_("Category"), max_length=20, choices=CATEGORY_CHOICES, default="city")
    image = models.ImageField(_("Image"), upload_to="attractions/", blank=True, null=True)
    description = models.TextField(_("Description"), blank=True)
    entrance_fee = models.CharField(_("Entrance fee"), max_length=100, blank=True)
    opening_hours = models.CharField(_("Opening hours"), max_length=200, blank=True)
    google_maps_url = models.URLField(_("Google Maps URL"), blank=True)

    class Meta:
        verbose_name = _("Attraction")
        verbose_name_plural = _("Attractions")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class City(TimeStampedModel, SEOMixin, PublishableMixin, OrderedMixin):
    """A city within a country, containing attractions and hotels."""

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cities",
        verbose_name=_("Country"),
    )
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, blank=True)
    cover_image = models.ImageField(_("Cover image"), upload_to="cities/covers/", blank=True, null=True)
    overview = models.TextField(_("Overview"), blank=True)
    population = models.PositiveIntegerField(_("Population"), null=True, blank=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        ordering = ["order", "name"]
        unique_together = [("country", "slug")]

    def __str__(self) -> str:
        return f"{self.name}, {self.country}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse(
            "destinations:city",
            kwargs={"country_slug": self.country.slug, "city_slug": self.slug},
        )


class CityImage(models.Model):
    """A gallery photo for a city (shown on the city detail page)."""

    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="images", verbose_name=_("City")
    )
    image = models.ImageField(_("Image"), upload_to="cities/gallery/")
    caption = models.CharField(_("Caption"), max_length=200, blank=True)
    description = models.TextField(_("Description"), blank=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("City image")
        verbose_name_plural = _("City images")
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.city.name} – image {self.order}"
