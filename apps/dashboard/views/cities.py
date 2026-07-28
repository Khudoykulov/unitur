"""Dashboard CRUD for domestic (Uzbek) cities.

These are the building blocks for Ichki Tur itineraries — the city dropdown in
the domestic-tour form only lists cities created here. Mirrors the Django-admin
``DomesticCity`` section but inside the custom dashboard.
"""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.forms import DOMESTIC_COUNTRY, DomesticCityForm
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.destinations.models import City


class DomesticCityListView(ManagerRequiredMixin, ListView):
    template_name = "dashboard/cities/list.html"
    context_object_name = "cities"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            City.objects.filter(country__name_en__icontains=DOMESTIC_COUNTRY)
            .select_related("country")
            .order_by("name")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class DomesticCityCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = City
    form_class = DomesticCityForm
    template_name = "dashboard/cities/form.html"
    success_url = reverse_lazy("dashboard:cities_list")

    def form_valid(self, form):
        # Attach Uzbekistan before the instance is written to the DB so the
        # NOT NULL constraint on country_id is never violated.
        from apps.destinations.models import Country as _Country
        if form.instance.country_id is None:
            uzbekistan = _Country.objects.filter(
                name_en__icontains=DOMESTIC_COUNTRY
            ).first()
            if uzbekistan:
                form.instance.country = uzbekistan
            else:
                messages.error(self.request, gettext("Uzbekistan country not found in database."))
                return self.form_invalid(form)
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("CREATE", "DomesticCity", self.object.pk)
        messages.success(self.request, gettext("City '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add City")
        return ctx


class DomesticCityEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = City
    form_class = DomesticCityForm
    template_name = "dashboard/cities/form.html"
    success_url = reverse_lazy("dashboard:cities_list")

    def get_queryset(self):
        return City.objects.filter(country__name_en__icontains=DOMESTIC_COUNTRY)

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("UPDATE", "DomesticCity", self.object.pk)
        messages.success(self.request, gettext("City '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        return ctx


class DomesticCityDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = City
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:cities_list")

    def get_queryset(self):
        return City.objects.filter(country__name_en__icontains=DOMESTIC_COUNTRY)

    def form_valid(self, form):
        self.log_action("DELETE", "DomesticCity", self.object.pk)
        messages.success(self.request, gettext("City '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)
