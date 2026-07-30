"""Dashboard views for FAQ Categories management."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from apps.core.models import FAQCategory
from apps.dashboard.autotranslate import AutoTranslateMixin
from apps.dashboard.forms import FAQCategoryForm
from apps.dashboard.mixins import StaffRequiredMixin


class FAQCategoryListView(StaffRequiredMixin, ListView):
    """List all FAQ Categories."""

    model = FAQCategory
    template_name = "dashboard/faq_categories/list.html"
    context_object_name = "categories"
    paginate_by = 30

    def get_queryset(self):
        return FAQCategory.objects.all().order_by("order", "name")


class FAQCategoryCreateView(AutoTranslateMixin, StaffRequiredMixin, CreateView):
    """Create a new FAQ Category with auto-translation across 6 languages."""

    model = FAQCategory
    form_class = FAQCategoryForm
    template_name = "dashboard/faq_categories/form.html"
    success_url = reverse_lazy("dashboard:faq_categories_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("FAQ category created successfully!"))
        return response


class FAQCategoryEditView(AutoTranslateMixin, StaffRequiredMixin, UpdateView):
    """Edit an existing FAQ Category with auto-translation across 6 languages."""

    model = FAQCategory
    form_class = FAQCategoryForm
    template_name = "dashboard/faq_categories/form.html"
    success_url = reverse_lazy("dashboard:faq_categories_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("FAQ category updated successfully!"))
        return response


class FAQCategoryDeleteView(StaffRequiredMixin, DeleteView):
    """Delete an FAQ Category."""

    model = FAQCategory
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:faq_categories_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("FAQ category deleted successfully!"))
        return super().delete(request, *args, **kwargs)
