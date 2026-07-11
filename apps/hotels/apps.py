from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HotelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hotels"
    verbose_name = _("Hotels")
