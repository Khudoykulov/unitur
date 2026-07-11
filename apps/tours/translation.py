"""modeltranslation registration for tour models."""

from modeltranslation.translator import TranslationOptions, register

from .models import Tour, TourCategory, TourDay


@register(TourCategory)
class TourCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Tour)
class TourTranslationOptions(TranslationOptions):
    fields = ("title", "overview", "includes", "excludes", "important_notes", "seo_title", "seo_description")


@register(TourDay)
class TourDayTranslationOptions(TranslationOptions):
    fields = ("title", "description", "accommodation", "transport")
