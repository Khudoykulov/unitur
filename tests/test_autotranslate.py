"""Tests for dashboard auto-translation of content."""

import pytest
from django.core.management import call_command

from apps.dashboard import autotranslate
from apps.dashboard.autotranslate import autofill_translations
from tests import factories as f

pytestmark = pytest.mark.django_db


class _FakeTranslator:
    def __init__(self, source="auto", target="en"):
        self.target = target

    def translate(self, text):
        return f"{self.target}:{text}"


def test_translated_field_detection():
    from apps.tours.models import Tour
    fields = autotranslate._translated_fields(Tour)
    assert "title" in fields
    assert "overview" in fields


def test_noop_when_disabled(settings):
    settings.AUTO_TRANSLATE = False
    tour = f.make_tour(title="Silk Road")
    autofill_translations(tour)  # must not raise / must not hit network
    tour.refresh_from_db()
    assert tour.title_ru in (None, "")


def test_fills_other_languages_when_enabled(settings, monkeypatch):
    settings.AUTO_TRANSLATE = True

    class FakeTranslator:
        def __init__(self, source="auto", target="en"):
            self.target = target

        def translate(self, text):
            return f"{self.target}:{text}"

    # autotranslate imports GoogleTranslator from deep_translator inside the
    # function; patch it at the source module.
    import deep_translator
    monkeypatch.setattr(deep_translator, "GoogleTranslator", FakeTranslator)

    tour = f.make_tour(title="Silk Road")
    autofill_translations(tour, source_lang="en")
    tour.refresh_from_db()

    assert tour.title_ru == "ru:Silk Road"
    assert tour.title_uz == "uz:Silk Road"
    assert tour.title_ja == "ja:Silk Road"
    # Source language stays as entered.
    assert tour.title_en == "Silk Road"


def test_refreshes_targets_on_resave(settings, monkeypatch):
    """Pure auto mode: re-saving re-translates targets from the source so
    edits to the source text propagate to every language."""
    settings.AUTO_TRANSLATE = True

    class FakeTranslator:
        def __init__(self, source="auto", target="en"):
            self.target = target

        def translate(self, text):
            return f"{self.target}:{text}"

    import deep_translator
    monkeypatch.setattr(deep_translator, "GoogleTranslator", FakeTranslator)

    tour = f.make_tour(title="Silk Road")
    tour.title_ru = "stale"  # an out-of-date translation
    tour.save()

    autofill_translations(tour, source_lang="en")
    tour.refresh_from_db()
    assert tour.title_ru == "ru:Silk Road"   # refreshed from source
    assert tour.title_uz == "uz:Silk Road"


def test_translate_content_command(settings, monkeypatch):
    """The bulk command back-fills translations even when AUTO_TRANSLATE is off
    (it passes force=True)."""
    settings.AUTO_TRANSLATE = False  # command must still work

    import deep_translator
    monkeypatch.setattr(deep_translator, "GoogleTranslator", _FakeTranslator)

    tour = f.make_tour(title="Registan Square")
    call_command("translate_content", models=["tours.Tour"], overwrite=True, source="en")

    tour.refresh_from_db()
    assert tour.title_ru == "ru:Registan Square"
    assert tour.title_uz == "uz:Registan Square"
