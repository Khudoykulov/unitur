"""Core abstract base models shared across all apps."""

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Abstract base providing created_at / updated_at timestamps."""

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SEOMixin(models.Model):
    """Abstract mixin adding SEO meta fields."""

    seo_title = models.CharField(_("SEO title"), max_length=70, blank=True)
    seo_description = models.CharField(_("SEO description"), max_length=160, blank=True)

    class Meta:
        abstract = True


class PublishableMixin(models.Model):
    """Abstract mixin adding is_active / is_featured flags."""

    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    is_featured = models.BooleanField(_("Featured"), default=False, db_index=True)

    class Meta:
        abstract = True


class OrderedMixin(models.Model):
    """Abstract mixin adding order field for manual sorting."""

    order = models.PositiveSmallIntegerField(_("Display order"), default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["order"]


class HeroSlide(TimeStampedModel, OrderedMixin):
    """A background image for a page's rotating hero slideshow.

    Managed from the dashboard so staff can upload/replace the rotating
    background images without code changes.
    """

    PAGE_CHOICES = [
        ("ichki_turlar", _("Domestic Tours")),
        ("home", _("Home")),
        ("tours", _("Tours")),
        ("destinations", _("Destinations")),
        ("hotels", _("Hotels")),
        ("guides", _("Guides")),
        ("faq", _("FAQ")),
    ]

    page = models.CharField(
        _("Page"), max_length=32, choices=PAGE_CHOICES,
        default="ichki_turlar", db_index=True,
        help_text=_("Which page's hero slideshow this image belongs to."),
    )
    image = models.ImageField(_("Image"), upload_to="hero_slides/")
    alt = models.CharField(_("Alt text"), max_length=200, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Hero slide")
        verbose_name_plural = _("Hero slides")
        ordering = ["page", "order", "-created_at"]

    def __str__(self) -> str:
        return f"{self.get_page_display()} — {self.alt or self.image.name}"


class SiteSettings(TimeStampedModel):
    """
    Global site settings managed from admin panel.

    Includes social media links, contact info, and other site-wide configuration.
    Only one instance should exist - singleton pattern.
    """

    # Site Information
    site_name = models.CharField(_("Site name"), max_length=200, default="UNITUR")
    site_tagline = models.CharField(_("Tagline"), max_length=500, blank=True)
    site_logo = models.ImageField(_("Logo"), upload_to="site/", blank=True, null=True)
    site_favicon = models.ImageField(_("Favicon"), upload_to="site/", blank=True, null=True)

    # Contact Information
    phone = models.CharField(_("Phone"), max_length=30, blank=True)
    phone_secondary = models.CharField(_("Secondary phone"), max_length=30, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    email_secondary = models.EmailField(_("Secondary email"), blank=True)
    address = models.TextField(_("Address"), blank=True)
    working_hours = models.CharField(_("Working hours"), max_length=200, blank=True)

    # Location
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)

    # Social Media Links
    facebook_url = models.URLField(_("Facebook URL"), blank=True)
    instagram_url = models.URLField(_("Instagram URL"), blank=True)
    telegram_url = models.URLField(_("Telegram URL"), blank=True)
    youtube_url = models.URLField(_("YouTube URL"), blank=True)
    twitter_url = models.URLField(_("Twitter URL"), blank=True)
    linkedin_url = models.URLField(_("LinkedIn URL"), blank=True)
    whatsapp_number = models.CharField(_("WhatsApp number"), max_length=30, blank=True,
                                      help_text=_("Format: +998901234567"))

    # SEO & Analytics
    google_analytics_id = models.CharField(_("Google Analytics ID"), max_length=50, blank=True)
    facebook_pixel_id = models.CharField(_("Facebook Pixel ID"), max_length=50, blank=True)
    meta_keywords = models.TextField(_("Meta keywords"), blank=True,
                                     help_text=_("Comma-separated keywords"))

    # Footer Text
    footer_text = models.TextField(_("Footer text"), blank=True)
    copyright_text = models.CharField(_("Copyright text"), max_length=200, blank=True,
                                      default="© 2024 UNITUR. All rights reserved.")

    class Meta:
        verbose_name = _("Site settings")
        verbose_name_plural = _("Site settings")

    def __str__(self) -> str:
        return "Site Settings"

    def save(self, *args, **kwargs) -> None:
        # Singleton pattern - only one instance allowed
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        # Prevent deletion
        pass

    @classmethod
    def load(cls):
        """Load the singleton instance, create if doesn't exist."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class FAQCategory(OrderedMixin):
    """Category for FAQ grouping (e.g., General, Booking, Tours, Visa)."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    icon = models.CharField(_("Tabler icon name"), max_length=60, default="help", blank=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("FAQ category")
        verbose_name_plural = _("FAQ categories")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FAQ(TimeStampedModel, OrderedMixin):
    """
    Frequently Asked Questions.

    Displayed on the FAQ page with expandable accordion interface.
    """

    category = models.ForeignKey(
        FAQCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faqs",
        verbose_name=_("Category"),
        help_text=_("Group similar questions together")
    )
    question = models.CharField(_("Question"), max_length=500)
    answer = models.TextField(_("Answer"))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ["category", "order", "-created_at"]

    def __str__(self) -> str:
        return self.question

