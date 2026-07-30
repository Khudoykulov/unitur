"""
Booking & Inquiry models.

Handles tour bookings, hotel inquiries, and general custom travel requests.
"""

import uuid

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

User = get_user_model()

# Lenient international phone check: digits with optional +, spaces, dashes,
# parentheses (7–20 chars). Keeps validation forgiving across countries.
phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-()]{7,20}$",
    message=_("Enter a valid phone number (7–20 digits, +, spaces, - or () allowed)."),
)


def _generate_confirmation_number() -> str:
    """Generate a short, uppercase confirmation code (8 chars)."""
    return uuid.uuid4().hex[:8].upper()


class Inquiry(TimeStampedModel):
    """
    A customer inquiry or booking request.

    Covers tours, hotels, corporate, and custom travel arrangements.
    Staff can assign and annotate inquiries through the admin.
    """

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("submitted", _("Submitted")),
        ("confirmed", _("Confirmed")),
        ("cancelled", _("Cancelled")),
        ("completed", _("Completed")),
    ]

    INQUIRY_TYPE_CHOICES = [
        ("tour", _("Tour Booking")),
        ("hotel", _("Hotel Booking")),
        ("corporate", _("Corporate / MICE")),
        ("custom", _("Custom Trip")),
    ]

    SOURCE_CHOICES = [
        ("web", _("Website")),
        ("email", _("Email")),
        ("phone", _("Phone")),
        ("social", _("Social Media")),
        ("referral", _("Referral")),
    ]

    BUDGET_CHOICES = [
        ("economy", _("Economy (< $500)")),
        ("standard", _("Standard ($500 – $1,500)")),
        ("premium", _("Premium ($1,500 – $3,000)")),
        ("luxury", _("Luxury (> $3,000)")),
    ]

    # Classification
    inquiry_type = models.CharField(
        _("Inquiry type"), max_length=20, choices=INQUIRY_TYPE_CHOICES, default="tour"
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="submitted")

    # Linked items (optional)
    tour = models.ForeignKey(
        "tours.Tour",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        verbose_name=_("Tour"),
    )
    category = models.ForeignKey(
        "tours.TourCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        verbose_name=_("Tour category"),
    )
    custom_category = models.CharField(
        _("Custom category"), max_length=100, blank=True
    )
    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        verbose_name=_("Hotel"),
    )
    departure = models.ForeignKey(
        "tours.TourDeparture",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        verbose_name=_("Tour departure"),
    )

    # Customer info
    first_name = models.CharField(_("First name"), max_length=100)
    last_name = models.CharField(_("Last name"), max_length=100)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=30, validators=[phone_validator])
    country_of_origin = models.CharField(_("Country of origin"), max_length=100, blank=True)

    # Travel details
    travel_date = models.DateField(_("Preferred travel date"), null=True, blank=True)
    num_adults = models.PositiveSmallIntegerField(_("Number of adults"), default=2)
    num_children = models.PositiveSmallIntegerField(_("Number of children"), default=0)
    special_requests = models.TextField(_("Special requests"), blank=True)
    budget_range = models.CharField(
        _("Budget range"), max_length=20, choices=BUDGET_CHOICES, blank=True
    )

    # Tracking
    source = models.CharField(_("Source"), max_length=20, choices=SOURCE_CHOICES, default="web")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_inquiries",
        verbose_name=_("Assigned to"),
    )
    notes = models.TextField(_("Internal notes"), blank=True, help_text=_("Visible to staff only"))
    created_ip = models.GenericIPAddressField(_("Created from IP"), null=True, blank=True)
    confirmation_number = models.CharField(
        _("Confirmation number"),
        max_length=10,
        unique=True,
        default=_generate_confirmation_number,
        editable=False,
    )

    class Meta:
        verbose_name = _("Inquiry")
        verbose_name_plural = _("Inquiries")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.confirmation_number}] {self.full_name} – {self.get_inquiry_type_display()}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def category_display(self) -> str:
        if self.category:
            return self.category.name
        if self.custom_category:
            return self.custom_category
        if self.tour and self.tour.category:
            return self.tour.category.name
        return "—"

    @property
    def total_travelers(self) -> int:
        return self.num_adults + self.num_children

    def get_client_ip(self, request) -> str:
        """Extract real IP from request (supports reverse proxy)."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
