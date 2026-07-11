"""
Guides / Travel Article models.

Articles with CKEditor rich text, categories, tags, and reading time.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

try:
    from ckeditor.fields import RichTextField
except ImportError:
    from django.db.models import TextField as RichTextField  # type: ignore[assignment]

from apps.core.models import OrderedMixin, PublishableMixin, SEOMixin, TimeStampedModel

User = get_user_model()


class Tag(models.Model):
    """A keyword tag that can be applied to articles."""

    name = models.CharField(_("Name"), max_length=80, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class GuideCategory(OrderedMixin):
    """Category for travel guide articles (e.g. Visa Tips, Food, Safety)."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    icon = models.CharField(_("Tabler icon name"), max_length=60, default="book", blank=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta(OrderedMixin.Meta):
        verbose_name = _("Guide category")
        verbose_name_plural = _("Guide categories")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("guides:by_category", kwargs={"slug": self.slug})


class Article(TimeStampedModel, SEOMixin, PublishableMixin):
    """
    A travel guide article authored by a staff user.

    Uses CKEditor for rich text content with structured reading time.
    """

    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=220, unique=True, blank=True)
    category = models.ForeignKey(
        GuideCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles",
        verbose_name=_("Category"),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles",
        verbose_name=_("Author"),
    )
    cover_image = models.ImageField(_("Cover image"), upload_to="articles/covers/", blank=True, null=True)
    excerpt = models.TextField(_("Excerpt"), blank=True, max_length=500)
    content = RichTextField(_("Content"))
    tags = models.ManyToManyField(Tag, related_name="articles", verbose_name=_("Tags"), blank=True)
    reading_time_minutes = models.PositiveSmallIntegerField(_("Reading time (min)"), default=5)
    views_count = models.PositiveIntegerField(_("Views count"), default=0, editable=False)
    is_published = models.BooleanField(_("Published"), default=False, db_index=True)
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ["-published_at", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("guides:detail", kwargs={"slug": self.slug})

    def publish(self) -> None:
        """Mark article as published and set timestamp."""
        self.is_published = True
        self.published_at = timezone.now()
        self.save(update_fields=["is_published", "published_at"])

    def increment_views(self) -> None:
        Article.objects.filter(pk=self.pk).update(views_count=models.F("views_count") + 1)
