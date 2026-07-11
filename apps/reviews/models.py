"""
Review models for tours, hotels, and the agency in general.

Reviews go through a moderation queue before appearing publicly.
"""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

User = get_user_model()


class Review(TimeStampedModel):
    """
    A customer review and star rating.

    Can be linked to a tour, hotel, or be a general agency review.
    Reviews must be approved by staff before becoming public.
    """

    STATUS_CHOICES = [
        ("pending", _("Pending moderation")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
    ]

    REVIEW_TYPE_CHOICES = [
        ("tour", _("Tour Review")),
        ("hotel", _("Hotel Review")),
        ("general", _("General Review")),
    ]

    review_type = models.CharField(
        _("Review type"), max_length=10, choices=REVIEW_TYPE_CHOICES, default="general"
    )

    # Linked items (mutually exclusive, only one should be set)
    tour = models.ForeignKey(
        "tours.Tour",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name=_("Tour"),
    )
    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name=_("Hotel"),
    )

    # Reviewer
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name=_("Registered user"),
    )
    guest_name = models.CharField(_("Guest name"), max_length=100, blank=True)
    guest_country = models.CharField(_("Guest country"), max_length=100, blank=True)

    # Review content
    rating = models.PositiveSmallIntegerField(
        _("Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
    )
    title = models.CharField(_("Review title"), max_length=200)
    body = models.TextField(_("Review body"))
    travel_date = models.DateField(_("Travel date"), null=True, blank=True)

    # Moderation
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default="pending")
    is_verified = models.BooleanField(
        _("Verified purchase"), default=False, help_text=_("Set by staff for confirmed bookings")
    )
    helpful_count = models.PositiveIntegerField(_("Helpful votes"), default=0)

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        reviewer = self.user.get_full_name() if self.user else self.guest_name
        return f"{reviewer} – {'★' * self.rating} – {self.title[:40]}"

    @property
    def reviewer_name(self) -> str:
        if self.user:
            return self.user.get_full_name() or self.user.email
        return self.guest_name or "Anonymous"

    @property
    def star_range(self) -> range:
        return range(self.rating)

    @property
    def empty_star_range(self) -> range:
        return range(5 - self.rating)

    def approve(self) -> None:
        self.status = "approved"
        self.save(update_fields=["status"])

    def reject(self) -> None:
        self.status = "rejected"
        self.save(update_fields=["status"])
