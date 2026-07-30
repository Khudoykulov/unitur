"""Dashboard views for Site Settings and FAQ management."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from apps.core.models import SiteSettings, FAQ, FAQCategory
from apps.dashboard.autotranslate import AutoTranslateMixin
from apps.dashboard.forms import FAQForm
from apps.dashboard.mixins import StaffRequiredMixin


class SiteSettingsEditView(StaffRequiredMixin, UpdateView):
    """Edit global site settings (singleton)."""

    model = SiteSettings
    template_name = "dashboard/settings/edit.html"
    fields = [
        "phone", "phone_secondary", "email", "email_secondary",
        "address", "working_hours", "latitude", "longitude",
        "facebook_url", "instagram_url", "telegram_url", "youtube_url",
        "twitter_url", "linkedin_url", "whatsapp_number",
    ]
    success_url = reverse_lazy("dashboard:settings_edit")

    def get_object(self, queryset=None):
        """Always return the singleton instance."""
        return SiteSettings.load()

    def form_valid(self, form):
        messages.success(self.request, _("Site settings updated successfully!"))
        return super().form_valid(form)


class FAQListView(StaffRequiredMixin, ListView):
    """List all FAQs with filtering by category."""

    model = FAQ
    template_name = "dashboard/faq/list.html"
    context_object_name = "faqs"
    paginate_by = 50

    def get_queryset(self):
        qs = FAQ.objects.select_related("category").all().order_by("category__order", "order", "-created_at")
        category_id = self.request.GET.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = FAQCategory.objects.all().order_by("order", "name")
        ctx["selected_category"] = self.request.GET.get("category", "")
        return ctx


class FAQCreateView(AutoTranslateMixin, StaffRequiredMixin, CreateView):
    """Create a new FAQ with auto-translation."""

    model = FAQ
    form_class = FAQForm
    template_name = "dashboard/faq/form.html"
    success_url = reverse_lazy("dashboard:faq_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("FAQ created successfully!"))
        return response


class FAQEditView(AutoTranslateMixin, StaffRequiredMixin, UpdateView):
    """Edit an existing FAQ with auto-translation."""

    model = FAQ
    form_class = FAQForm
    template_name = "dashboard/faq/form.html"
    success_url = reverse_lazy("dashboard:faq_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("FAQ updated successfully!"))
        return response



class FAQDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a FAQ."""

    model = FAQ
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:faq_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("FAQ deleted successfully!"))
        return super().delete(request, *args, **kwargs)

