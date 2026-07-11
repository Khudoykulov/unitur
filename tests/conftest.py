"""Shared pytest fixtures."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.utils import translation


@pytest.fixture(autouse=True)
def _reset_language():
    """Reset the active translation to the default between tests.

    LocaleMiddleware activates a language per request and leaves it active;
    without resetting, a request in one test can change how modeltranslation
    resolves fields for objects built in the next test.
    """
    translation.activate(settings.LANGUAGE_CODE)
    yield
    translation.deactivate()


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the (shared, process-wide) LocMemCache between tests.

    Views like the tour list use ``cache_page``; without this, a cached
    response from an earlier test with the same URL leaks into the next one
    (and cached responses carry no ``.context`` in the test client).
    """
    cache.clear()
    yield
    cache.clear()
