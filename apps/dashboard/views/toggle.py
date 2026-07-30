"""Quick "show / hide" toggle for a record's ``is_active`` flag.

The create/edit forms deliberately no longer expose ``is_active`` (new records
are always published). To keep the ability to *temporarily* hide a record from
the public site without deleting it, each list row has a small toggle button
that POSTs here and flips the flag in one click.
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext
from django.views import View

from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.destinations.models import Attraction, City, Country
from apps.hotels.models import Hotel
from apps.tours.models import Tour

# Which models can be toggled, keyed by the slug used in the URL. Each entry
# maps to (model, list-view url name) so we can bounce back to the right page.
TOGGLEABLE = {
    "tour": (Tour, "dashboard:tours_list"),
    "ichki-tur": (Tour, "dashboard:ichki_turlar_list"),
    "city": (City, "dashboard:cities_list"),
    "hotel": (Hotel, "dashboard:hotels_list"),
    "country": (Country, "dashboard:destinations_list"),
    "attraction": (Attraction, "dashboard:attractions_list"),
}


class ToggleActiveView(AuditMixin, ManagerRequiredMixin, View):
    """Flip ``is_active`` or ``is_published`` for a single record (POST only)."""

    def post(self, request, model, pk):
        entry = TOGGLEABLE.get(model)
        if entry is None:
            raise Http404("Unknown model")
        model_cls, list_url = entry

        obj = get_object_or_404(model_cls, pk=pk)
        if hasattr(obj, "is_active"):
            obj.is_active = not obj.is_active
            obj.save(update_fields=["is_active"])
            is_vis = obj.is_active
        elif hasattr(obj, "is_published"):
            obj.is_published = not obj.is_published
            obj.save(update_fields=["is_published"])
            is_vis = obj.is_published
        else:
            is_vis = True

        self.log_action("TOGGLE_ACTIVE", model_cls.__name__, obj.pk)
        label = str(obj)
        if is_vis:
            messages.success(request, gettext("'%(name)s' is now visible on the site.") % {"name": label})
        else:
            messages.success(request, gettext("'%(name)s' is now hidden from the site.") % {"name": label})

        return redirect(request.META.get("HTTP_REFERER") or list_url)


class ToggleFeaturedView(AuditMixin, ManagerRequiredMixin, View):
    """Flip ``is_featured`` for a single record (POST only)."""

    def post(self, request, model, pk):
        entry = TOGGLEABLE.get(model)
        if entry is None:
            raise Http404("Unknown model")
        model_cls, list_url = entry

        obj = get_object_or_404(model_cls, pk=pk)
        if hasattr(obj, "is_featured"):
            obj.is_featured = not obj.is_featured
            obj.save(update_fields=["is_featured"])
            is_feat = obj.is_featured
        else:
            is_feat = False

        self.log_action("TOGGLE_FEATURED", model_cls.__name__, obj.pk)
        label = str(obj)
        if is_feat:
            messages.success(request, gettext("'%(name)s' is now featured on the main page.") % {"name": label})
        else:
            messages.success(request, gettext("'%(name)s' is no longer featured on the main page.") % {"name": label})

        return redirect(request.META.get("HTTP_REFERER") or list_url)
