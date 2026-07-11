"""
Hotel models: Hotel, HotelAmenity, HotelRoom.

Hotels can be linked to tours and city destinations.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import OrderedMixin, PublishableMixin, SEOMixin, TimeStampedModel


class HotelAmenity(OrderedMixin):
    """An amenity offered by hotels (e.g. WiFi, Pool, Gym)."""

    name = models.CharField(_("Name"), max_length=100)
    icon = models.CharField(_("Tabler icon name"), max_length=60, default="check", blank=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Hotel amenity")
        verbose_name_plural = _("Hotel amenities")

    def __str__(self) -> str:
        return self.name


class Hotel(TimeStampedModel, SEOMixin, PublishableMixin, OrderedMixin):
    """A hotel or accommodation property."""

    CATEGORY_CHOICES = [
        ("budget", _("Budget")),
        ("standard", _("Standard")),
        ("superior", _("Superior")),
        ("boutique", _("Boutique")),
        ("resort", _("Resort")),
        ("hostel", _("Hostel")),
        ("luxury", _("Luxury")),
    ]

    STAR_CHOICES = [(i, f"{'★' * i}") for i in range(1, 6)]

    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=220, unique=True, blank=True)
    city = models.ForeignKey(
        "destinations.City",
        on_delete=models.CASCADE,
        related_name="hotels",
        verbose_name=_("City"),
    )
    category = models.CharField(_("Category"), max_length=20, choices=CATEGORY_CHOICES, default="standard")
    stars = models.PositiveSmallIntegerField(_("Stars"), choices=STAR_CHOICES, default=3)
    cover_image = models.ImageField(_("Cover image"), upload_to="hotels/covers/", blank=True, null=True)
    address = models.CharField(_("Address"), max_length=300, blank=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(_("Phone"), max_length=30, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    description = models.TextField(_("Description"), blank=True)
    amenities = models.ManyToManyField(
        HotelAmenity, related_name="hotels", verbose_name=_("Amenities"), blank=True
    )
    check_in_time = models.TimeField(_("Check-in time"), null=True, blank=True)
    check_out_time = models.TimeField(_("Check-out time"), null=True, blank=True)
    price_from = models.DecimalField(_("Price from (per night)"), max_digits=10, decimal_places=2, default=0)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotels")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("hotels:detail", kwargs={"slug": self.slug})

    @property
    def star_display(self) -> str:
        return "★" * self.stars + "☆" * (5 - self.stars)


class HotelImage(models.Model):
    """Gallery image for a hotel."""

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="gallery", verbose_name=_("Hotel"))
    image = models.ImageField(_("Image"), upload_to="hotels/gallery/")
    caption = models.CharField(_("Caption"), max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Hotel image")
        verbose_name_plural = _("Hotel images")
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.hotel} – {self.caption or 'image'}"


class HotelRoom(models.Model):
    """A room type offered by a hotel."""

    ROOM_TYPE_CHOICES = [
        ("single", _("Single")),
        ("double", _("Double")),
        ("twin", _("Twin")),
        ("triple", _("Triple")),
        ("suite", _("Suite")),
        ("family", _("Family Room")),
        ("deluxe", _("Deluxe")),
        ("presidential", _("Presidential Suite")),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rooms", verbose_name=_("Hotel"))
    room_type = models.CharField(_("Room type"), max_length=20, choices=ROOM_TYPE_CHOICES, default="double")
    description = models.TextField(_("Description"), blank=True)
    capacity = models.PositiveSmallIntegerField(_("Capacity (persons)"), default=2)
    price_per_night = models.DecimalField(_("Price per night"), max_digits=10, decimal_places=2, default=0)
    amenities = models.TextField(_("Amenities"), blank=True, help_text=_("Comma-separated list"))
    image = models.ImageField(_("Image"), upload_to="hotels/rooms/", blank=True, null=True)
    is_available = models.BooleanField(_("Available"), default=True)

    class Meta:
        verbose_name = _("Hotel room")
        verbose_name_plural = _("Hotel rooms")
        ordering = ["room_type"]

    def __str__(self) -> str:
        return f"{self.hotel} – {self.get_room_type_display()}"
