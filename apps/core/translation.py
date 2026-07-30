"""modeltranslation registration for core models."""

from modeltranslation.translator import TranslationOptions, register

from .models import HeroSlide, SiteSettings, FAQ, FAQCategory


@register(HeroSlide)
class HeroSlideTranslationOptions(TranslationOptions):
    fields = ("alt",)


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("site_tagline", "address", "working_hours", "footer_text", "copyright_text")


@register(FAQCategory)
class FAQCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ("question", "answer")

