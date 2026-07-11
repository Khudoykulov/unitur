"""
User profile and preferences model.

Extends Django's built-in User with profile info, saved tours, and preferences.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

User = get_user_model()


class UserProfile(TimeStampedModel):
    """Extended profile data for registered users."""

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("uz", "O'zbekcha"),
        ("ru", "Русский"),
        ("it", "Italiano"),
        ("es", "Español"),
        ("ja", "日本語"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name=_("User")
    )
    avatar = models.ImageField(_("Avatar"), upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(_("Bio"), blank=True, max_length=500)
    phone = models.CharField(_("Phone"), max_length=30, blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    preferred_language = models.CharField(
        _("Preferred language"), max_length=5, choices=LANGUAGE_CHOICES, default="en"
    )
    saved_tours = models.ManyToManyField(
        "tours.Tour",
        related_name="saved_by",
        verbose_name=_("Saved tours"),
        blank=True,
    )
    newsletter_subscribed = models.BooleanField(_("Newsletter subscribed"), default=True)

    class Meta:
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")

    def __str__(self) -> str:
        return f"Profile of {self.user}"

    def get_absolute_url(self) -> str:
        return reverse("accounts:profile")


class AdminLoginLog(TimeStampedModel):
    """Audit trail for staff logins via the hidden keyboard-shortcut form."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_logins",
        verbose_name=_("User"),
    )
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)

    class Meta:
        verbose_name = _("Admin login log")
        verbose_name_plural = _("Admin login logs")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} @ {self.created_at:%Y-%m-%d %H:%M}"
