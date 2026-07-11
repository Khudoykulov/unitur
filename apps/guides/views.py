"""Guide / article views: list, by category, and detail."""

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Article, GuideCategory


class ArticleListView(ListView):
    """Featured article + category grid + recent articles."""

    model = Article
    template_name = "guides/list.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        return (
            Article.objects.filter(is_published=True, is_active=True)
            .select_related("category", "author")
            .prefetch_related("tags")
            .order_by("-published_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = GuideCategory.objects.all().order_by("order")
        ctx["featured_article"] = (
            Article.objects.filter(is_published=True, is_featured=True, is_active=True)
            .select_related("category")
            .order_by("-published_at")
            .first()
        )
        return ctx


class ArticleByCategoryView(ListView):
    """Articles filtered by guide category."""

    model = Article
    template_name = "guides/list.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(GuideCategory, slug=self.kwargs["slug"])
        return (
            Article.objects.filter(category=self.category, is_published=True, is_active=True)
            .select_related("author")
            .order_by("-published_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_category"] = self.category
        ctx["categories"] = GuideCategory.objects.all().order_by("order")
        return ctx


class ArticleDetailView(DetailView):
    """Full article view with TOC and related articles."""

    model = Article
    template_name = "guides/detail.html"
    context_object_name = "article"
    slug_field = "slug"

    def get_queryset(self):
        return (
            Article.objects.filter(is_published=True, is_active=True)
            .select_related("category", "author")
            .prefetch_related("tags")
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        article = self.object
        ctx["related_articles"] = (
            Article.objects.filter(category=article.category, is_published=True, is_active=True)
            .exclude(pk=article.pk)
            .order_by("-published_at")[:3]
        )
        return ctx
