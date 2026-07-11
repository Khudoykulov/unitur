"""Tests for the guides app: Tag, GuideCategory, Article."""

import pytest
from django.urls import reverse
from django.utils import timezone

from tests import factories as f

pytestmark = pytest.mark.django_db


class TestTag:
    def test_str_and_slug(self):
        tag = f.make_tag(name="Budget Travel")
        assert str(tag) == "Budget Travel"
        assert tag.slug == "budget-travel"


class TestGuideCategory:
    def test_str_and_slug(self):
        cat = f.make_guide_category(name="Visa Tips")
        assert str(cat) == "Visa Tips"
        assert cat.slug == "visa-tips"

    def test_get_absolute_url(self):
        cat = f.make_guide_category(name="Food", slug="food")
        assert cat.get_absolute_url() == reverse(
            "guides:by_category", kwargs={"slug": "food"}
        )


class TestArticle:
    def test_str_and_slug(self):
        article = f.make_article(title="Top 10 Beaches")
        assert str(article) == "Top 10 Beaches"
        assert article.slug == "top-10-beaches"

    def test_get_absolute_url(self):
        article = f.make_article(title="My Trip", slug="my-trip")
        assert article.get_absolute_url() == reverse(
            "guides:detail", kwargs={"slug": "my-trip"}
        )

    def test_published_at_set_on_save_when_published(self):
        article = f.make_article(is_published=True)
        assert article.published_at is not None

    def test_published_at_not_set_when_draft(self):
        article = f.make_article(is_published=False)
        assert article.published_at is None

    def test_published_at_preserved_if_already_set(self):
        earlier = timezone.now() - timezone.timedelta(days=5)
        article = f.make_article(is_published=True, published_at=earlier)
        assert article.published_at == earlier

    def test_publish_method(self):
        article = f.make_article(is_published=False)
        article.publish()
        article.refresh_from_db()
        assert article.is_published is True
        assert article.published_at is not None

    def test_increment_views(self):
        article = f.make_article()
        article.increment_views()
        article.refresh_from_db()
        assert article.views_count == 1
