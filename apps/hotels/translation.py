"""modeltranslation registration for hotel models."""

from modeltranslation.translator import TranslationOptions, register

from .models import Hotel, HotelAmenity, HotelCategory, HotelRoom


@register(HotelCategory)
class HotelCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(HotelAmenity)
class HotelAmenityTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ("name", "description", "seo_title", "seo_description")


@register(HotelRoom)
class HotelRoomTranslationOptions(TranslationOptions):
    fields = ("description",)
