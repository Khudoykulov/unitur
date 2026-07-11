"""Dashboard views for Site Settings and FAQ management."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from apps.core.models import SiteSettings, FAQ
from apps.dashboard.mixins import StaffRequiredMixin


class SiteSettingsEditView(StaffRequiredMixin, UpdateView):
    """Edit global site settings (singleton)."""

    model = SiteSettings
    template_name = "dashboard/settings/edit.html"
    fields = [
        "site_name", "site_tagline", "site_logo", "site_favicon",
        "phone", "phone_secondary", "email", "email_secondary",
        "address", "working_hours", "latitude", "longitude",
        "facebook_url", "instagram_url", "telegram_url", "youtube_url",
        "twitter_url", "linkedin_url", "whatsapp_number",
        "google_analytics_id", "facebook_pixel_id", "meta_keywords",
        "footer_text", "copyright_text"
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
        qs = FAQ.objects.all().order_by("category", "order", "-created_at")
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = FAQ.CATEGORY_CHOICES
        ctx["selected_category"] = self.request.GET.get("category", "")
        return ctx


class FAQCreateView(StaffRequiredMixin, CreateView):
    """Create a new FAQ."""

    model = FAQ
    template_name = "dashboard/faq/form.html"
    fields = ["category", "question", "answer", "is_active", "order"]
    success_url = reverse_lazy("dashboard:faq_list")

    def form_valid(self, form):
        messages.success(self.request, _("FAQ created successfully!"))
        return super().form_valid(form)


class FAQEditView(StaffRequiredMixin, UpdateView):
    """Edit an existing FAQ."""

    model = FAQ
    template_name = "dashboard/faq/form.html"
    fields = ["category", "question", "answer", "is_active", "order"]
    success_url = reverse_lazy("dashboard:faq_list")

    def form_valid(self, form):
        messages.success(self.request, _("FAQ updated successfully!"))
        return super().form_valid(form)


class FAQDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a FAQ."""

    model = FAQ
    template_name = "dashboard/faq/delete.html"
    success_url = reverse_lazy("dashboard:faq_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("FAQ deleted successfully!"))
        return super().delete(request, *args, **kwargs)
