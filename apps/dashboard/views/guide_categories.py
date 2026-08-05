"""Dashboard CRUD views for Guide Categories."""

from django.contrib import messages
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.guides.models import GuideCategory


class GuideCategoryListView(ManagerRequiredMixin, ListView):
    model = GuideCategory
    template_name = "dashboard/guide_categories/list.html"
    context_object_name = "categories"
    paginate_by = 30

    def get_queryset(self):
        return (
            GuideCategory.objects.annotate(article_count=Count("articles"))
            .order_by("order", "name")
        )


class GuideCategoryCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = GuideCategory
    template_name = "dashboard/guide_categories/form.html"
    success_url = reverse_lazy("dashboard:guide_categories_list")
    fields = ["name", "icon", "description"]

    def form_valid(self, form):
        response = super().form_valid(form)
        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)
        self.log_action("CREATE", "GuideCategory", self.object.pk)
        messages.success(self.request, gettext("Category '%(name)s' created.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Guide Category")
        return ctx


class GuideCategoryEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = GuideCategory
    template_name = "dashboard/guide_categories/form.html"
    success_url = reverse_lazy("dashboard:guide_categories_list")
    fields = ["name", "icon", "description"]

    def form_valid(self, form):
        response = super().form_valid(form)
        lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
        autofill_translations(self.object, source_lang=lang, overwrite=False)
        self.log_action("UPDATE", "GuideCategory", self.object.pk)
        messages.success(self.request, gettext("Category '%(name)s' updated.") % {"name": self.object.name})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(name)s") % {"name": self.object.name}
        return ctx


class GuideCategoryDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = GuideCategory
    success_url = reverse_lazy("dashboard:guide_categories_list")
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "GuideCategory", self.object.pk)
        messages.success(self.request, gettext("Category '%(name)s' deleted.") % {"name": self.object.name})
        return super().form_valid(form)
