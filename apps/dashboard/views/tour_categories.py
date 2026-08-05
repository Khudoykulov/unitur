"""Dashboard CRUD views for Tour Categories."""

from django.contrib import messages
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.forms import TourCategoryForm
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.tours.models import TourCategory


class TourCategoryListView(ManagerRequiredMixin, ListView):
    model = TourCategory
    template_name = "dashboard/tour_categories/list.html"
    context_object_name = "categories"
    paginate_by = 30

    def get_queryset(self):
        return (
            TourCategory.objects.annotate(tour_count=Count("tours"))
            .order_by("order", "name")
        )


class TourCategoryCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = TourCategory
    form_class = TourCategoryForm
    template_name = "dashboard/tour_categories/form.html"
    success_url = reverse_lazy("dashboard:tour_categories_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)
        self.log_action("CREATE", "TourCategory", self.object.pk)
        messages.success(self.request, gettext("Category '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Category")
        return ctx


class TourCategoryEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = TourCategory
    form_class = TourCategoryForm
    template_name = "dashboard/tour_categories/form.html"
    success_url = reverse_lazy("dashboard:tour_categories_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)
        self.log_action("UPDATE", "TourCategory", self.object.pk)
        messages.success(self.request, gettext("Category '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        return ctx


class TourCategoryDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = TourCategory
    success_url = reverse_lazy("dashboard:tour_categories_list")
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "TourCategory", self.object.pk)
        messages.success(self.request, gettext("Category '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)
