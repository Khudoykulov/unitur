"""Dashboard CRUD views for Destinations (Countries & Cities)."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from django.db.models import Count

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.forms import ContinentForm
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.destinations.models import City, Continent, Country


class DestinationListView(ManagerRequiredMixin, ListView):
    model = Country
    template_name = "dashboard/destinations/list.html"
    context_object_name = "countries"
    paginate_by = 30

    def get_queryset(self):
        qs = Country.objects.select_related("continent").order_by("name")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["continents"] = Continent.objects.all()
        return ctx


class CountryCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = Country
    template_name = "dashboard/destinations/country_form.html"
    success_url = reverse_lazy("dashboard:destinations_list")
    fields = ["name", "slug", "continent", "cover_image", "overview"]

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("CREATE", "Country", self.object.pk)
        messages.success(self.request, gettext("Country '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Country")
        return ctx


class CountryEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Country
    template_name = "dashboard/destinations/country_form.html"
    success_url = reverse_lazy("dashboard:destinations_list")
    fields = ["name", "slug", "continent", "cover_image", "overview"]

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("UPDATE", "Country", self.object.pk)
        messages.success(self.request, gettext("Country '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        return ctx


class CountryDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Country
    success_url = reverse_lazy("dashboard:destinations_list")
    # GET shows the confirmation page; POST (list button or that page) deletes.
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "Country", self.object.pk)
        messages.success(self.request, gettext("Country '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)


class ContinentListView(ManagerRequiredMixin, ListView):
    model = Continent
    template_name = "dashboard/continents/list.html"
    context_object_name = "continents"
    paginate_by = 30

    def get_queryset(self):
        return (
            Continent.objects.annotate(country_count=Count("countries"))
            .order_by("order", "name")
        )


class ContinentCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = Continent
    form_class = ContinentForm
    template_name = "dashboard/continents/form.html"
    success_url = reverse_lazy("dashboard:continents_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("CREATE", "Continent", self.object.pk)
        messages.success(self.request, gettext("Continent '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Continent")
        return ctx


class ContinentEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Continent
    form_class = ContinentForm
    template_name = "dashboard/continents/form.html"
    success_url = reverse_lazy("dashboard:continents_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("UPDATE", "Continent", self.object.pk)
        messages.success(self.request, gettext("Continent '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        return ctx


class ContinentDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Continent
    success_url = reverse_lazy("dashboard:continents_list")
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "Continent", self.object.pk)
        messages.success(self.request, gettext("Continent '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)
