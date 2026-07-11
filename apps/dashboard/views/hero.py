"""Dashboard CRUD for hero slides (rotating page background images)."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.models import HeroSlide
from apps.dashboard.forms import HeroSlideForm
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin


class HeroSlideListView(ManagerRequiredMixin, ListView):
    model = HeroSlide
    template_name = "dashboard/hero/list.html"
    context_object_name = "slides"
    paginate_by = 30

    def get_queryset(self):
        qs = HeroSlide.objects.all()
        page = self.request.GET.get("page", "")
        if page:
            qs = qs.filter(page=page)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_choices"] = HeroSlide.PAGE_CHOICES
        ctx["selected_page"] = self.request.GET.get("page", "")
        return ctx


class HeroSlideCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = HeroSlide
    form_class = HeroSlideForm
    template_name = "dashboard/hero/form.html"
    success_url = reverse_lazy("dashboard:hero_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action("CREATE", "HeroSlide", self.object.pk)
        messages.success(self.request, gettext("Hero image added."))
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Hero Image")
        return ctx


class HeroSlideEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = HeroSlide
    form_class = HeroSlideForm
    template_name = "dashboard/hero/form.html"
    success_url = reverse_lazy("dashboard:hero_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action("UPDATE", "HeroSlide", self.object.pk)
        messages.success(self.request, gettext("Hero image updated."))
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Edit Hero Image")
        return ctx


class HeroSlideDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = HeroSlide
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:hero_list")

    def form_valid(self, form):
        self.log_action("DELETE", "HeroSlide", self.object.pk)
        messages.success(self.request, gettext("Hero image deleted."))
        return super().form_valid(form)
