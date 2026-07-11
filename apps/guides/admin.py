"""Admin configuration for guide articles with CKEditor and moderation."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import Article, GuideCategory, Tag


def publish_articles(modeladmin, request, queryset):
    for article in queryset:
        article.publish()
publish_articles.short_description = _("Publish selected articles")


def unpublish_articles(modeladmin, request, queryset):
    queryset.update(is_published=False)
unpublish_articles.short_description = _("Unpublish selected articles")


@admin.register(GuideCategory)
class GuideCategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug", "icon", "article_count", "order")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("order",)

    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = _("Articles")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(TranslationAdmin):
    list_display = (
        "title", "category", "author", "is_published_badge", "is_featured",
        "views_count", "reading_time_minutes", "published_at"
    )
    list_filter = ("is_published", "is_featured", "category", "author")
    search_fields = ("title", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views_count", "created_at", "updated_at")
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    actions = [publish_articles, unpublish_articles]

    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "author", "cover_image", "is_featured", "is_active")}),
        (_("Content"), {"fields": ("excerpt", "content", "tags", "reading_time_minutes")}),
        (_("Publishing"), {"fields": ("is_published", "published_at")}),
        (_("SEO"), {"fields": ("seo_title", "seo_description"), "classes": ("collapse",)}),
        (_("Stats"), {"fields": ("views_count", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def is_published_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="color:green">✓ Published</span>')
        return format_html('<span style="color:gray">Draft</span>')
    is_published_badge.short_description = _("Status")
