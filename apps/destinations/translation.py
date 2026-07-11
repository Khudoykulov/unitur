"""modeltranslation registration for destination models."""

from modeltranslation.translator import TranslationOptions, register

from .models import Attraction, City, CityImage, Continent, Country


@register(Continent)
class ContinentTranslationOptions(TranslationOptions):
    fields = ("name", "seo_title", "seo_description")


@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ("name", "overview", "visa_info", "best_time_to_visit", "seo_title", "seo_description")


@register(City)
class CityTranslationOptions(TranslationOptions):
    fields = ("name", "overview", "seo_title", "seo_description")


@register(Attraction)
class AttractionTranslationOptions(TranslationOptions):
    fields = ("name", "description", "opening_hours")


@register(CityImage)
class CityImageTranslationOptions(TranslationOptions):
    fields = ("caption", "description")
