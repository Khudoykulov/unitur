"""Register the DomesticCity proxy for translation (mirrors City)."""

from modeltranslation.translator import TranslationOptions, register

from .models import DomesticCity


@register(DomesticCity)
class DomesticCityTranslationOptions(TranslationOptions):
    fields = ("name", "overview", "seo_title", "seo_description")
