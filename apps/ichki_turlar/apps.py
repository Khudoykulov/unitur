from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IchkiTurlarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ichki_turlar"
    verbose_name = _("Domestic Tours")
