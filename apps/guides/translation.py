"""modeltranslation registration for guide models."""

from modeltranslation.translator import TranslationOptions, register

from .models import Article, GuideCategory, Tag


@register(GuideCategory)
class GuideCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ("title", "excerpt", "content", "seo_title", "seo_description")
