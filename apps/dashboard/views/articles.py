"""Dashboard CRUD views for Articles (guides)."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.autotranslate import autofill_translations
from apps.dashboard.mixins import AuditMixin, ManagerRequiredMixin
from apps.guides.models import Article, GuideCategory


class ArticleListView(ManagerRequiredMixin, ListView):
    model = Article
    template_name = "dashboard/articles/list.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        qs = Article.objects.select_related("category", "author").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(title__icontains=q)
        cat = self.request.GET.get("category", "")
        if cat:
            qs = qs.filter(category__slug=cat)
        pub = self.request.GET.get("published", "")
        if pub == "1":
            qs = qs.filter(is_published=True)
        elif pub == "0":
            qs = qs.filter(is_published=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = GuideCategory.objects.all()
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_category"] = self.request.GET.get("category", "")
        return ctx


class ArticleCreateView(AuditMixin, ManagerRequiredMixin, CreateView):
    model = Article
    template_name = "dashboard/articles/form.html"
    success_url = reverse_lazy("dashboard:articles_list")
    fields = [
        "title", "category", "author", "cover_image",
        "excerpt", "content", "tags",
        "reading_time_minutes", "is_published",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("CREATE", "Article", self.object.pk)
        messages.success(self.request, gettext("Article '%(title)s' created.") % {"title": self.object.title})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Create Article")
        return ctx


class ArticleEditView(AuditMixin, ManagerRequiredMixin, UpdateView):
    model = Article
    template_name = "dashboard/articles/form.html"
    success_url = reverse_lazy("dashboard:articles_list")
    fields = [
        "title", "category", "author", "cover_image",
        "excerpt", "content", "tags",
        "reading_time_minutes", "is_published",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)
        autofill_translations(self.object)
        self.log_action("UPDATE", "Article", self.object.pk)
        messages.success(self.request, gettext("Article '%(title)s' updated.") % {"title": self.object.title})
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = gettext("Edit: %(title)s") % {"title": self.object.title}
        return ctx


class ArticleDeleteView(AuditMixin, ManagerRequiredMixin, DeleteView):
    model = Article
    success_url = reverse_lazy("dashboard:articles_list")
    # GET shows the confirmation page; POST (list button or that page) deletes.
    template_name = "dashboard/confirm_delete.html"

    def form_valid(self, form):
        self.log_action("DELETE", "Article", self.object.pk)
        messages.success(self.request, gettext("Article '%(title)s' deleted.") % {"title": self.object.title})
        return super().form_valid(form)
