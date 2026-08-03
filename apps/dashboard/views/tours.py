"""Dashboard CRUD views for Tours."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.tours.models import Tour, TourCategory


class TourListView(ManagerRequiredMixin, ListView):
    model = Tour
    template_name = "dashboard/tours/list.html"
    context_object_name = "tours"
    paginate_by = 20

    def get_queryset(self):
        qs = Tour.objects.select_related("category").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(title__icontains=q)
        cat = self.request.GET.get("category", "")
        if cat:
            qs = qs.filter(category__slug=cat)
        status = self.request.GET.get("status", "")
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = TourCategory.objects.all()
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["selected_status"] = self.request.GET.get("status", "")
        return ctx


from django.db import transaction
from apps.dashboard.forms import TourDayFormSet


class _TourFormMixin:
    """Shared formset handling for Tour create and edit views."""

    model = Tour
    template_name = "dashboard/tours/form.html"
    success_url = reverse_lazy("dashboard:tours_list")
    fields = [
        "title", "category", "destinations", "duration_days",
        "group_size_min", "group_size_max", "difficulty",
        "price_per_person", "price_currency", "discount_percent",
        "cover_image", "overview", "includes", "excludes",
        "important_notes", "is_featured",
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            ctx["days"] = TourDayFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            ctx["days"] = TourDayFormSet(instance=self.object)
        ctx["categories"] = TourCategory.objects.all()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data(form=form)
        days = ctx["days"]
        if not days.is_valid():
            return self.render_to_response(ctx)
        with transaction.atomic():
            self.object = form.save()
            days.instance = self.object
            saved_days = days.save(commit=False)
            for day in saved_days:
                if day.title and day.title.strip():
                    day.save()
            days.save_m2m()
            for obj_to_delete in days.deleted_objects:
                obj_to_delete.delete()

            # Re-sequence day numbers sequentially for remaining active days
            active_days = self.object.days.all().order_by("day_number", "id")
            for idx, d in enumerate(active_days, start=1):
                if d.day_number != idx:
                    d.day_number = idx
                    d.save(update_fields=["day_number"])

        autofill_translations(self.object)
        self.log_action(getattr(self, "audit_action", "SAVE"), "Tour", self.object.pk)
        messages.success(self.request, getattr(self, "success_message", gettext("Tour saved.")))
        return redirect(self.success_url)


class TourCreateView(_TourFormMixin, AuditMixin, ManagerRequiredMixin, CreateView):
    audit_action = "CREATE"
    success_message = _("Tour created.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Create Tour")
        return ctx


class TourEditView(_TourFormMixin, AuditMixin, ManagerRequiredMixin, UpdateView):
    audit_action = "UPDATE"
    success_message = _("Tour updated.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(title)s") % {"title": self.object.title}
        return ctx


class TourDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Tour
    success_url = reverse_lazy("dashboard:tours_list")
    # GET shows the confirmation page; POST (list button or that page) deletes.
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "Tour", self.object.pk)
        messages.success(self.request, gettext("Tour '%(title)s' deleted.") % {"title": self.object.title})
        return super().form_valid(form)
