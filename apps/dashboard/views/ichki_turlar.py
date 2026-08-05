"""Dashboard CRUD for "Ichki Turlar" — domestic multi-city tours.

These are regular :class:`~apps.tours.models.Tour` objects distinguished by
having more than one itinerary stop (``TourStop``). The site's "Ichki Turlar"
page lists exactly these, so this section lets staff build them — base tour
details plus the ordered list of city stops — from the dashboard.
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.forms import IchkiTurForm, TourDayFormSet, TourStopFormSet
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.tours.models import Tour, TourCategory


class IchkiTurListView(ManagerRequiredMixin, ListView):
    template_name = "dashboard/ichki_turlar/list.html"
    context_object_name = "tours"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Tour.objects.annotate(num_stops=Count("stops"))
            .filter(num_stops__gt=1)
            .select_related("category")
            .prefetch_related("stops__city")
            .order_by("-created_at")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class _StopsFormMixin:
    """Shared formset handling for the create and edit views."""

    model = Tour
    form_class = IchkiTurForm
    template_name = "dashboard/ichki_turlar/form.html"
    success_url = reverse_lazy("dashboard:ichki_turlar_list")
    audit_action = "SAVE"
    success_message = _("Domestic tour saved.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            ctx["stops"] = TourStopFormSet(self.request.POST, instance=self.object)
            ctx["days"] = TourDayFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            ctx["stops"] = TourStopFormSet(instance=self.object)
            ctx["days"] = TourDayFormSet(instance=self.object)
        ctx["categories"] = TourCategory.objects.all()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        stops = ctx["stops"]
        days = ctx["days"]
        if not stops.is_valid() or not days.is_valid():
            return self.render_to_response(ctx)
        with transaction.atomic():
            self.object = form.save()
            stops.instance = self.object
            stops.save()
            days.instance = self.object
            days.save()
            # Re-sequence day numbers sequentially for remaining active days
            active_days = self.object.days.all().order_by("day_number", "id")
            for idx, d in enumerate(active_days, start=1):
                if d.day_number != idx:
                    d.day_number = idx
                    d.save(update_fields=["day_number"])

        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)
        self.log_action(self.audit_action, "IchkiTur", self.object.pk)
        messages.success(self.request, self.success_message)
        return redirect(self.success_url)


class IchkiTurCreateView(_StopsFormMixin, AuditMixin, ManagerRequiredMixin, CreateView):
    audit_action = "CREATE"
    success_message = _("Domestic tour created.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Create Domestic Tour")
        return ctx


class IchkiTurEditView(_StopsFormMixin, AuditMixin, ManagerRequiredMixin, UpdateView):
    audit_action = "UPDATE"
    success_message = _("Domestic tour updated.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(title)s") % {"title": self.object.title}
        return ctx


class IchkiTurDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Tour
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:ichki_turlar_list")

    def form_valid(self, form):
        self.log_action("DELETE", "IchkiTur", self.object.pk)
        messages.success(
            self.request,
            gettext("Domestic tour '%(title)s' deleted.") % {"title": self.object.title},
        )
        return super().form_valid(form)
