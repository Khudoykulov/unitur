"""Dashboard-specific models: audit log and notifications."""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AdminLoginLog(models.Model):
    """Audit trail for dashboard login events."""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="login_logs",
        verbose_name=_("User"),
    )
    email = models.EmailField(_("Email"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    user_agent = models.TextField(_("User agent"), blank=True)
    success = models.BooleanField(_("Success"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Admin login log")
        verbose_name_plural = _("Admin login logs")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"[{status}] {self.email} @ {self.ip_address} — {self.created_at:%Y-%m-%d %H:%M}"


class DashboardNotification(models.Model):
    """In-dashboard notification for staff."""

    LEVEL_CHOICES = [
        ("info", _("Info")),
        ("success", _("Success")),
        ("warning", _("Warning")),
        ("danger", _("Danger")),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="dashboard_notifications",
        verbose_name=_("Recipient"),
        help_text=_("Null = broadcast to all staff"),
    )
    level = models.CharField(_("Level"), max_length=10, choices=LEVEL_CHOICES, default="info")
    title = models.CharField(_("Title"), max_length=200)
    message = models.TextField(_("Message"), blank=True)
    link = models.CharField(_("Link"), max_length=300, blank=True)
    is_read = models.BooleanField(_("Read"), default=False)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Dashboard notification")
        verbose_name_plural = _("Dashboard notifications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.title}"
