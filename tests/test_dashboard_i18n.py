"""The custom dashboard renders in the user's selected language."""

import pytest
from django.urls import reverse

from tests import factories as f

pytestmark = pytest.mark.django_db


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


def _set_lang(client, lang):
    client.cookies["django_language"] = lang


class TestDashboardI18n:
    def test_sidebar_translated_uz(self, super_client):
        _set_lang(super_client, "uz")
        html = super_client.get(reverse("dashboard:home")).content.decode()
        assert "Ichki Turlar" in html          # Domestic Tours
        assert "Chiqish" in html               # Sign Out

    def test_sidebar_english_default(self, super_client):
        _set_lang(super_client, "en")
        html = super_client.get(reverse("dashboard:home")).content.decode()
        assert "Sign Out" in html
        assert "Overview" in html

    def test_users_page_translated_uz(self, super_client):
        _set_lang(super_client, "uz")
        html = super_client.get(reverse("dashboard:users_list")).content.decode()
        assert "Yangi foydalanuvchi" in html   # New User

    def test_ichki_turlar_form_translated_uz(self, super_client):
        _set_lang(super_client, "uz")
        html = super_client.get(reverse("dashboard:ichki_turlar_create")).content.decode()
        assert "Bekat qo'shish" in html        # Add stop

    def test_language_switcher_present(self, super_client):
        html = super_client.get(reverse("dashboard:home")).content.decode()
        assert reverse("set_language") in html
