"""Tests for dashboard-managed hero slides (rotating page backgrounds)."""

import io

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.core.models import HeroSlide
from tests import factories as f

pytestmark = pytest.mark.django_db


def _image(name="slide.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (24, 14), (80, 140, 200)).save(buf, "JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


@pytest.fixture
def super_client(client):
    user = f.make_user(username="root", password="x", is_staff=True, is_superuser=True)
    client.force_login(user)
    return client


@pytest.fixture(autouse=True)
def _media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


class TestHeroSlideCrud:
    def test_create(self, super_client):
        resp = super_client.post(
            reverse("dashboard:hero_create"),
            {"page": "ichki_turlar", "alt": "Test", "order": 1, "is_active": "on", "image": _image()},
        )
        assert resp.status_code == 302
        assert HeroSlide.objects.filter(page="ichki_turlar").count() == 1

    def test_list(self, super_client):
        s = HeroSlide(page="ichki_turlar", order=1)
        s.image.save("a.jpg", _image(), save=True)
        resp = super_client.get(reverse("dashboard:hero_list"))
        assert resp.status_code == 200
        assert s in resp.context["slides"]

    def test_edit(self, super_client):
        s = HeroSlide(page="ichki_turlar", order=1, is_active=True)
        s.image.save("a.jpg", _image(), save=True)
        resp = super_client.post(
            reverse("dashboard:hero_edit", args=[s.pk]),
            {"page": "home", "image": _image("b.jpg")},
        )
        assert resp.status_code == 302
        s.refresh_from_db()
        assert s.page == "home"

    def test_delete(self, super_client):
        s = HeroSlide(page="ichki_turlar", order=1)
        s.image.save("a.jpg", _image(), save=True)
        resp = super_client.post(reverse("dashboard:hero_delete", args=[s.pk]))
        assert resp.status_code == 302
        assert not HeroSlide.objects.filter(pk=s.pk).exists()


class TestHeroSlidePublic:
    def test_page_uses_db_slides(self, client):
        s = HeroSlide(page="ichki_turlar", order=1, is_active=True)
        s.image.save("from-db.jpg", _image(), save=True)
        html = client.get(reverse("ichki-turlar-list")).content.decode()
        assert s.image.url in html
        assert "hero-ichki-1.jpg" not in html  # static fallback not used

    def test_page_falls_back_to_static(self, client):
        html = client.get(reverse("ichki-turlar-list")).content.decode()
        assert "hero-ichki-1.jpg" in html  # no DB slides → bundled images

    def test_inactive_slides_excluded(self, client):
        s = HeroSlide(page="ichki_turlar", order=1, is_active=False)
        s.image.save("hidden.jpg", _image(), save=True)
        html = client.get(reverse("ichki-turlar-list")).content.decode()
        # No active DB slides → fallback to static
        assert "hero-ichki-1.jpg" in html


class TestHeroSlidePermissions:
    def test_plain_user_forbidden(self, client):
        user = f.make_user(username="plain", password="x")
        client.force_login(user)
        assert client.get(reverse("dashboard:hero_list")).status_code != 200

    def test_manager_allowed(self, client):
        Group.objects.get_or_create(name="Manager")
        mgr = f.make_user(username="mgr", password="x", is_staff=True)
        mgr.groups.add(Group.objects.get(name="Manager"))
        client.force_login(mgr)
        assert client.get(reverse("dashboard:hero_list")).status_code == 200
