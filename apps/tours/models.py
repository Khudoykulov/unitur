"""
Tour models: TourCategory, Tour, TourDay, TourDeparture, TourImage.

Tours are the core product of the agency, linking destinations,
hotels, and day-by-day itineraries.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import OrderedMixin, PublishableMixin, SEOMixin, TimeStampedModel

User = get_user_model()


class TourCategory(OrderedMixin):
    """Classification of tours (e.g. Adventure, Cultural, Beach)."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    icon = models.CharField(_("Icon (Tabler icon name)"), max_length=60, blank=True, default="compass")
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Image"), upload_to="tour_categories/", blank=True, null=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Tour category")
        verbose_name_plural = _("Tour categories")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("tours:list") + f"?category={self.slug}"


class Tour(TimeStampedModel, SEOMixin, PublishableMixin, OrderedMixin):
    """
    A tour package offered by the agency.

    Includes pricing, itinerary reference, destinations, and departure
    schedule information.
    """

    DIFFICULTY_CHOICES = [
        ("easy", _("Easy")),
        ("medium", _("Moderate")),
        ("hard", _("Challenging")),
    ]

    CURRENCY_CHOICES = [
        ("USD", "USD"),
        ("EUR", "EUR"),
        ("GBP", "GBP"),
        ("UZS", "UZS"),
    ]

    # Core fields
    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=220, unique=True, blank=True)
    category = models.ForeignKey(
        TourCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tours",
        verbose_name=_("Category"),
    )
    destinations = models.ManyToManyField(
        "destinations.Country",
        related_name="tours",
        verbose_name=_("Destinations"),
        blank=True,
    )
    hotels = models.ManyToManyField(
        "hotels.Hotel",
        related_name="tours",
        verbose_name=_("Hotels"),
        blank=True,
    )

    # Tour specs
    duration_days = models.PositiveSmallIntegerField(_("Duration (days)"), default=1)
    group_size_min = models.PositiveSmallIntegerField(_("Min group size"), default=2)
    group_size_max = models.PositiveSmallIntegerField(_("Max group size"), default=20)
    difficulty = models.CharField(_("Difficulty"), max_length=10, choices=DIFFICULTY_CHOICES, default="easy")

    # Pricing
    price_per_person = models.DecimalField(_("Price per person"), max_digits=10, decimal_places=2, default=Decimal("0"))
    price_currency = models.CharField(_("Currency"), max_length=3, choices=CURRENCY_CHOICES, default="USD")
    discount_percent = models.PositiveSmallIntegerField(_("Discount %"), default=0)

    # Media
    cover_image = models.ImageField(_("Cover image"), upload_to="tours/covers/", blank=True, null=True)

    # Content
    overview = models.TextField(_("Overview"), blank=True)
    includes = models.TextField(_("What's included"), blank=True)
    excludes = models.TextField(_("What's excluded"), blank=True)
    important_notes = models.TextField(_("Important notes"), blank=True)

    # Stats
    views_count = models.PositiveIntegerField(_("Views count"), default=0, editable=False)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Tour")
        verbose_name_plural = _("Tours")
        ordering = ["order", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("tours:detail", kwargs={"slug": self.slug})

    @property
    def discounted_price(self) -> Decimal:
        """Return price after applying discount_percent."""
        if self.discount_percent:
            return self.price_per_person * (1 - Decimal(self.discount_percent) / 100)
        return self.price_per_person

    @property
    def average_rating(self) -> float:
        """Return average rating from approved reviews."""
        reviews = self.reviews.filter(status="approved")
        if not reviews.exists():
            return 0.0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def increment_views(self) -> None:
        """Atomically increment view counter."""
        Tour.objects.filter(pk=self.pk).update(views_count=models.F("views_count") + 1)

    @property
    def is_multi_city(self) -> bool:
        """True when the tour has a multi-stop itinerary (Ichki Turlar)."""
        return self.stops.count() > 1


class TourStop(models.Model):
    """
    An ordered stop in a tour's multi-city itinerary.

    A tour with more than one stop is a multi-city ("Ichki Turlar") tour and
    renders the interactive route line on its detail page. Cities are shown in
    the visited sequence given by ``order`` rather than arbitrary M2M order.
    """

    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="stops", verbose_name=_("Tour")
    )
    city = models.ForeignKey(
        "destinations.City",
        on_delete=models.CASCADE,
        related_name="tour_stops",
        verbose_name=_("City"),
    )
    order = models.PositiveIntegerField(_("Order"), help_text=_("Sequence in the itinerary: 1, 2, 3…"))
    nights = models.PositiveIntegerField(_("Nights"), default=1, help_text=_("Nights spent in this city"))

    class Meta:
        verbose_name = _("Tour stop")
        verbose_name_plural = _("Tour stops")
        ordering = ["order"]
        unique_together = [("tour", "order")]

    def __str__(self) -> str:
        return f"{self.tour} – {self.order}. {self.city.name}"


class TourImage(models.Model):
    """Additional gallery images for a tour."""

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images", verbose_name=_("Tour"))
    image = models.ImageField(_("Image"), upload_to="tours/gallery/")
    caption = models.CharField(_("Caption"), max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Tour image")
        verbose_name_plural = _("Tour images")
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.tour} – image {self.order}"


class TourDay(OrderedMixin):
    """A single day's itinerary within a tour."""

    MEAL_CHOICES = [
        ("none", _("No meals")),
        ("breakfast", _("Breakfast")),
        ("breakfast_lunch", _("Breakfast & Lunch")),
        ("breakfast_dinner", _("Breakfast & Dinner")),
        ("all", _("All meals")),
    ]

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="days", verbose_name=_("Tour"))
    day_number = models.PositiveSmallIntegerField(_("Day number"))
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    meals_included = models.CharField(_("Meals included"), max_length=30, choices=MEAL_CHOICES, default="none")
    accommodation = models.CharField(_("Accommodation"), max_length=200, blank=True)
    transport = models.CharField(_("Transport"), max_length=200, blank=True)
    image = models.ImageField(_("Image"), upload_to="tours/days/", blank=True, null=True)

    class Meta:
        verbose_name = _("Tour day")
        verbose_name_plural = _("Tour days")
        ordering = ["day_number"]
        unique_together = [("tour", "day_number")]

    def __str__(self) -> str:
        return f"Day {self.day_number}: {self.title}"


class TourDeparture(models.Model):
    """A scheduled departure for a tour with seat availability."""

    STATUS_CHOICES = [
        ("open", _("Open for booking")),
        ("closed", _("Closed")),
        ("full", _("Fully booked")),
    ]

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="departures", verbose_name=_("Tour"))
    departure_date = models.DateField(_("Departure date"))
    return_date = models.DateField(_("Return date"))
    available_seats = models.PositiveSmallIntegerField(_("Available seats"), default=20)
    booked_seats = models.PositiveSmallIntegerField(_("Booked seats"), default=0)
    price_override = models.DecimalField(
        _("Price override"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default="open")

    class Meta:
        verbose_name = _("Tour departure")
        verbose_name_plural = _("Tour departures")
        ordering = ["departure_date"]

    def __str__(self) -> str:
        return f"{self.tour} – {self.departure_date}"

    @property
    def seats_left(self) -> int:
        return max(0, self.available_seats - self.booked_seats)

    @property
    def effective_price(self) -> Decimal:
        return self.price_override if self.price_override else self.tour.discounted_price

    def is_bookable(self) -> bool:
        return self.status == "open" and self.seats_left > 0
