"""Dashboard CRUD views for Article Tags."""

from django.contrib import messages
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.guides.models import Tag


class TagListView(ManagerRequiredMixin, ListView):
    model = Tag
    template_name = "dashboard/tags/list.html"
    context_object_name = "tags"
    paginate_by = 30

    def get_queryset(self):
        qs = Tag.objects.annotate(article_count=Count("articles")).order_by("name")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class TagCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = Tag
    template_name = "dashboard/tags/form.html"
    success_url = reverse_lazy("dashboard:tags_list")
    fields = ["name"]

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action("CREATE", "Tag", self.object.pk)
        messages.success(
            self.request,
            gettext("Tag '%(name)s' created.") % {"name": self.object.name},
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Add Tag")
        return ctx


class TagEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Tag
    template_name = "dashboard/tags/form.html"
    success_url = reverse_lazy("dashboard:tags_list")
    fields = ["name"]

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action("UPDATE", "Tag", self.object.pk)
        messages.success(
            self.request,
            gettext("Tag '%(name)s' updated.") % {"name": self.object.name},
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit tag: %(name)s") % {"name": self.object.name}
        return ctx


class TagDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Tag
    success_url = reverse_lazy("dashboard:tags_list")
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "Tag", self.object.pk)
        messages.success(
            self.request,
            gettext("Tag '%(name)s' deleted.") % {"name": self.object.name},
        )
        return super().form_valid(form)
